from simulator import Node, Message, NodeState
from typing import List

class RingNode(Node):
    def __init__(self, node_id: int, total_nodes: int):
        super().__init__(node_id, total_nodes)
        self.election_ids = []
        self.participant = False
        
        # Ring maintenance
        self.next_neighbor = (node_id + 1) % total_nodes
        self.last_ping_sent = 0.0
        self.ping_timeout = None
        
        # Leader detection
        self.leader_timeout = None
        self.last_token_sent = 0.0
        
    def start_election(self, current_time: float) -> List[Message]:
        if self.crashed:
            return []
        self.state = NodeState.CANDIDATE
        self.participant = True
        self.election_ids = [self.node_id]
        
        return [Message(
            from_node=self.node_id,
            to_node=self.next_neighbor,
            type="ELECTION",
            data={"ids": [self.node_id]},
            timestamp=current_time
        )]
        
    def receive_message(self, msg: Message, current_time: float) -> List[Message]:
        responses = []
        
        if msg.type == "PING":
            responses.append(Message(
                from_node=self.node_id,
                to_node=msg.from_node,
                type="ACK",
                data=msg.data,
                timestamp=current_time
            ))
            
        elif msg.type == "ACK":
            if msg.data.get("probe"):
                # Original neighbor is back!
                original_neighbor = (self.node_id + 1) % self.total_nodes
                if msg.from_node == original_neighbor:
                    self.next_neighbor = original_neighbor
                    self.ping_timeout = None
            elif msg.from_node == self.next_neighbor:
                self.ping_timeout = None
                
        elif msg.type == "TOKEN":
            self.leader_timeout = current_time + 0.5
            if self.state == NodeState.LEADER:
                # Token returned to leader
                pass
            else:
                # Forward token
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
                    type="TOKEN",
                    data=msg.data,
                    timestamp=current_time
                ))
                if msg.data.get("leader_id") == self.leader_id:
                     pass
                else:
                     # New leader detected via token?
                     self.leader_id = msg.data.get("leader_id")
                     self.state = NodeState.FOLLOWER

        elif msg.type == "ELECTION":
            election_list = msg.data["ids"]
            
            if self.node_id in election_list:
                if not self.participant:
                    return responses
                    
                max_id = max(election_list)
                self.leader_id = max_id
                if self.node_id == max_id:
                    self.state = NodeState.LEADER
                    self.last_token_sent = current_time # Start sending tokens
                else:
                    self.state = NodeState.FOLLOWER
                    self.leader_timeout = current_time + 0.5
                    
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
                    type="ELECTED",
                    data={"leader_id": max_id},
                    timestamp=current_time
                ))
            else:
                self.participant = True
                election_list.append(self.node_id)
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
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
                    self.leader_timeout = current_time + 0.5
                    
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
                    type="ELECTED",
                    data={"leader_id": leader},
                    timestamp=current_time
                ))
            self.participant = False
            
        return responses

    def tick(self, current_time: float) -> List[Message]:
        responses = []
        
        # 1. Neighbor Maintenance
        # Check if we should try to revert to original neighbor
        original_neighbor = (self.node_id + 1) % self.total_nodes
        if self.next_neighbor != original_neighbor:
             # Probe original neighbor
             responses.append(Message(
                from_node=self.node_id,
                to_node=original_neighbor,
                type="PING",
                data={"probe": True},
                timestamp=current_time
            ))

        if current_time - self.last_ping_sent >= 0.5:
            self.last_ping_sent = current_time
            responses.append(Message(
                from_node=self.node_id,
                to_node=self.next_neighbor,
                type="PING",
                data={},
                timestamp=current_time
            ))
            # Only set timeout if not already waiting (or reset it?)
            # Let's reset it.
            self.ping_timeout = current_time + 0.3

        if self.ping_timeout and current_time >= self.ping_timeout:
            # Neighbor failed. Move to next.
            self.next_neighbor = (self.next_neighbor + 1) % self.total_nodes
            if self.next_neighbor == self.node_id:
                # We are alone
                pass
            else:
                # Retry PING immediately to new neighbor
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
                    type="PING",
                    data={},
                    timestamp=current_time
                ))
                self.ping_timeout = current_time + 0.3

        # 2. Leader Logic
        if self.state == NodeState.LEADER:
            if current_time - self.last_token_sent >= 0.2:
                self.last_token_sent = current_time
                responses.append(Message(
                    from_node=self.node_id,
                    to_node=self.next_neighbor,
                    type="TOKEN",
                    data={"leader_id": self.node_id},
                    timestamp=current_time
                ))

        # 3. Follower Logic
        if self.state == NodeState.FOLLOWER and self.leader_id is not None:
            if self.leader_timeout and current_time >= self.leader_timeout:
                self.leader_id = None
                msgs = self.start_election(current_time)
                responses.extend(msgs)
                
        return responses

