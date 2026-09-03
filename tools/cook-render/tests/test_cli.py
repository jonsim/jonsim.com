import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cook_render import main


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name) / 'recipes'
        self.base_dir.mkdir()
        self.out_dir = Path(self.temp_dir.name) / 'output'

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renders_recipes_recursively(self):
        # Create a recipe at the root of base_dir and one in a subfolder
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        sub_dir = self.base_dir / 'desserts'
        sub_dir.mkdir()
        (sub_dir / 'cake.cook').write_text('Bake @flour{200%g}.', encoding='utf-8')

        dummy_recipe = {
            'metadata': {'map': {'title': 'Dummy'}},
            'sections': [],
            'ingredients': [],
            'cookware': [],
            'timers': [],
            'inline_quantities': [],
        }

        with patch('cook_render.load_recipe', return_value=dummy_recipe):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 0)

        simple_html = self.out_dir / 'simple.html'
        cake_html = self.out_dir / 'desserts' / 'cake.html'
        index_html = self.out_dir / 'index.html'

        self.assertTrue(simple_html.exists())
        self.assertTrue(cake_html.exists())
        self.assertTrue(index_html.exists())
        self.assertIn('<!DOCTYPE html>', simple_html.read_text(encoding='utf-8'))
        self.assertIn('<h2>Dummy</h2>', cake_html.read_text(encoding='utf-8'))
        self.assertIn(
            '<a class="recipe-row" href="simple.html">',
            index_html.read_text(encoding='utf-8'),
        )
        self.assertIn(
            '<a class="recipe-row" href="desserts/cake.html">',
            index_html.read_text(encoding='utf-8'),
        )

    def test_nonexistent_base_path(self):
        with self.assertRaises(SystemExit):
            main(['-b', str(self.base_dir / 'does_not_exist')])

    def test_cook_command_not_found(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        with patch('cook_render.load_recipe', side_effect=FileNotFoundError):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    def test_cook_called_process_error(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        err = subprocess.CalledProcessError(
            returncode=1, cmd=['cook'], stderr='Parse error'
        )
        with patch('cook_render.load_recipe', side_effect=err):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    def test_cook_json_decode_error(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        err = json.JSONDecodeError('Expecting value', '', 0)
        with patch('cook_render.load_recipe', side_effect=err):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    def test_real_cook_execution(self):
        # Run against tests/examples with actual cook CLI if available
        examples_dir = Path(__file__).parent / 'examples'
        ret = main(['-b', str(examples_dir), '-o', str(self.out_dir)])
        self.assertEqual(ret, 0)

        self.assertTrue((self.out_dir / 'index.html').exists())
        self.assertTrue((self.out_dir / 'pancakes.html').exists())
        self.assertTrue((self.out_dir / 'tomato-sauce.html').exists())
        self.assertTrue((self.out_dir / 'minimal.html').exists())

        pancakes_content = (self.out_dir / 'pancakes.html').read_text(encoding='utf-8')
        self.assertIn('<h2>Pancakes</h2>', pancakes_content)
        self.assertIn('<span class="name">flour</span>', pancakes_content)

        index_content = (self.out_dir / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<h1>Recipes</h1>', index_content)
        self.assertIn('<a class="recipe-row" href="pancakes.html">', index_content)


if __name__ == '__main__':
    unittest.main()
