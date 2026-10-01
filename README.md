# Vireo Audio - AI-Assisted Support Operations Copilot

An automated support operations copilot that cleans legacy tickets, normalizes time zones, audits policy violations, and isolates financial support leakage.

## Quick Start (Clean Machine Setup)

### Prerequisites
* Python 3.9 or higher
* Standard Python `pip` package manager

### 1. Installation
Clone or unpack the repository, then install requirements:
```bash
pip install -r requirements.txt
```

### 2. Run the AI Operations Copilot

Execute the main interactive copilot tool:

```bash
python vireo_copilot.py
```

### 3. Run Automated Validation & Test Suite

Verify data hygiene, time-offset conversions, and financial calculations:

```bash
python validate_pipeline.py
```

## System Architecture & Key Capabilities

* **Automatic Deduplication**: Cleans 653 duplicate legacy records while prioritizing primary helpdesk data.
* **UTC -> IST Timestamp Conversion**: Applies +5.5 hour adjustments to reconstructed UTC logs.
* **Leakage Audit Engine**: Calculates quarterly run-rate across SLA breach credits, internal transfer costs, and policy overrides.
* **Cohort Z-Score Model**: Evaluates agent performance fairly within Tier/Channel peer cohorts.

## File Overview

| File | Purpose |
| :--- | :--- |
| `vireo_copilot.py` | Main user-facing CLI tool — runs the full audit and prints executive action plan |
| `vireo_analysis.py` | Core analytical engine — data cleaning, SLA, violations, transfers, agent scoring |
| `validate_pipeline.py` | Unit test suite — 5 assertions verifying deduplication, math, and financials |
| `MEMO_PRIYA_RAMAN.md` | One-page executive memorandum for Priya Raman |
| `VIDEO_SCRIPT_AND_PROMPTS.md` | 3-minute screen recording walkthrough script |
