import unittest

from app.domain.entities.detail_design_review import review_detail_design


class ReviewServiceTest(unittest.TestCase):
    def test_review_reports_missing_sections(self):
        payload = {
            "analysis": {"summary": "Only summary"},
            "detailDesign": {"screen": {}},
        }
        result = review_detail_design(payload, 1)
        self.assertEqual(result["status"], "NG")
        self.assertGreaterEqual(len(result["findings"]), 1)

    def test_review_findings_include_rule_metadata(self):
        payload = {
            "analysis": {"summary": "Only summary"},
            "detailDesign": {"screen": {}, "api": {}, "batch": {}},
        }

        result = review_detail_design(payload, 1)

        finding = result["findings"][0]
        self.assertIsInstance(finding, dict)
        self.assertIn("ruleId", finding)
        self.assertIn("severity", finding)
        self.assertIn("message", finding)
        self.assertIn("path", finding)


if __name__ == "__main__":
    unittest.main()
