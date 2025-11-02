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

##  Output

<p align="center">
  <img src="https://github.com/user-attachments/assets/fd9dd54c-8387-4941-bfd8-a9cbfe791e64" alt="CLI Output" width="600" />
</p>

---

##  Working of Each Algorithm

###  Bully Algorithm
Higher ID nodes dominate — **O(n²)** message complexity.

<p align="center">
  <img src="https://github.com/user-attachments/assets/265b2d63-8f01-42ab-b59c-760f8d9baa62" alt="Bully Election Sequence" width="600" />
</p>

---

###  Ring Algorithm
Token passes in a circular manner — **O(n)** message complexity.

<p align="center">
  <img src="https://github.com/user-attachments/assets/7e4ed839-f5f9-4173-bc8a-0ac1b73fdc9a" alt="Ring Election Phases" width="600" />
</p>

---

###  Raft Algorithm
Randomized timeouts with majority voting — **Balanced and resilient election performance.**

<p align="center">
  <img src="https://github.com/user-attachments/assets/8c969675-798f-4eac-89e2-5a0ca5610958" alt="Raft Election FSM" width="600" />
</p>

---

###  End-to-End Workflow
Event-driven simulation showing configuration, election, failure, recovery, and re-election phases.

<p align="center">
  <img src="https://github.com/user-attachments/assets/61061790-1175-4d2a-bbc5-222364f6ee11" alt="End-to-End Leader Election Workflow" width="600" />
</p>

### Authors
- **Ishank Sharma:** Designed simulator core, implemented Raft election, and metric computation. Analyzed stabiliza-
tion time, message complexity, and recovery efficiency.
- **Sri Lalitha:** Developed evaluation and monitoring framework, automated timing/message tracking, and comparative
testing.
- **Prerana:** Implemented crash-recovery logic, integrated restart features, and authored documentation/literature syn-
thesis connecting theory to results.



