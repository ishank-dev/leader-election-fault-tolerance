from simulator import Node, Message, NodeState
from typing import List
import random

class RaftNode(Node):
    def __init__(self, node_id: int, total_nodes: int):
        super().__init__(node_id, total_nodes)
        self.current_term = 0
        self.voted_for = None
        self.votes_received = 0
        self.election_timeout = None
        self.heartbeat_timeout = None
        
    def start_election(self, current_time: float) -> List[Message]:
        if self.crashed:
            return []
        self.current_term += 1
        self.state = NodeState.CANDIDATE
        self.voted_for = self.node_id
        self.votes_received = 1
        self.election_timeout = current_time + random.uniform(0.15, 0.3)
        
        messages = []
        for i in range(self.total_nodes):
            if i != self.node_id:
                messages.append(Message(
                    from_node=self.node_id,
                    to_node=i,
                    type="REQUEST_VOTE",
                    data={"term": self.current_term, "candidate_id": self.node_id},
                    timestamp=current_time
                ))
        return messages
        
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        responses = []
        
        if msg.type == "REQUEST_VOTE":
            term = msg.data["term"]
            candidate_id = msg.data["candidate_id"]
            
            if term > self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.voted_for = None
                self.leader_id = None
                
            vote_granted = False
            if term >= self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
                vote_granted = True
                self.voted_for = candidate_id
                self.current_term = term
                
            responses.append(Message(
                from_node=self.node_id,
                to_node=candidate_id,
                type="VOTE_RESPONSE",
                data={"term": self.current_term, "vote_granted": vote_granted},
                timestamp=current_time
            ))
            
        elif msg.type == "VOTE_RESPONSE":
            if self.state == NodeState.CANDIDATE and msg.data["term"] == self.current_term:
                if msg.data["vote_granted"]:
                    self.votes_received += 1
                    if self.votes_received > self.total_nodes // 2:
                        self.state = NodeState.LEADER
                        self.leader_id = self.node_id
                        self.heartbeat_timeout = current_time + 0.1
                        for i in range(self.total_nodes):
                            if i != self.node_id:
                                responses.append(Message(
                                    from_node=self.node_id,
                                    to_node=i,
                                    type="HEARTBEAT",
                                    data={"term": self.current_term, "leader_id": self.node_id},
                                    timestamp=current_time
                                ))
                                
        elif msg.type == "HEARTBEAT":
            term = msg.data["term"]
            if term >= self.current_term:
                self.current_term = term
                self.state = NodeState.FOLLOWER
                self.leader_id = msg.data["leader_id"]
                self.voted_for = None
                self.election_timeout = current_time + random.uniform(0.15, 0.3)
                        
        return responses

    def tick(self, current_time: float) -> List[Message]:
        responses = []
        if self.state == NodeState.CANDIDATE and self.election_timeout:
            if current_time >= self.election_timeout:
                msgs = self.start_election(current_time)
                responses.extend(msgs)
                        
        if self.state == NodeState.LEADER and self.heartbeat_timeout:
            if current_time >= self.heartbeat_timeout:
                self.heartbeat_timeout = current_time + 0.1
                for i in range(self.total_nodes):
                    if i != self.node_id:
                        responses.append(Message(
                            from_node=self.node_id,
                            to_node=i,
                            type="HEARTBEAT",
                            data={"term": self.current_term, "leader_id": self.node_id},
                            timestamp=current_time
                        ))
        return responses

