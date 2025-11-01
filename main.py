#!/usr/bin/env python3
import yaml
from simulator import Simulator, Metrics
from bully import BullyNode
from ring import RingNode
from raft import RaftNode

def run_algorithm(algorithm_name: str, node_class, config: dict) -> Metrics:
    sim = Simulator(config["latency_ms"])
    
    for i in range(config["num_nodes"]):
        node = node_class(i, config["num_nodes"])
        sim.nodes.append(node)
    
    restart_time = config["optional_restart_time"] if config["enable_restart"] else None
    
    metrics = sim.run_simulation(
        duration=5.0,
        kill_time=config["leader_kill_time"],
        restart_time=restart_time,
        killed_node=0
    )
    
    return metrics

def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    print("=" * 60)
    print("Leader Election Algorithm Comparison")
    print("=" * 60)
    print(f"Setup: {config['num_nodes']} nodes, {config['latency_ms']}ms latency")
    print(f"Leader crash at t={config['leader_kill_time']}s")
    if config['enable_restart']:
        print(f"Leader restart at t={config['optional_restart_time']}s")
    print("=" * 60)
    print()
    
    algorithms = [
        ("Bully", BullyNode),
        ("Ring", RingNode),
        ("Raft", RaftNode)
    ]
    
    results = []
    for name, node_class in algorithms:
        print(f"Running {name} algorithm...")
        metrics = run_algorithm(name, node_class, config)
        results.append((name, metrics))
        print(f"  ✓ Completed\n")
    
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    
    print(f"{'Algorithm':<12} {'Election(s)':<15} {'Re-election(s)':<15} {'Messages':<12} {'Success'}")
    print("-" * 70)
    
    for name, metrics in results:
        success = "✓" if metrics.final_leaders == 1 else f"✗ ({metrics.final_leaders})"
        print(f"{name:<12} {metrics.election_time:<15.3f} {metrics.reelection_time:<15.3f} "
              f"{metrics.messages_sent:<12} {success}")
    
    print()
    print("=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    fastest_election = min(results, key=lambda x: x[1].election_time)
    fastest_reelection = min(results, key=lambda x: x[1].reelection_time)
    fewest_messages = min(results, key=lambda x: x[1].messages_sent)
    
    print(f"Fastest election:     {fastest_election[0]} ({fastest_election[1].election_time:.3f}s)")
    print(f"Fastest re-election:  {fastest_reelection[0]} ({fastest_reelection[1].reelection_time:.3f}s)")
    print(f"Fewest messages:      {fewest_messages[0]} ({fewest_messages[1].messages_sent} msgs)")
    
    success_count = sum(1 for _, m in results if m.final_leaders == 1)
    print(f"Success rate:         {success_count}/{len(results)} algorithms")
    print()

if __name__ == "__main__":
    main()

