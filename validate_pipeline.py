"""
VIREO AUDIO - PIPELINE VALIDATION TEST SUITE
--------------------------------------------
Programmatically asserts correctness of deduplication,
timestamp offsets, policy violations, and math calculations.
"""

import unittest
import os
import vireo_analysis


class TestVireoPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ref_docs = os.path.join(base_dir, "reference docs")
        cls.data_dir = ref_docs if os.path.exists(ref_docs) else base_dir
        cls.data = vireo_analysis.load_data(cls.data_dir)
        cls.clean_tickets = vireo_analysis.clean_and_deduplicate(cls.data['tickets'])
        cls.sla_res = vireo_analysis.calculate_sla_breaches(cls.clean_tickets)
        cls.viol_res = vireo_analysis.detect_policy_violations(cls.clean_tickets, cls.data['products'])
        cls.trans_res = vireo_analysis.calculate_transfer_costs(cls.clean_tickets)
        cls.fin_res = vireo_analysis.financial_summary(cls.sla_res, cls.viol_res, cls.trans_res)

    def test_01_deduplication(self):
        """Assert exact deduplication count (12,528 raw -> 11,875 clean, 653 removed)."""
        raw_count = len(self.data['tickets'])
        clean_count = len(self.clean_tickets)
        self.assertEqual(raw_count, 12528)
        self.assertEqual(clean_count, 11875)
        self.assertEqual(raw_count - clean_count, 653)

    def test_02_policy_violations(self):
        """Assert exact detection of 4 double-dipping policy violations."""
        self.assertEqual(self.viol_res['violation_count'], 4)
        self.assertAlmostEqual(self.viol_res['total_loss_inr'], 17910.0, places=2)

    def test_03_transfer_costs(self):
        """Assert exact transfer count (1,169 transfers @ Rs 305 = Rs 3,56,545)."""
        self.assertEqual(self.trans_res['total_transfers'], 1169)
        self.assertAlmostEqual(self.trans_res['total_cost_inr'], 356545.0, places=2)

    def test_04_sla_breaches(self):
        """Assert SLA breaches count and total credit cost (992 breaches @ Rs 350 = Rs 3,47,200)."""
        self.assertEqual(self.sla_res['total_breached'], 992)
        self.assertAlmostEqual(self.sla_res['total_credit_cost_inr'], 347200.0, places=2)

    def test_05_quarterly_leakage(self):
        """Assert quarterly leakage run-rate (Rs 7,21,655 total / 6 quarters = Rs 120,276)."""
        expected_quarterly = 721655.0 / 6.0
        self.assertAlmostEqual(self.fin_res['quarterly_inr'], expected_quarterly, places=2)


if __name__ == '__main__':
    unittest.main()
