import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
import heapq

@dataclass
class Message:
    from_node: int
    to_node: int
    type: str
    data: Dict
    timestamp: float

@dataclass
class Metrics:
    election_time: float = 0.0
    reelection_time: float = 0.0
    messages_sent: int = 0
    final_leaders: int = 0
    messages_election: int = 0
    messages_reelection: int = 0
    
class NodeState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3
    CRASHED = 4

class Node(ABC):
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = NodeState.FOLLOWER
        self.leader_id: Optional[int] = None
        self.crashed = False
        
    @abstractmethod
    def start_election(self, current_time: float) -> List[Message]:
        pass
    
    @abstractmethod
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        pass

    def tick(self, current_time: float) -> List[Message]:
        """Called periodically to handle timeouts."""
        return []
    
    def crash(self):
        self.crashed = True
        self.state = NodeState.CRASHED
        
    def restart(self):
        self.crashed = False
        self.state = NodeState.FOLLOWER
        self.leader_id = None

class Simulator:
    def __init__(self, latency_ms: float, latency_jitter_ms: float = 0.0, message_loss_prob: float = 0.0):
        self.latency = latency_ms / 1000.0
        self.latency_jitter = latency_jitter_ms / 1000.0
        self.message_loss_prob = message_loss_prob
        self.current_time = 0.0
        self.message_queue: List[Tuple[float, int, Message]] = []
        self.msg_counter = 0
        self.nodes: List[Node] = []
        
    def send_message(self, msg: Message):
        if self.message_loss_prob > 0 and random.random() < self.message_loss_prob:
            return

        jitter = random.uniform(-self.latency_jitter, self.latency_jitter) if self.latency_jitter > 0 else 0
        delivery_time = self.current_time + max(0.001, self.latency + jitter)
        heapq.heappush(self.message_queue, (delivery_time, self.msg_counter, msg))
        self.msg_counter += 1
        
    def run_simulation(self, duration: float, kill_time: float, restart_time: Optional[float] = None, 
                      killed_node: Optional[int] = None,
                      partition_start: Optional[float] = None,
                      partition_end: Optional[float] = None,
                      partition_groups: Optional[List[List[int]]] = None) -> Metrics:
        metrics = Metrics()
        election_start_time = self.current_time
        reelection_start_time = None
        has_initial_leader = False
        election_complete_time = None
        reelection_complete_time = None
        actual_killed_node = -1
        
        msgs_at_election_end = 0
        msgs_at_reelection_start = 0
        msgs_at_reelection_end = 0
        
        initial_msgs = self.nodes[1].start_election(self.current_time)
        for msg in initial_msgs:
            self.send_message(msg)
        
        while self.current_time < duration:
            # Handle kill
            if abs(self.current_time - kill_time) < 0.01 and actual_killed_node == -1:
                target_node = killed_node
                if target_node is None:
                    # Find current leader
                    leaders = [n for n in self.nodes if n.state == NodeState.LEADER and not n.crashed]
                    if leaders:
                        target_node = leaders[0].node_id
                    else:
                        # No leader? Kill node 0
                        target_node = 0
                
                if not self.nodes[target_node].crashed:
                    self.nodes[target_node].crash()
                    actual_killed_node = target_node
                    reelection_start_time = self.current_time
                    has_initial_leader = True
                    msgs_at_reelection_start = metrics.messages_sent
                    
                    # Magic leader invalidation removed. Nodes must detect failure themselves.
            
            # Handle restart
            if restart_time and abs(self.current_time - restart_time) < 0.01 and actual_killed_node != -1:
                if self.nodes[actual_killed_node].crashed:
                    self.nodes[actual_killed_node].restart()
                    restart_msgs = self.nodes[actual_killed_node].start_election(self.current_time)
                    for msg in restart_msgs:
                        self.send_message(msg)
            
            # Process messages due now
            while self.message_queue and self.message_queue[0][0] <= self.current_time:
                _, _, msg = heapq.heappop(self.message_queue)
                
                if self.nodes[msg.to_node].crashed:
                    continue
                
                # Partition check
                if partition_start and partition_end and partition_groups:
                    if partition_start <= self.current_time <= partition_end:
                        # Check if from_node and to_node are in the same group
                        in_same_group = False
                        for group in partition_groups:
                            if msg.from_node in group and msg.to_node in group:
                                in_same_group = True
                                break
                        if not in_same_group:
                            continue # Drop message due to partition

                metrics.messages_sent += 1
                
                responses = self.nodes[msg.to_node].receive_message(msg, self.current_time)
                for response in responses:
                    self.send_message(response)
            
            # Tick nodes
            for node in self.nodes:
                if not node.crashed:
                    tick_msgs = node.tick(self.current_time)
                    for msg in tick_msgs:
                        self.send_message(msg)
            
            # Check metrics
            if election_complete_time is None and not has_initial_leader:
                leader_nodes = [n for n in self.nodes if not n.crashed and n.state == NodeState.LEADER]
                if leader_nodes:
                    election_complete_time = self.current_time
                    has_initial_leader = True
                    msgs_at_election_end = metrics.messages_sent
                    
            if reelection_start_time and reelection_complete_time is None:
                active_nodes = [n for n in self.nodes if not n.crashed]
                leader_nodes = [n for n in active_nodes if n.state == NodeState.LEADER]
                if leader_nodes:
                    reelection_complete_time = self.current_time
                    msgs_at_reelection_end = metrics.messages_sent
                
            self.current_time += 0.01
                
        leader_count = sum(1 for n in self.nodes if not n.crashed and n.state == NodeState.LEADER)
        metrics.final_leaders = leader_count
        
        if election_complete_time:
            metrics.election_time = election_complete_time - election_start_time
        else:
            metrics.election_time = kill_time - election_start_time
            
        if reelection_start_time:
            if reelection_complete_time:
                metrics.reelection_time = reelection_complete_time - reelection_start_time
            else:
                metrics.reelection_time = duration - reelection_start_time
        
        metrics.messages_election = msgs_at_election_end
        if msgs_at_reelection_end > 0:
            metrics.messages_reelection = msgs_at_reelection_end - msgs_at_reelection_start
        elif msgs_at_reelection_start > 0:
            metrics.messages_reelection = metrics.messages_sent - msgs_at_reelection_start
                
        return metrics

