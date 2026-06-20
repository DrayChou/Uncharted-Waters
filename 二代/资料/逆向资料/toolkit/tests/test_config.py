from pathlib import Path
import unittest

from uw2toolkit.config import ToolkitConfig


class ConfigTests(unittest.TestCase):
    def test_default_paths_are_repo_relative(self):
        cfg = ToolkitConfig.from_env()
        self.assertTrue(str(cfg.toolkit_root).endswith('二代/资料/逆向资料/toolkit'))
        self.assertEqual(cfg.raw_dir, cfg.toolkit_root / 'raw' / 'Koukai2')
        self.assertEqual(cfg.output_dir, cfg.toolkit_root / 'output')
        self.assertEqual(cfg.chip_no_path.name, 'Chip_no.dat')
        self.assertEqual(cfg.exe_path.name, 'Main.exe')


if __name__ == '__main__':
    unittest.main()
