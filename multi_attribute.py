from simulator import Node, Message, NodeState
from typing import List
import random

class MultiAttributeNode(Node):
    def __init__(self, node_id: int, total_nodes: int):
        super().__init__(node_id, total_nodes)
        # Simulate dynamic attributes (Paper: Multi-attribute Self-Stabilizing Leader Election)
        self.battery = random.randint(50, 100)
        self.cpu_load = random.randint(0, 60)
        # Score calculation: Higher is better
        self.score = (0.7 * self.battery) + (0.3 * (100 - self.cpu_load))
        
        self.awaiting_ok = False
        self.ok_timeout = None
        self.heartbeat_timeout = None
        self.last_heartbeat_sent = 0.0
        
    def start_election(self, current_time: float) -> List[Message]:
        if self.crashed:
            return []
        self.state = NodeState.CANDIDATE
        self.awaiting_ok = True
        self.ok_timeout = current_time + 0.3  # Slightly longer timeout for broadcast
        
        messages = []
        # In Multi-attribute, we don't know who has a higher score, so we broadcast to ALL
        # (Optimization: In a real system, we might gossip, but here we broadcast)
        for i in range(self.total_nodes):
            if i != self.node_id:
                messages.append(Message(
                    from_node=self.node_id,
                    to_node=i,
                    type="ELECTION",
                    data={"score": self.score},
                    timestamp=current_time
                ))
        return messages
        
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        responses = []
        
        if msg.type == "ELECTION":
            sender_score = msg.data["score"]
            
            # If I have a higher score (or tie-break with higher ID), I bully them
            is_higher = self.score > sender_score or (self.score == sender_score and self.node_id > msg.from_node)
            
            if is_higher:
                # Send OK to tell them to stop (I am taking over)
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    type="OK",
                    data={},
                    timestamp=current_time
                ))
                # Start my own election if I haven't already
                if self.state != NodeState.LEADER and self.state != NodeState.CANDIDATE:
                    msgs = self.start_election(current_time)
                    responses.extend(msgs)
            else:
                # They are better. I do nothing and let them win.
                pass
                        
        elif msg.type == "OK":
            # Someone better responded. I step down and wait for their Coordinator msg.
            self.awaiting_ok = False
            self.state = NodeState.FOLLOWER
            self.ok_timeout = None
            
        elif msg.type == "COORDINATOR":
            self.leader_id = msg.data["leader_id"]
            self.state = NodeState.FOLLOWER
            self.awaiting_ok = False
            self.heartbeat_timeout = current_time + 0.4

        elif msg.type == "HEARTBEAT":
            self.leader_id = msg.data["leader_id"]
            self.state = NodeState.FOLLOWER
            self.heartbeat_timeout = current_time + 0.4
            
        return responses

    def tick(self, current_time: float) -> List[Message]:
        responses = []
        
        # Leader Logic: Send Heartbeats
        if self.state == NodeState.LEADER:
            if current_time - self.last_heartbeat_sent >= 0.1:
                self.last_heartbeat_sent = current_time
                for i in range(self.total_nodes):
                    if i != self.node_id:
                        responses.append(Message(
                            from_node=self.node_id,
                            to_node=i,
                            type="HEARTBEAT",
                            data={"leader_id": self.node_id},
                            timestamp=current_time
                        ))
                        
        # Follower Logic: Check Heartbeat Timeout
        if self.state == NodeState.FOLLOWER and self.leader_id is not None:
            if self.heartbeat_timeout and current_time >= self.heartbeat_timeout:
                self.leader_id = None
                msgs = self.start_election(current_time)
                responses.extend(msgs)

        # Candidate Logic: Check Election Timeout
        if self.state == NodeState.CANDIDATE and self.awaiting_ok:
            if self.ok_timeout and current_time >= self.ok_timeout:
                # No one with a higher score responded. I win!
                self.state = NodeState.LEADER
                self.leader_id = self.node_id
                self.awaiting_ok = False
                self.last_heartbeat_sent = current_time
                for i in range(self.total_nodes):
                    if i != self.node_id:
                        responses.append(Message(
                            from_node=self.node_id,
                            to_node=i,
                            type="COORDINATOR",
                            data={"leader_id": self.node_id},
                            timestamp=current_time
                        ))
        return responses
