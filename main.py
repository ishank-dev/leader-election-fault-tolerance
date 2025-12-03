#!/usr/bin/env python3
import yaml
import math
import statistics
from simulator import Simulator, Metrics
from bully import BullyNode
from ring import RingNode
from raft import RaftNode
from multi_attribute import MultiAttributeNode

def get_percentile(data, percentile):
    size = len(data)
    return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]

def run_algorithm(algorithm_name: str, node_class, config: dict) -> Metrics:
    sim = Simulator(
        latency_ms=config["latency_ms"],
        latency_jitter_ms=config.get("latency_jitter_ms", 0),
        message_loss_prob=config.get("message_loss_prob", 0.0)
    )
    
    for i in range(config["num_nodes"]):
        node = node_class(i, config["num_nodes"])
        sim.nodes.append(node)
    
    restart_time = config["optional_restart_time"] if config["enable_restart"] else None
    
    partition_start = config.get("partition_start_time") if config.get("enable_partition") else None
    partition_end = config.get("partition_end_time") if config.get("enable_partition") else None
    partition_groups = config.get("partition_groups") if config.get("enable_partition") else None

    metrics = sim.run_simulation(
        duration=5.0,
        kill_time=config["leader_kill_time"],
        restart_time=restart_time,
        killed_node=None,
        partition_start=partition_start,
        partition_end=partition_end,
        partition_groups=partition_groups
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
    if config.get('enable_partition'):
        print(f"Partition at t={config['partition_start_time']}s - {config['partition_end_time']}s")
        print(f"Groups: {config['partition_groups']}")
    print("=" * 60)
    print()
    
    algorithms = [
        ("Bully", BullyNode),
        ("Ring", RingNode),
        ("Raft", RaftNode),
        ("Multi-Attr", MultiAttributeNode)
    ]
    
    NUM_TRIALS = 5
    print(f"Running {NUM_TRIALS} trials per algorithm for P50/P95 analysis...")
    print()

    results = []
    for name, node_class in algorithms:
        print(f"Running {name} algorithm...", end="", flush=True)
        trial_metrics = []
        for _ in range(NUM_TRIALS):
            metrics = run_algorithm(name, node_class, config)
            trial_metrics.append(metrics)
            print(".", end="", flush=True)
        results.append((name, trial_metrics))
        print(f" Done")
    
    print("\n" + "=" * 80)
    print("RESULTS (P50 / P95)")
    print("=" * 80)
    print()
    
    # Header
    print(f"{'Algorithm':<10} | {'Election (s)':<18} | {'Re-election (s)':<18} | {'Messages':<15} | {'Success'}")
    print("-" * 80)
    
    final_stats = []

    for name, metrics_list in results:
        # Extract data
        elec_times = [m.election_time for m in metrics_list]
        reelec_times = [m.reelection_time for m in metrics_list]
        msgs = [m.messages_sent for m in metrics_list]
        success_count = sum(1 for m in metrics_list if m.final_leaders == 1)
        
        # Calculate stats
        e_p50 = get_percentile(elec_times, 50)
        e_p95 = get_percentile(elec_times, 95)
        
        r_p50 = get_percentile(reelec_times, 50)
        r_p95 = get_percentile(reelec_times, 95)
        
        m_p50 = get_percentile(msgs, 50)
        m_p95 = get_percentile(msgs, 95)
        
        success_rate = f"{success_count}/{NUM_TRIALS}"
        
        # Store for analysis
        final_stats.append({
            "name": name,
            "e_p50": e_p50, "r_p50": r_p50, "m_p50": m_p50
        })

        # Print row
        print(f"{name:<10} | {e_p50:.3f} / {e_p95:.3f}      | {r_p50:.3f} / {r_p95:.3f}      | {m_p50:<5} / {m_p95:<5} | {success_rate}")
    
    print()
    print("=" * 80)
    print("ANALYSIS (Based on P50)")
    print("=" * 80)
    
    fastest_election = min(final_stats, key=lambda x: x["e_p50"])
    fastest_reelection = min(final_stats, key=lambda x: x["r_p50"])
    fewest_messages = min(final_stats, key=lambda x: x["m_p50"])
    
    print(f"Fastest election:     {fastest_election['name']} ({fastest_election['e_p50']:.3f}s)")
    print(f"Fastest re-election:  {fastest_reelection['name']} ({fastest_reelection['r_p50']:.3f}s)")
    print(f"Fewest messages:      {fewest_messages['name']} ({fewest_messages['m_p50']} msgs)")
    print()

if __name__ == "__main__":
    main()

