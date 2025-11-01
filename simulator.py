import time
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
    
    def crash(self):
        self.crashed = True
        self.state = NodeState.CRASHED
        
    def restart(self):
        self.crashed = False
        self.state = NodeState.FOLLOWER
        self.leader_id = None

class Simulator:
    def __init__(self, latency_ms: float):
        self.latency = latency_ms / 1000.0
        self.current_time = 0.0
        self.message_queue: List[Tuple[float, int, Message]] = []
        self.msg_counter = 0
        self.nodes: List[Node] = []
        
    def send_message(self, msg: Message):
        delivery_time = self.current_time + self.latency
        heapq.heappush(self.message_queue, (delivery_time, self.msg_counter, msg))
        self.msg_counter += 1
        
    def run_simulation(self, duration: float, kill_time: float, restart_time: Optional[float] = None, 
                      killed_node: int = 0) -> Metrics:
        metrics = Metrics()
        election_start_time = self.current_time
        reelection_start_time = None
        has_initial_leader = False
        election_complete_time = None
        reelection_complete_time = None
        
        initial_msgs = self.nodes[1].start_election(self.current_time)
        for msg in initial_msgs:
            self.send_message(msg)
        
        while self.current_time < duration:
            if abs(self.current_time - kill_time) < 0.01 and not self.nodes[killed_node].crashed:
                self.nodes[killed_node].crash()
                reelection_start_time = self.current_time
                has_initial_leader = True
                
                for node in self.nodes:
                    if not node.crashed and node.node_id != killed_node:
                        if node.leader_id == killed_node:
                            node.leader_id = None
                            if hasattr(node, 'election_timeout'):
                                node.election_timeout = self.current_time + 0.2
                
            if restart_time and abs(self.current_time - restart_time) < 0.01:
                if self.nodes[killed_node].crashed:
                    self.nodes[killed_node].restart()
                    restart_msgs = self.nodes[killed_node].start_election(self.current_time)
                    for msg in restart_msgs:
                        self.send_message(msg)
                    
            if not self.message_queue:
                self.current_time += 0.01
                continue
                
            if self.message_queue[0][0] > self.current_time:
                self.current_time = min(self.message_queue[0][0], self.current_time + 0.01)
                continue
                
            _, _, msg = heapq.heappop(self.message_queue)
            
            if self.nodes[msg.to_node].crashed:
                continue
                
            metrics.messages_sent += 1
            
            responses = self.nodes[msg.to_node].receive_message(msg, self.current_time)
            for response in responses:
                self.send_message(response)
            
            if election_complete_time is None and not has_initial_leader:
                leader_nodes = [n for n in self.nodes if not n.crashed and n.state == NodeState.LEADER]
                if leader_nodes:
                    election_complete_time = self.current_time
                    has_initial_leader = True
                    
            if reelection_start_time and reelection_complete_time is None:
                active_nodes = [n for n in self.nodes if not n.crashed]
                leader_nodes = [n for n in active_nodes if n.state == NodeState.LEADER]
                if leader_nodes:
                    reelection_complete_time = self.current_time
                
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
                
        return metrics

