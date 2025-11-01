from simulator import Node, Message, NodeState
from typing import List

class BullyNode(Node):
    def __init__(self, node_id: int, total_nodes: int):
        super().__init__(node_id, total_nodes)
        self.awaiting_ok = False
        self.ok_timeout = None
        
    def start_election(self, current_time: float) -> List[Message]:
        if self.crashed:
            return []
        self.state = NodeState.CANDIDATE
        self.awaiting_ok = True
        self.ok_timeout = current_time + 0.2
        
        messages = []
        higher_nodes = [i for i in range(self.node_id + 1, self.total_nodes)]
        if not higher_nodes:
            self.state = NodeState.LEADER
            self.leader_id = self.node_id
            self.awaiting_ok = False
            for i in range(self.total_nodes):
                if i != self.node_id:
                    messages.append(Message(
                        from_node=self.node_id,
                        to_node=i,
                        type="COORDINATOR",
                        data={"leader_id": self.node_id},
                        timestamp=current_time
                    ))
        else:
            for node in higher_nodes:
                messages.append(Message(
                    from_node=self.node_id,
                    to_node=node,
                    type="ELECTION",
                    data={},
                    timestamp=current_time
                ))
        return messages
        
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        responses = []
        
        if msg.type == "ELECTION":
            if msg.from_node < self.node_id:
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=msg.from_node,
                    type="OK",
                    data={},
                    timestamp=current_time
                ))
                if self.state != NodeState.LEADER:
                    self.start_election(current_time)
                    higher_nodes = [i for i in range(self.node_id + 1, self.total_nodes)]
                    for node in higher_nodes:
                        responses.append(Message(
                            from_node=self.node_id,
                            to_node=node,
                            type="ELECTION",
                            data={},
                            timestamp=current_time
                        ))
                        
        elif msg.type == "OK":
            self.awaiting_ok = False
            self.state = NodeState.FOLLOWER
            
        elif msg.type == "COORDINATOR":
            self.leader_id = msg.data["leader_id"]
            self.state = NodeState.FOLLOWER
            self.awaiting_ok = False
            
        if self.state == NodeState.CANDIDATE and self.awaiting_ok:
            if self.ok_timeout and current_time >= self.ok_timeout:
                self.state = NodeState.LEADER
                self.leader_id = self.node_id
                self.awaiting_ok = False
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

