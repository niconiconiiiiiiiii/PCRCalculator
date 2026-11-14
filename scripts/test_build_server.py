import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

spec = importlib.util.spec_from_file_location('build_server', Path(__file__).with_name('build_server.py'))
build_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_server)

class ServerPackageTests(unittest.TestCase):
    def test_fresh_publish_preserves_previous_package_and_does_not_bundle_its_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / 'Linux/publish'
            old.mkdir(parents=True)
            (old / 'jp10067700.db').write_text('old')
            def publish(command, **kwargs):
                self.assertIn('linux-x64', command)
                target = Path(command[-1])
                target.mkdir()
                (target / 'PCRCalculatorServer').write_text('new')
            with patch('sys.argv', ['build_server', '--target', 'linux', '--output-root', tmp]), patch.object(build_server.subprocess, 'run', side_effect=publish):
                build_server.main()
            self.assertTrue((root / 'mzq-linux-x64.zip').is_file())
            self.assertFalse((old / 'jp10067700.db').exists())
            self.assertEqual(len(list(root.glob('Linux-previous-*/Linux/publish/jp10067700.db'))), 1)

    def test_publish_failure_leaves_previous_package_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'Linux'
            target.mkdir()
            (target / 'previous').write_text('intact')
            with patch('sys.argv', ['build_server', '--target', 'linux', '--output-root', tmp]), patch.object(build_server.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'dotnet')):
                with self.assertRaises(subprocess.CalledProcessError):
                    build_server.main()
            self.assertEqual((target / 'previous').read_text(), 'intact')

    def test_arm64_package_uses_arm64_rid_and_keeps_x64_package_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            x64 = root / 'Linux' / 'existing'
            x64.mkdir(parents=True)
            (x64 / 'sentinel.txt').write_text('unchanged')

            def publish(command, **kwargs):
                self.assertEqual(command[command.index('-r') + 1], 'linux-arm64')
                self.assertEqual(command[command.index('--self-contained') + 1], 'true')
                target = Path(command[-1])
                target.mkdir()
                (target / 'PCRCalculatorServer').write_text('arm64 test binary')

            argv = ['build_server', '--target', 'linux-arm64', '--output-root', tmp]
            with patch('sys.argv', argv), patch.object(build_server.subprocess, 'run', side_effect=publish):
                build_server.main()

            self.assertTrue((root / 'mzq-linux-arm64.zip').is_file())
            self.assertTrue((root / 'LinuxARM64' / 'publish' / 'PCRCalculatorServer').is_file())
            self.assertEqual((x64 / 'sentinel.txt').read_text(), 'unchanged')
            self.assertFalse((root / 'mzq-linux-x64.zip').exists())

    def test_arm64_framework_dependent_and_no_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            def publish(command, **kwargs):
                self.assertEqual(command[command.index('-r') + 1], 'linux-arm64')
                self.assertEqual(command[command.index('--self-contained') + 1], 'false')
                target = Path(command[-1])
                target.mkdir()
                (target / 'PCRCalculatorServer.dll').write_text('test')

            argv = ['build_server', '--target', 'linux-arm64', '--output-root', tmp,
                    '--framework-dependent', '--no-zip']
            with patch('sys.argv', argv), patch.object(build_server.subprocess, 'run', side_effect=publish):
                build_server.main()
            self.assertFalse((Path(tmp) / 'mzq-linux-arm64.zip').exists())
            self.assertTrue((Path(tmp) / 'LinuxARM64' / 'publish' / 'PCRCalculatorServer.dll').is_file())


if __name__ == '__main__':
    unittest.main()
