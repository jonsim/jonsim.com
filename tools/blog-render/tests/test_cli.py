import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name) / 'blog'
        self.base_dir.mkdir()
        self.out_dir = Path(self.temp_dir.name) / 'output'

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renders_blogs_recursively(self):
        pass


if __name__ == '__main__':
    unittest.main()
