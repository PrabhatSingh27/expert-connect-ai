# System Architecture

Customer
    |
    v
Describe Problem
(Text + Image + Audio + Video)
    |
    v
AI Triage Engine
    |
    |-- Problem Detection
    |-- Category Mapping
    |-- Urgency Detection
    |
    v
Assignment Engine
    |
    |-- Category Match
    |-- Round Robin
    |-- Load Balancing
    |-- Availability Check
    |-- Priority Scheduling
    |
    v
Expert Assigned
    |
    v
Issue Resolution
    |
    |-- Chat
    |-- Status Updates
    |
    v
Resolved
    |
    v
Feedback