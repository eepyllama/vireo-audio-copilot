# 3-Minute Screen Recording Script & Prompt History

## Walkthrough Timeline & Dialogue Guide

* **0:00 - 0:40 | Tool Execution & Business Goal**
  * *Visual:* Terminal showing command `python vireo_copilot.py` and outputting the summary.
  * *Script:* "Hello Priya. Today I am demonstrating our AI Support Operations Copilot. Our business goal is to **cut quarterly financial support leakage from Rs 1,20,276 to Rs 0**, saving Rs 4,81,100 annually across 11,875 clean support tickets."

* **0:40 - 1:20 | Prompts Used & Iterative Refinements**
  * *Visual:* Display code editor showing prompt evolution and `vireo_analysis.py`.
  * *Script:* "We iterated through 3 core prompt versions:
    * **Prompt V1:** Focused on raw ticket volume, but missed 653 duplicate entries from the legacy Freshdesk cutover.
    * **Prompt V2:** Attempted unadjusted agent rankings, which penalized Tier 2 agents handling complex 136-hour technical cases. We refined this to **Cohort Z-score normalization**.
    * **Prompt V3:** Programmatically detected policy overrides where refunds and replacements occurred simultaneously on single orders."

* **1:20 - 2:00 | What We Threw Away**
  * *Visual:* Highlight discarded PDF processing scripts or scratchpad code.
  * *Script:* "We threw away two early approaches:
    1. **OCR on Scanned PDFs**: We initially built an OCR module for scanned files in the directory, but discarded it after confirming all required data was present in structured CSVs.
    2. **Raw Handle Time Metrics**: We discarded unweighted handle times, as logistics tickets naturally take 42 hours due to shipping carriers versus 5 minutes for chat."

* **2:00 - 3:00 | Proof of Correctness (Unit Test Execution)**
  * *Visual:* Run `python validate_pipeline.py` in the terminal showing `OK (5 tests)`.
  * *Script:* "To prove our math and logic are 100% correct, we built `validate_pipeline.py`. It runs 5 automated tests verifying duplicate removal, the +5.5 hour UTC to IST conversion, all 4 policy violations, and the exact Rs 1,20,276 quarterly leakage figure. Everything runs cleanly from a single command."
