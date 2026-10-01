"""
VIREO AUDIO - SUPPORT OPERATIONS AI COPILOT
-------------------------------------------
User-facing CLI application wrapping vireo_analysis.py.
Executes data reconciliation, financial leakage auditing,
and AI-driven executive synthesis.
"""

import os
import vireo_analysis


def run_copilot():
    print("=" * 68)
    print("  VIREO AUDIO - SUPPORT OPERATIONS AI COPILOT")
    print("=" * 68)

    # 1. Determine Data Location & Load
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ref_docs = os.path.join(base_dir, "reference docs")
    data_dir = ref_docs if os.path.exists(ref_docs) else base_dir

    print(f"\n[Copilot] Loading data from: {data_dir}")
    data = vireo_analysis.load_data(data_dir)

    # 2. Execute Data Engine Logic
    clean_tickets = vireo_analysis.clean_and_deduplicate(data['tickets'])
    sla_res = vireo_analysis.calculate_sla_breaches(clean_tickets)
    viol_res = vireo_analysis.detect_policy_violations(clean_tickets, data['products'])
    trans_res = vireo_analysis.calculate_transfer_costs(clean_tickets)
    fin_res = vireo_analysis.financial_summary(sla_res, viol_res, trans_res)

    # 3. Generate Executive AI Synthesis
    print("\n" + "=" * 68)
    print("  AI EXECUTIVE ACTION PLAN FOR PRIYA RAMAN")
    print("=" * 68)
    print(f"  • BUSINESS GOAL: Eliminate Rs {fin_res['quarterly_inr']:,.0f}/qtr in operational leakage.")
    print(f"  • TARGET RECLAIM (Annual): Rs {fin_res['total_18m_inr'] / 1.5:,.0f} / year")
    print("\n  TOP 3 RECOMMENDED SYSTEM CONTROLS:")
    print("    1. Hard CRM Policy Block:")
    print("       Block dual Refund + Replacement triggers on single order IDs in Helpdesk.")
    print(f"       Impact: Prevents direct inventory & cash loss (Rs {viol_res['total_loss_inr']:,.0f} loss).")
    print("\n    2. Smart Tier-2 Technical Auto-Routing:")
    print("       Direct 'Connectivity' & 'Audio Quality' queries straight to Tier 2 Support.")
    print(f"       Impact: Eliminates {trans_res['total_transfers']:,} transfer hops (Rs {trans_res['total_cost_inr']:,.0f} saved).")
    print("\n    3. Peak Email Queue Rebalancing:")
    print("       Reallocate off-peak Chat agents to clear morning Email backlogs.")
    print(f"       Impact: Eliminates 410 Email SLA breaches (Rs {sla_res['total_credit_cost_inr']:,.0f} saved).")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    run_copilot()
