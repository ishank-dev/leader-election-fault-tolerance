# Leader Election Simulator under Crash-Recovery Fault Models
**Group 5: Ishank Sharma, Srilalitha Subbaswamy, Prerana Puttaswamy**

---

## Agenda
* Introduction & Motivation
* Background & Assumptions
* Implemented Work & Methodology
* Simulator Architecture
* Experimental Setup (Enhanced)
* Simulation Results (P50/P95)
* Analysis & Limitations
* Future Work & Summary

---

## Project Description
* Deliverables: Research Survey & Benchmarking Simulator
* Focus: Crash-Recovery & Network Partition Environments
* Algorithms Evaluated:
  - Bully (Classic)
  - Ring (Token-based)
  - Raft (Consensus-based)
  - Multi-Attribute (New)
* Implementation: Custom event-driven simulator with jitter, packet loss, and partitions.

---

## Background
* Importance: Coordination, Consistency, Synchronization
* Challenges in Crash-Recovery:
  - Node failures and restarts
  - Ambiguity of leadership
  - Network Partitions (Split-brain)
* Key Considerations:
  - Synchrony assumptions
  - Failure detection (Heartbeats vs Timeouts)
  - Safety & Liveness guarantees
  - Message Complexity
  - Leader Quality (ID vs Resources)

---

## Literature Survey: Recent Advances (1/2)
* Multi-attribute Self-Stabilizing Leader Election (2025)
  - Focus: Self-stabilization in arbitrary fault models.
  - Key Idea: Uses multiple attributes (CPU, uptime) vs just ID.
  - Relevance: Basis for our Multi-Attribute implementation.

* Hierarchical Adaptive Leader Election (2024)
  - Focus: Scalability in crash-recovery.
  - Key Idea: Hierarchical groups reduce message load.
  - Relevance: Highlights limits of flat algorithms (Bully).

---

## Literature Survey: Recent Advances (2/2)
* Enhancing Election Algorithms (2025)
  - Focus: Optimizing timeout mechanisms.
  - Key Idea: Dynamic timeouts based on network load.
  - Relevance: Validates use of Jitter/Adaptive timeouts.

* Near-Optimal Knowledge-Free Resilient Election (2022)
  - Focus: Minimal global knowledge.
  - Key Idea: Nodes operate without knowing total N.
  - Relevance: Contrasts with our fixed N=10 assumption.

---

## Algorithms Included
* Bully Algorithm
  - Prioritizes highest ID.
  - Fast but message-heavy.

* Ring Algorithm
  - Logical ring structure.
  - Message-efficient but slow.

* Raft Election
  - Majority consensus.
  - Robust against partitions.

* Multi-Attribute (New)
  - Score = f(Battery, CPU).
  - Broadcast-based bullying.

---

## Implemented Work
* Implemented Algorithms: Bully, Ring, Raft, Multi-Attr
* Standardized Test Scenario:
  - Crash-Recovery
  - Network Partitions
* Metrics Measured:
  - Election & Re-election Latency (P50/P95)
  - Message Counts (Per phase)
  - Success Rate (Partition tolerance)
* Comparative Analysis: Multi-seed statistical trials.

---

## Methodology
* Simulator: Single-process, event-driven
* Network Model:
  - 10 Nodes
  - 50ms Latency + 10ms Jitter
  - 5% Probabilistic Message Loss
* Events:
  - Crash @ t=2.0s
  - Partition @ t=2.5s - 4.0s
  - Restart @ t=3.0s
* Data Collection: Multi-seed trials (5 runs) for statistical significance.

---

## Simulator Architecture
* Node Module: Algorithm logic (Bully, Ring, Raft, Multi-Attr)
* Event Scheduler: Priority queue for timed events
* Fault Injector: Crashes, Restarts, Packet Loss
* Partition Manager: Simulates network cuts/groups
* Message Bus: Models communication with jitter
* Monitoring System: Collects P50/P95 metrics

---

## Experimental Setup
* Configuration:
  - 10 Nodes
  - Latency: 50ms +/- 10ms
  - Packet Loss: 5%
* Timeline:
  - t=0.0s: Start
  - t=2.0s: Leader Crash
  - t=2.5s: Network Partition (Groups: [0-4], [5-9])
  - t=3.0s: Leader Restart
  - t=4.0s: Partition Heals

---

## Simulation Results (P50)
Bully:
* Elec: 0.05s | Re-elec: 0.81s | Msgs: ~1168 | Success: 5/5

Ring:
* Elec: 2.00s | Re-elec: 3.01s | Msgs: ~463 | Success: 1/5

Raft:
* Elec: 0.11s | Re-elec: 2.29s | Msgs: ~284 | Success: 5/5

Multi-Attribute (New):
* Elec: 0.35s | Re-elec: 0.73s | Msgs: ~573 | Success: 5/5

---

## Performance Patterns
* Speed: Multi-Attribute is fastest at Re-election.
* Efficiency: Raft is most efficient (Fewest messages).
* Resilience:
  - Raft, Bully, Multi-Attr: High (Handled partitions).
  - Ring: Low (Circuit broken by partition).
* Innovation:
  - Multi-Attr beats Bully in efficiency & speed.

---

## Analysis
* Bully:
  - Fast but chatty (O(n^2)).
* Ring:
  - Fragile in partitions.
* Raft:
  - Optimal balance & safety.
* Multi-Attribute (New):
  - Superior to Bully.
  - 50% fewer messages.
  - Faster recovery (0.73s vs 0.81s).

---

## Team Contributions
* Ishank:
  - Simulator Core & Raft Implementation.
  - Added Jitter, Packet Loss, and Partition logic.
  - Statistical Analysis (P50/P95).
* Srilalitha:
  - Evaluation Framework & Monitoring.
  - Comparative Testing & Results Visualization.
* Prerana:
  - Crash-Recovery Logic & Ring Repair.
  - Literature Review & Multi-Attribute Algo.

---

## Difficulties & Solutions
* Challenges:
  - Timing Precision: Handling jitter and random delays.
  - Partitions: Ring algorithm failed to recover token.
  - Failure Detection: Replaced "magic" detection with Heartbeats.
* Solutions:
  - Implemented robust timeout logic (Tick mechanism).
  - Added Ring Repair probes.
  - Used Multi-seed trials to smooth out variance.

---

## Future Work
* Completed Phase 2:
  - Jitter, Packet Loss, Partitions (Done).
  - Multi-seed P50/P95 Analysis (Done).
  - Multi-Attribute Implementation (Done).
* Next Steps:
  - Byzantine Fault Tolerance (BFT).
  - Scalability testing (100+ nodes).
  - Formal verification of protocol correctness.
  - Dynamic membership changes.

---

## Summary
* Implemented & Benchmarked: Bully, Ring, Raft, Multi-Attr.
* Realistic Conditions:
  - Crash-Recovery, Partitions, Jitter, Loss.
* Key Findings:
  - Raft is most robust.
  - Multi-Attribute is fastest & efficient.
* Outcome: A comprehensive simulator + New Algorithm.
