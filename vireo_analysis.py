"""
===============================================================================
VIREO AUDIO - SUPPORT TICKET ANALYSIS & VENDOR EVALUATION
Complete Execution Script
===============================================================================

Purpose:  Reproduces all data cleaning, deduplication, SLA breach calculation,
          policy violation detection, categorization, and agent performance
          evaluation from the raw CSV exports.

Inputs:   tickets.csv, agents.csv, orders.csv, products.csv
Policy:   support-policy.pdf (Version 3.2, Effective 1 April 2025)

Author:   Customer Operations Analytics
Date:     September 2026
===============================================================================
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Update these paths to point at your data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference docs")

# File names (with UUID prefixes as exported)
TICKETS_FILE  = "cded5ec7-cd54-40e6-ba66-7b3e581319c7-tickets.csv"
AGENTS_FILE   = "1bb95ea8-f7cb-44b6-b5d2-2fb20c9a4e47-agents.csv"
ORDERS_FILE   = "e5c326e5-4764-4ab0-87fd-75abb8f287ae-orders.csv"
PRODUCTS_FILE = "8e1b3214-16f2-4456-a618-cd1a4e8bddef-products.csv"

# Policy constants (support-policy.pdf, Version 3.2)
SLA_TARGETS_MINUTES = {
    'chat':   15,    # 15 minutes
    'voice':  120,   # 2 hours
    'social': 240,   # 4 hours
    'email':  480,   # 8 hours
}
SLA_BREACH_CREDIT_INR    = 350    # Rs 350 store credit per breach
TRANSFER_COST_INR        = 305    # Rs 305 per internal transfer
REPLACEMENT_LOGISTICS_INR = 340   # Rs 340 reverse pickup + forward shipping
COST_PER_CONTACT = {
    'chat':   210,
    'email':  260,
    'voice':  520,
    'social': 240,
}
BLENDED_COST_PER_CONTACT = 290
IST_UTC_OFFSET_HOURS = 5.5       # IST = UTC + 5:30
HELPDESK_CUTOVER_DATE = "2025-09-14"  # Current helpdesk went live

# ==============================================================================
# STEP 0: LOAD DATA
# ==============================================================================

def load_data(data_dir):
    """Load all CSV datasets and return as a dict of DataFrames."""
    tickets  = pd.read_csv(os.path.join(data_dir, TICKETS_FILE))
    agents   = pd.read_csv(os.path.join(data_dir, AGENTS_FILE))
    orders   = pd.read_csv(os.path.join(data_dir, ORDERS_FILE))
    products = pd.read_csv(os.path.join(data_dir, PRODUCTS_FILE))
    return {
        'tickets':  tickets,
        'agents':   agents,
        'orders':   orders,
        'products': products,
    }


# ==============================================================================
# STEP 1: DATA CLEANING & RECONCILIATION
# ==============================================================================

def clean_and_deduplicate(tickets):
    """
    Remove duplicate ticket entries caused by the legacy Freshdesk migration.

    LOGIC:
    - The legacy helpdesk (Freshdesk) was replaced on 14 Sep 2025.
    - A subset of pre-cutover tickets was re-imported during reconciliation,
      resulting in rows appearing under BOTH source_system='helpdesk' AND
      source_system='legacy_fd' for the same ticket_id.
    - For each duplicate pair, we keep the 'helpdesk' version because:
      (a) It uses IST timestamps natively (the standard report format).
      (b) The legacy_fd resolved_at is stored in UTC and needs correction.
    - For legacy-only tickets (no helpdesk duplicate), we correct the
      resolved_at timestamp by adding +5:30 (IST offset) per policy Sec 9.
    - Auto-closed tickets (status='closed') are retained in the dataset;
      per policy Sec 8, they count as completed attendance and are surveyed.

    Returns:
        cleaned DataFrame with duplicates removed and timestamps normalised.
    """
    raw_count = len(tickets)

    # Sort so 'helpdesk' rows come before 'legacy_fd' alphabetically
    tickets_sorted = tickets.sort_values('source_system', ascending=True)

    # Drop duplicate ticket_ids, keeping the first occurrence (helpdesk)
    tickets_dedup = tickets_sorted.drop_duplicates(subset='ticket_id', keep='first').copy()
    dupes_removed = raw_count - len(tickets_dedup)

    # Parse timestamps
    for col in ['created_at', 'first_response_at', 'resolved_at']:
        tickets_dedup[col + '_dt'] = pd.to_datetime(tickets_dedup[col], errors='coerce')

    # Fix legacy_fd resolved_at timestamps: stored in UTC, convert to IST
    # Per policy Sec 9: "Resolution timestamps for migrated tickets were
    # reconstructed from the legacy event log, which stores UTC."
    legacy_mask = tickets_dedup['source_system'] == 'legacy_fd'
    tickets_dedup.loc[legacy_mask, 'resolved_at_dt'] = (
        tickets_dedup.loc[legacy_mask, 'resolved_at_dt']
        + pd.Timedelta(hours=IST_UTC_OFFSET_HOURS)
    )

    print(f"[Step 1] Raw rows:           {raw_count:,}")
    print(f"[Step 1] Duplicates removed: {dupes_removed:,}")
    print(f"[Step 1] Clean rows:         {len(tickets_dedup):,}")
    print(f"[Step 1] Legacy UTC->IST:    {legacy_mask.sum():,} rows corrected")

    return tickets_dedup


# ==============================================================================
# STEP 2: FINANCIAL & POLICY LEAKAGE ANALYSIS
# ==============================================================================

def calculate_sla_breaches(tickets):
    """
    Calculate first-response SLA breach rate and total breach credit cost.

    Per policy Sec 3:
      - Chat: 15 min | Voice: 2 hr | Social: 4 hr | Email: 8 hr
      - Every breach triggers Rs 350 store credit on resolution.
    """
    tickets = tickets.copy()
    tickets['resp_minutes'] = (
        (tickets['first_response_at_dt'] - tickets['created_at_dt'])
        .dt.total_seconds() / 60
    )

    # Only count resolved/closed tickets with a valid first response
    valid = tickets[
        tickets['resp_minutes'].notna() &
        tickets['status'].isin(['resolved', 'closed'])
    ]

    results = {}
    total_breached = 0

    for channel, target_min in SLA_TARGETS_MINUTES.items():
        ch_data = valid[valid['channel'] == channel]
        breached = ch_data[ch_data['resp_minutes'] > target_min]
        rate = len(breached) / len(ch_data) * 100 if len(ch_data) > 0 else 0
        total_breached += len(breached)
        results[channel] = {
            'total_tickets': len(ch_data),
            'breached': len(breached),
            'breach_rate_pct': round(rate, 1),
            'target_minutes': target_min,
        }

    overall_rate = total_breached / len(valid) * 100 if len(valid) > 0 else 0
    credit_cost = total_breached * SLA_BREACH_CREDIT_INR

    print(f"\n[Step 2a] SLA Breach Analysis (on {len(valid):,} resolved tickets):")
    for ch, r in results.items():
        print(f"  {ch:8s}: {r['total_tickets']:5,} tickets | "
              f"{r['breached']:4,} breached | {r['breach_rate_pct']:5.1f}% | "
              f"target={r['target_minutes']}min")
    print(f"  {'OVERALL':8s}: {len(valid):5,} tickets | "
          f"{total_breached:4,} breached | {overall_rate:5.1f}%")
    print(f"  Total SLA breach credits (18 months): Rs {credit_cost:,.0f}")
    print(f"  Per quarter:                          Rs {credit_cost/6:,.0f}")

    return {
        'channel_details': results,
        'total_breached': total_breached,
        'overall_rate_pct': round(overall_rate, 1),
        'total_credit_cost_inr': credit_cost,
    }


def detect_policy_violations(tickets, products):
    """
    Identify orders that received BOTH a refund AND a replacement.

    Per policy Sec 5: "In no case is a customer to receive both a refund
    and a replacement for the same order."

    Financial loss per violation:
      refund_amount_inr + product unit_cost_inr + Rs 340 logistics
    """
    violations = tickets[
        (tickets['refund_amount_inr'] > 0) &
        (tickets['replacement_issued'] == 'Y')
    ].copy()

    # Merge product unit costs
    violations = violations.merge(
        products[['sku', 'unit_cost_inr', 'product_name']],
        left_on='product_sku', right_on='sku', how='left'
    )

    violations['total_loss_inr'] = (
        violations['refund_amount_inr'] +
        violations['unit_cost_inr'] +
        REPLACEMENT_LOGISTICS_INR
    )

    total_loss = violations['total_loss_inr'].sum()

    print(f"\n[Step 2b] Policy Violations (Refund + Replacement on same order):")
    print(f"  Violations found: {len(violations)}")
    for _, v in violations.iterrows():
        print(f"    {v['ticket_id']} | {v['order_id']} | {v['product_name']} | "
              f"Refund Rs {v['refund_amount_inr']:,.0f} + "
              f"Unit Rs {v['unit_cost_inr']:,.0f} + "
              f"Logistics Rs {REPLACEMENT_LOGISTICS_INR} = "
              f"Rs {v['total_loss_inr']:,.0f}")
    print(f"  Total policy violation loss: Rs {total_loss:,.0f}")

    return {
        'violation_count': len(violations),
        'total_loss_inr': total_loss,
        'detail': violations,
    }


def calculate_transfer_costs(tickets):
    """
    Quantify the overhead cost of internal team transfers.

    Per policy Sec 4: Rs 305 per transfer (re-handling and administration).
    The 'transfers' field counts hand-offs between teams.
    """
    total_transfers = int(tickets['transfers'].sum())
    total_cost = total_transfers * TRANSFER_COST_INR

    print(f"\n[Step 2c] Transfer Cost Analysis:")
    print(f"  Total transfers (18 months): {total_transfers:,}")
    print(f"  Cost @ Rs {TRANSFER_COST_INR}/transfer:   Rs {total_cost:,.0f}")
    print(f"  Per quarter:                  Rs {total_cost/6:,.0f}")

    transfer_dist = tickets['transfers'].value_counts().sort_index()
    print(f"  Distribution: {dict(transfer_dist)}")

    return {
        'total_transfers': total_transfers,
        'total_cost_inr': total_cost,
    }


# ==============================================================================
# STEP 3: CATEGORIZATION & WEEKLY DIGEST
# ==============================================================================

def generate_category_summary(tickets, products):
    """
    Group tickets by category with key metrics.
    Categories are set by the chatbot intake flow and corrected by agents.
    """
    summary = tickets.groupby('category').agg(
        ticket_count=('ticket_id', 'count'),
        avg_csat=('csat_score', lambda x: round(x[x > 0].mean(), 2)),
        total_refunds_inr=('refund_amount_inr', 'sum'),
        replacements=('replacement_issued', lambda x: (x == 'Y').sum()),
        avg_transfers=('transfers', lambda x: round(x.mean(), 3)),
    ).sort_values('ticket_count', ascending=False)

    # Top SKUs per category
    sku_counts = tickets.groupby(['category', 'product_sku']).size().reset_index(name='count')

    print(f"\n[Step 3a] Category Summary ({len(summary)} categories):")
    print(summary.to_string())

    print(f"\n[Step 3a] Top 3 SKUs per Top 5 Categories:")
    for cat in summary.index[:5]:
        top = sku_counts[sku_counts['category'] == cat].nlargest(3, 'count')
        skus_str = " | ".join(
            f"{r['product_sku']}({r['count']})" for _, r in top.iterrows()
        )
        print(f"  {cat}: {skus_str}")

    return summary


def generate_weekly_digest(tickets, products):
    """
    Produce a sample Weekly Complaint Digest for the most recent full week.
    Highlights top trending categories, affected SKUs, and volume.
    """
    tickets = tickets.copy()
    tickets['week_num']  = tickets['created_at_dt'].dt.isocalendar().week.astype(int)
    tickets['year_num']  = tickets['created_at_dt'].dt.year

    # Get last full week
    last = tickets.sort_values('created_at_dt').iloc[-1]
    wk, yr = int(last['week_num']), int(last['year_num'])
    week_data = tickets[(tickets['year_num'] == yr) & (tickets['week_num'] == wk)]

    print(f"\n{'='*60}")
    print(f"  WEEKLY COMPLAINT DIGEST - Week {wk}, {yr}")
    print(f"  Tickets this week: {len(week_data)}")
    print(f"{'='*60}")

    print(f"\n  TOP CATEGORIES:")
    for cat, cnt in week_data['category'].value_counts().head(5).items():
        pct = cnt / len(week_data) * 100
        print(f"    {cat:25s}  {cnt:3d} ({pct:.0f}%)")

    print(f"\n  TOP AFFECTED SKUs:")
    for sku, cnt in week_data['product_sku'].value_counts().head(5).items():
        match = products[products['sku'] == sku]
        name = match['product_name'].values[0] if len(match) > 0 else sku
        print(f"    {sku:14s} {name:35s} {cnt:3d} tickets")

    # Refund/replacement activity this week
    refunds = week_data['refund_amount_inr'].sum()
    replacements = (week_data['replacement_issued'] == 'Y').sum()
    breaches = 0
    for ch, target in SLA_TARGETS_MINUTES.items():
        ch_data = week_data[week_data['channel'] == ch]
        resp = (ch_data['first_response_at_dt'] - ch_data['created_at_dt']).dt.total_seconds() / 60
        breaches += (resp > target).sum()

    print(f"\n  FINANCIALS THIS WEEK:")
    print(f"    Total refunds issued:    Rs {refunds:,.0f}")
    print(f"    Replacements issued:     {replacements}")
    print(f"    SLA breaches:            {breaches}")
    print(f"    Est. breach credits:     Rs {breaches * SLA_BREACH_CREDIT_INR:,.0f}")

    return week_data


# ==============================================================================
# STEP 4: AGENT PERFORMANCE EVALUATION
# ==============================================================================

def build_agent_cohorts(tickets, agents):
    """
    Create a normalized agent performance model with fair peer cohorts.

    WHY RAW "TICKETS CLOSED PER WEEK" IS FLAWED:
    1. Tier Mismatch: Tier 1 agents handle high-volume, quick-resolution
       contacts (avg 5-10 hrs). Tier 2 (Escalations & Warranty) handles
       complex cases averaging 136 hrs. Comparing raw volume is unfair.
    2. Channel Differences: Chat handle time (~6 hrs) vs Voice (~5 hrs) vs
       Email (~9 hrs) vs Logistics (~42 hrs) means identical effort produces
       very different ticket counts.
    3. Transfer Complexity: Agents on teams with high transfer rates (Returns
       at 15.5%) spend time on re-routing, not captured by close counts.
    4. Roster Variation: Night-shift agents cover different queue depth than
       day-shift agents; tenure affects assigned ticket complexity.

    NORMALISED MODEL:
    - Agents grouped into cohorts: Tier x Team (e.g., Tier 1 Chat, Tier 2 Warranty)
    - Metrics Z-scored within cohort to compare like-with-like
    - Composite score: 30% volume + 30% efficiency + 40% quality (CSAT)
    """
    merged = tickets.merge(agents, on='agent_id', how='left', suffixes=('', '_agent'))

    # Calculate handle time
    merged['handle_hours'] = (
        (merged['resolved_at_dt'] - merged['created_at_dt'])
        .dt.total_seconds() / 3600
    )

    # Define cohorts
    def assign_cohort(row):
        if row['tier'] == 2:
            return 'Tier 2 - Escalations & Warranty'
        team = str(row.get('team', 'Unknown'))
        if 'Chat' in team:     return 'Tier 1 - Chat'
        if 'Email' in team:    return 'Tier 1 - Email'
        if 'Voice' in team:    return 'Tier 1 - Voice'
        if 'Logistics' in team: return 'Tier 1 - Logistics'
        if 'Billing' in team:  return 'Tier 1 - Billing'
        if 'Returns' in team:  return 'Tier 1 - Returns'
        return f'Tier {row["tier"]} - {team}'

    merged['cohort'] = merged.apply(assign_cohort, axis=1)

    # Cohort benchmarks
    cohort_stats = merged.groupby('cohort').agg(
        agents=('agent_id', 'nunique'),
        total_tickets=('ticket_id', 'count'),
        avg_handle_hours=('handle_hours', lambda x: round(x.mean(), 1)),
        avg_csat=('csat_score', lambda x: round(x[x > 0].mean(), 2)),
        avg_transfers=('transfers', lambda x: round(x.mean(), 3)),
    ).reset_index()

    print(f"\n[Step 4] Cohort Benchmark Statistics:")
    print(cohort_stats.to_string(index=False))

    # Per-agent metrics
    name_col = 'name' if 'name' in merged.columns else 'name_agent'
    agent_perf = merged.groupby(['agent_id', name_col, 'cohort']).agg(
        tickets_closed=('ticket_id', 'count'),
        avg_handle_hours=('handle_hours', 'mean'),
        avg_csat=('csat_score', lambda x: x[x > 0].mean()),
        avg_transfers=('transfers', 'mean'),
    ).reset_index()

    # Z-score normalisation within cohort
    for metric in ['tickets_closed', 'avg_handle_hours', 'avg_csat']:
        mu = agent_perf.groupby('cohort')[metric].transform('mean')
        sigma = agent_perf.groupby('cohort')[metric].transform('std').replace(0, 1)
        agent_perf[f'{metric}_z'] = (agent_perf[metric] - mu) / sigma

    # Composite: +volume, -handle_time, +csat
    agent_perf['composite_score'] = (
        agent_perf['tickets_closed_z'] * 0.30 +
        (-agent_perf['avg_handle_hours_z']) * 0.30 +
        agent_perf['avg_csat_z'] * 0.40
    )

    # Performance bands
    agent_perf['performance_band'] = pd.cut(
        agent_perf['composite_score'],
        bins=[-np.inf, -0.5, 0.0, 0.5, np.inf],
        labels=['Needs Support', 'Developing', 'Proficient', 'Excelling']
    )

    agent_perf_sorted = agent_perf.sort_values('composite_score', ascending=False)

    print(f"\n[Step 4] Agent Performance Leaderboard (normalised within cohort):")
    display_cols = ['agent_id', name_col, 'cohort', 'tickets_closed',
                    'avg_handle_hours', 'avg_csat', 'composite_score', 'performance_band']
    print(agent_perf_sorted[display_cols].to_string(index=False))

    # Band distribution
    band_dist = agent_perf['performance_band'].value_counts()
    print(f"\n[Step 4] Performance Band Distribution:")
    for band, count in band_dist.items():
        print(f"  {band}: {count} agents")

    return agent_perf_sorted, cohort_stats


# ==============================================================================
# STEP 5: FINANCIAL SUMMARY
# ==============================================================================

def financial_summary(sla_result, violation_result, transfer_result):
    """Compute and display the total financial leakage."""
    sla_cost      = sla_result['total_credit_cost_inr']
    violation_cost = violation_result['total_loss_inr']
    transfer_cost  = transfer_result['total_cost_inr']
    total_18m      = sla_cost + violation_cost + transfer_cost
    total_quarterly = total_18m / 6

    print(f"\n{'='*60}")
    print(f"  FINANCIAL LEAKAGE SUMMARY")
    print(f"{'='*60}")
    print(f"  SLA Breach Credits (18m):      Rs {sla_cost:>12,.0f}")
    print(f"  Policy Violations (18m):       Rs {violation_cost:>12,.0f}")
    print(f"  Transfer Overhead (18m):       Rs {transfer_cost:>12,.0f}")
    print(f"  {'-'*45}")
    print(f"  TOTAL (18 months):             Rs {total_18m:>12,.0f}")
    print(f"  ESTIMATED PER QUARTER:         Rs {total_quarterly:>12,.0f}")
    print(f"{'='*60}")

    return {
        'sla_cost_inr': sla_cost,
        'violation_cost_inr': violation_cost,
        'transfer_cost_inr': transfer_cost,
        'total_18m_inr': total_18m,
        'quarterly_inr': total_quarterly,
    }


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  VIREO AUDIO - SUPPORT DATA ANALYSIS")
    print("  Full Execution Script")
    print("=" * 60)

    # Load
    data = load_data(DATA_DIR)

    # Step 1: Clean & Deduplicate
    tickets_clean = clean_and_deduplicate(data['tickets'])

    # Step 2: Financial Analysis
    sla_result       = calculate_sla_breaches(tickets_clean)
    violation_result = detect_policy_violations(tickets_clean, data['products'])
    transfer_result  = calculate_transfer_costs(tickets_clean)

    # Step 3: Categorization
    cat_summary  = generate_category_summary(tickets_clean, data['products'])
    weekly_digest = generate_weekly_digest(tickets_clean, data['products'])

    # Step 4: Agent Performance
    agent_perf, cohort_stats = build_agent_cohorts(tickets_clean, data['agents'])

    # Step 5: Financial Summary
    financials = financial_summary(sla_result, violation_result, transfer_result)

    print("\n[DONE] Analysis complete. All figures based on deduplicated,"
          " timestamp-corrected dataset of {:,} tickets.".format(len(tickets_clean)))
