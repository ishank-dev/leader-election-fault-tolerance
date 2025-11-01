from simulator import Node, Message, NodeState
from typing import List

class RingNode(Node):
    def __init__(self, node_id: int, total_nodes: int):
        super().__init__(node_id, total_nodes)
        self.election_ids = []
        self.participant = False
        
    def start_election(self, current_time: float) -> List[Message]:
        if self.crashed:
            return []
        self.state = NodeState.CANDIDATE
        self.participant = True
        self.election_ids = [self.node_id]
        
        next_node = (self.node_id + 1) % self.total_nodes
        return [Message(
            from_node=self.node_id,
            to_node=next_node,
            type="ELECTION",
            data={"ids": [self.node_id]},
            timestamp=current_time
        )]
        
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        responses = []
        
        if msg.type == "ELECTION":
            election_list = msg.data["ids"]
            
            if self.node_id in election_list:
                if not self.participant:
                    return responses
                    
                max_id = max(election_list)
                self.leader_id = max_id
                if self.node_id == max_id:
                    self.state = NodeState.LEADER
                else:
                    self.state = NodeState.FOLLOWER
                    
                next_node = (self.node_id + 1) % self.total_nodes
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=next_node,
                    type="ELECTED",
                    data={"leader_id": max_id},
                    timestamp=current_time
                ))
            else:
                self.participant = True
                election_list.append(self.node_id)
                next_node = (self.node_id + 1) % self.total_nodes
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=next_node,
                    type="ELECTION",
                    data={"ids": election_list},
                    timestamp=current_time
                ))
                
        elif msg.type == "ELECTED":
            leader = msg.data["leader_id"]
            if self.leader_id != leader:
                self.leader_id = leader
                if self.node_id == leader:
                    self.state = NodeState.LEADER
                else:
                    self.state = NodeState.FOLLOWER
                    
                next_node = (self.node_id + 1) % self.total_nodes
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=next_node,
                    type="ELECTED",
                    data={"leader_id": leader},
                    timestamp=current_time
                ))
            self.participant = False
            
        return responses

