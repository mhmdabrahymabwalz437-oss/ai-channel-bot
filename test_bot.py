import os
import tempfile
import unittest
from storage import Storage
from config import Settings

class BotTests(unittest.TestCase):
    def test_storage_deduplicates_sources(self):
        with tempfile.TemporaryDirectory() as d:
            s = Storage(os.path.join(d, "x.db"))
            self.assertFalse(s.already_used("https://example.com/a"))
            s.save("t", "c", "https://example.com/a", "", "dry-run")
            self.assertTrue(s.already_used("https://example.com/a"))

    def test_default_is_dry_run(self):
        self.assertTrue(Settings().dry_run)

if __name__ == "__main__":
    unittest.main()
