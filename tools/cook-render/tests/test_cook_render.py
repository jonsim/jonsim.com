import io
import unittest
from contextlib import redirect_stdout

from cook_render import main


class TestMain(unittest.TestCase):
    def test_prints_greeting(self) -> None:
        # The command gives the same greeting wherever it is invoked.
        output = io.StringIO()

        with redirect_stdout(output):
            main()

        self.assertEqual('Hello, world!\n', output.getvalue())


if __name__ == '__main__':
    unittest.main()
