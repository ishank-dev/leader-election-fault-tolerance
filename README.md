# Leader Election Algorithm Simulator

Simulates and compares three leader election algorithms: Bully, Ring, and Raft (election-only).

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

Edit `config.yaml`:
- `num_nodes`: Number of nodes (default: 5)
- `latency_ms`: Network latency in milliseconds (default: 50)
- `leader_kill_time`: When to crash the leader (default: 2.0s)
- `optional_restart_time`: When to restart crashed node (default: 3.0s)
- `enable_restart`: Enable/disable restart (default: true)

## Metrics

- **Election time**: Time to elect initial leader
- **Re-election time**: Time to elect new leader after crash
- **Messages sent**: Total messages during simulation
- **Success rate**: Did exactly one leader emerge?

## Algorithms

- **Bully**: Higher ID nodes dominate, O(n²) messages
- **Ring**: Token passes in circle, O(n) messages
- **Raft**: Randomized timeouts, majority voting
