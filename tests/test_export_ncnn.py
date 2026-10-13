"""Exporter control-flow tests; native inference is exercised on each edge."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('export_ncnn', ROOT / 'tools/export_ncnn.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class Converter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stage = self.root / 'stage'
        self.stage.mkdir()
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('release/pnnx', b'verified converter')
            archive.writestr('../../unwanted', b'never extracted')
        self.data = data.getvalue()
        self.hash = hashlib.sha256(self.data).hexdigest()

    def test_verified_download_and_offline_cache(self):
        with patch.object(exporter, 'SHA256', self.hash), patch.object(
                exporter.urllib.request, 'urlopen', return_value=io.BytesIO(self.data)) as download:
            binary = exporter.install_converter(self.root / 'cache', self.stage)
            self.assertEqual(binary.read_bytes(), b'verified converter')
            self.assertTrue(os.access(binary, os.X_OK))
            self.assertFalse((self.root / 'unwanted').exists())
            exporter.install_converter(self.root / 'cache', self.stage)
            download.assert_called_once()

    def test_bad_download_is_not_cached_or_executed(self):
        with patch.object(exporter, 'SHA256', '0' * 64), patch.object(
                exporter.urllib.request, 'urlopen', return_value=io.BytesIO(self.data)):
            with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch'):
                exporter.install_converter(self.root / 'cache', self.stage)
        self.assertFalse((self.stage / 'pnnx').exists())
        self.assertEqual(list((self.root / 'cache').iterdir()), [])

    def test_corrupt_cache_fails_closed(self):
        cache = self.root / 'cache'
        cache.mkdir()
        (cache / exporter.ASSET).write_bytes(b'corrupt')
        with patch.object(exporter.urllib.request, 'urlopen') as download:
            with self.assertRaisesRegex(RuntimeError, 'cache SHA256 mismatch'):
                exporter.install_converter(cache, self.stage)
            download.assert_not_called()


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.models = self.root / 'models'
        self.models.mkdir()
        self.pt = self.models / 'swift.pt'
        self.pt.write_bytes(b'original pt')
        self.old = self.models / 'swift_ncnn_model'
        self.old.mkdir()
        (self.old / 'previous').write_text('old model')
        self.bin = self.root / 'cvenv/bin'
        self.bin.mkdir(parents=True)
        (self.bin / 'yolo').touch()
        for mock in (patch.object(exporter, 'ROOT', self.root),
                     patch.object(exporter.platform, 'system', return_value='Linux'),
                     patch.object(exporter.platform, 'machine', return_value='aarch64'),
                     patch.object(exporter.sys, 'executable', str(self.bin / 'python')),
                     patch.object(exporter, 'install_converter', side_effect=self.converter)):
            mock.start()
            self.addCleanup(mock.stop)

    @staticmethod
    def converter(cache, stage):
        (stage / 'pnnx').write_bytes(b'pinned converter')

    def runner(self, command, **kwargs):
        stage = kwargs['cwd']
        paths = kwargs['env']['PATH'].split(os.pathsep)
        self.assertEqual(paths[:2], [str(stage), str(self.bin)])
        self.assertEqual(kwargs['env']['PYTHONIOENCODING'], 'utf-8')
        self.assertTrue(kwargs['check'])
        self.assertEqual((self.old / 'previous').read_text(), 'old model')
        if 'export' in command:
            self.assertEqual((stage / 'swift.pt').read_bytes(), b'original pt')
            candidate = stage / 'swift_ncnn_model'
            candidate.mkdir()
            for name in ('model.ncnn.param', 'model.ncnn.bin', 'metadata.yaml'):
                (candidate / name).write_text('new model')
        else:
            self.assertIn('faulthandler', command)
            self.assertEqual(kwargs['timeout'], 180)
        return subprocess.CompletedProcess(command, 0)

    def test_success_activates_only_after_smoke_and_keeps_backup(self):
        with patch.object(exporter.subprocess, 'run', side_effect=self.runner) as run:
            exporter.export_model(self.pt)
        self.assertEqual(run.call_count, 2)
        self.assertEqual((self.old / 'model.ncnn.bin').read_text(), 'new model')
        saved = list((self.root / 'logs/ncnn-backups').glob('*/swift_ncnn_model/previous'))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(), 'old model')
        self.assertEqual(self.pt.read_bytes(), b'original pt')
        self.assertEqual(list(self.models.glob('.ncnn-export-*')), [])

    def test_crash_or_timeout_preserves_previous_model(self):
        for failure in (subprocess.CalledProcessError(-11, ['inference']),
                        subprocess.TimeoutExpired(['inference'], 180)):
            with self.subTest(failure=failure):
                def run(command, **kwargs):
                    result = self.runner(command, **kwargs)
                    if 'export' not in command:
                        raise failure
                    return result
                with patch.object(exporter.subprocess, 'run', side_effect=run):
                    with self.assertRaises(type(failure)):
                        exporter.export_model(self.pt)
                self.assertEqual((self.old / 'previous').read_text(), 'old model')
                self.assertEqual(list(self.models.glob('.ncnn-export-*')), [])

    def test_export_failure_preserves_previous_model(self):
        with patch.object(exporter.subprocess, 'run', side_effect=
                          subprocess.CalledProcessError(1, ['export'])) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                exporter.export_model(self.pt)
        self.assertEqual(run.call_count, 1)
        self.assertTrue((self.old / 'previous').exists())

    def test_failed_activation_restores_previous_model(self):
        candidate = self.models / 'candidate'
        candidate.mkdir()
        real_rename = Path.rename
        def rename(path, target):
            if path == candidate:
                raise OSError('simulated rename failure')
            return real_rename(path, target)
        with patch.object(Path, 'rename', rename):
            with self.assertRaises(OSError):
                exporter.publish(candidate, self.old, self.root / 'backups')
        self.assertEqual((self.old / 'previous').read_text(), 'old model')


class Makefile(unittest.TestCase):
    def test_export_failure_stops_loop_and_make(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Makefile').write_bytes((ROOT / 'Makefile').read_bytes())
            (root / 'cvenv/bin').mkdir(parents=True)
            (root / 'cvenv/bin/activate').touch()
            python = root / 'cvenv/bin/python'
            python.write_text('#!/bin/sh\necho called >> calls\nexit 7\n')
            python.chmod(0o755)
            (root / 'models').mkdir()
            (root / 'models/a.pt').touch()
            (root / 'models/b.pt').touch()
            result = subprocess.run(['make', 'export_models'], cwd=root,
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((root / 'calls').read_text(), 'called\n')
            self.assertNotIn('All models exported', result.stdout)


if __name__ == '__main__':
    unittest.main()
