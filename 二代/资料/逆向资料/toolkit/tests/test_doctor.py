import unittest

from uw2toolkit.config import ToolkitConfig
from uw2toolkit.doctor import run_doctor, summarize


class DoctorTests(unittest.TestCase):
    def test_doctor_returns_summary(self):
        cfg = ToolkitConfig.from_env()
        results = run_doctor(cfg)
        summary = summarize(results)
        self.assertIn('ok', summary)
        self.assertIn('warn', summary)
        self.assertIn('missing', summary)
        self.assertTrue(any(r['name'] == 'toolkit_root' for r in summary['results']))


if __name__ == '__main__':
    unittest.main()
