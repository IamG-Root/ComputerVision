import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('copy_config', ROOT / 'tools/copy_config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class Merge(unittest.TestCase):
    def test_real_config_preserves_new_parameters_and_derived_topic(self):
        destination = (ROOT / 'module/config.py').read_text()
        source = '\n'.join(line for line in destination.splitlines()
                           if not line.startswith(('CLOCK_SYNCHRONIZED =', 'PROTOCOL_VERSION =')))
        source = source.replace('MODULE_NAME = "MODULEX"', 'MODULE_NAME = "MODULE7"')
        source = source.replace('CAMERA_H = 2.545', 'CAMERA_H = 3.1')
        source = source.replace('EXCLUSIONS = []', 'EXCLUSIONS = [[(1, 2), (3, 4), (5, 6)]]')
        merged, copied, retained, ignored = config.merge(source, destination)
        _, values = config.parse_config(merged, 'result')
        self.assertEqual(values['MODULE_NAME'], 'MODULE7')
        self.assertEqual(values['TOPIC'], 'CV/MODULE7')
        self.assertEqual(values['CAMERA_H'], 3.1)
        self.assertEqual(values['EXCLUSIONS'], [[(1, 2), (3, 4), (5, 6)]])
        self.assertIn("TOPIC = 'CV/' + MODULE_NAME", merged)
        self.assertEqual(retained, ['CLOCK_SYNCHRONIZED', 'PROTOCOL_VERSION'])
        self.assertFalse(values['CLOCK_SYNCHRONIZED'])
        self.assertEqual(values['PROTOCOL_VERSION'], 2)
        self.assertIn('# Camera height (Meters, m)', merged)
        self.assertIn('╔═══════════════╗', merged)

    def test_unicode_offsets_multiline_and_inline_comments(self):
        merged, *_ = config.merge('NAME="è"; SIZE=(1 +\n 2)\n',
                                  'NAME="à"; SIZE=0 # dimensione\n')
        self.assertEqual(config.parse_config(merged, 'result')[1], {'NAME': 'è', 'SIZE': 3})
        self.assertIn('# dimensione', merged)

    def test_source_only_helpers_are_not_added(self):
        merged, copied, retained, ignored = config.merge('BASE=10\nPORT=BASE+2\n', 'PORT=0\nNEW=True\n')
        self.assertEqual(merged, 'PORT=12\nNEW=True\n')
        self.assertEqual(ignored, ['BASE'])

    def test_unsafe_code_duplicates_or_missing_references_rejected(self):
        for source in ('A=__import__("os").getcwd()\n', 'import os\nA=1\n',
                       'A=1\nA=2\n', 'A=MISSING+1\n'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                config.merge(source, 'A=0\n')


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src, self.dst = self.root/'old config.py', self.root/'config.py'
        self.src.write_text('A=7\n')
        self.dst.write_text('A=1 # comment\nNEW=False\n')
        self.original = self.dst.read_bytes()

    def test_atomic_copy_backup_and_idempotence(self):
        backup = config.copy_config(self.src, self.dst)
        self.assertEqual(backup.read_bytes(), self.original)
        self.assertEqual(self.src.read_text(), 'A=7\n')
        self.assertEqual(self.dst.read_text(), 'A=7 # comment\nNEW=False\n')
        self.assertIsNone(config.copy_config(self.src, self.dst))
        self.assertEqual(len(list(self.root.glob('config.py.backup-*'))), 1)

    def test_dry_run_and_failure_leave_original_untouched(self):
        config.copy_config(self.src, self.dst, dry_run=True)
        self.assertEqual(self.dst.read_bytes(), self.original)
        self.assertEqual(len(list(self.root.iterdir())), 2)
        with patch.object(config.os, 'replace', side_effect=OSError('simulated error')):
            with self.assertRaises(OSError):
                config.copy_config(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), self.original)

    def test_same_file_rejected(self):
        with self.assertRaises(ValueError):
            config.copy_config(self.dst, self.dst)

    def test_make_source_with_spaces_and_shell_characters_is_literal(self):
        (self.root/'Makefile').write_bytes((ROOT/'Makefile').read_bytes())
        (self.root/'tools').mkdir()
        (self.root/'tools/copy_config.py').write_text(
            'import os\nfrom pathlib import Path\nPath("received").write_text(os.environ["COPY_CONFIG_SOURCE"])\n')
        source = '../old dir/$(touch BAD); config.py'
        result = subprocess.run(['make', 'copy_config', f'PYTHON={sys.executable}', f'SOURCE={source}'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root/'received').read_text(), source)
        self.assertFalse((self.root/'BAD').exists())

    def test_cli_missing_source_has_actionable_error(self):
        import os
        env = {k: v for k, v in os.environ.items() if k != 'COPY_CONFIG_SOURCE'}
        result = subprocess.run([sys.executable, str(ROOT/'tools/copy_config.py')], env=env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('make copy_config SOURCE=', result.stderr)


if __name__ == '__main__':
    unittest.main()
