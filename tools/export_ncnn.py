#!/usr/bin/env python3
"""Export with verified PNNX on Pi5; publish only after subprocess inference passes."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

PNNX_VERSION = "20260526"
ASSET = f"pnnx-{PNNX_VERSION}-linux-aarch64.zip"
URL = f"https://github.com/pnnx/pnnx/releases/download/{PNNX_VERSION}/{ASSET}"
SHA256 = "5ec705eba0f9bec09652f966244201f5af2bcf8657b1580c46028fe83183f8b1"
ROOT = Path(__file__).resolve().parents[1]

SMOKE_TEST = """
import sys
import numpy as np
from ultralytics import YOLO
model = YOLO(sys.argv[1], task='detect')
frame = np.zeros((640, 640, 3), dtype=np.uint8)
for i in range(3):
    model.predict(source=frame, verbose=False)
    print(f'NCNN inference {i + 1}/3 OK', flush=True)
"""


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def install_converter(cache, stage):
    """Verify archive on every use, and extract only its single executable."""
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / ASSET
    if not archive.exists():
        print(f'Downloading PNNX {PNNX_VERSION}: {URL}', flush=True)
        with tempfile.NamedTemporaryFile(dir=cache, suffix='.download', delete=False) as out:
            temporary = Path(out.name)
            try:
                with urllib.request.urlopen(URL, timeout=120) as response:
                    shutil.copyfileobj(response, out)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            if digest(temporary) != SHA256:
                raise RuntimeError('PNNX download SHA256 mismatch; export cancelled')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(archive) != SHA256:
        raise RuntimeError(f'PNNX cache SHA256 mismatch; remove {archive} and retry')
    with zipfile.ZipFile(archive) as bundle:
        members = [m for m in bundle.infolist()
                   if not m.is_dir() and Path(m.filename).name == 'pnnx']
        if len(members) != 1:
            raise RuntimeError('PNNX archive does not contain exactly one executable')
        executable = stage / 'pnnx'
        with bundle.open(members[0]) as src, executable.open('wb') as dst:
            shutil.copyfileobj(src, dst)
    executable.chmod(0o755)
    print(f'PNNX {PNNX_VERSION}: SHA256 verified', flush=True)
    return executable


def publish(candidate, destination, backup_root):
    """Keep the previous model; restore it if the final rename fails."""
    previous = None
    if destination.exists():
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=destination.name + '-', dir=backup_root))
        previous = backup / destination.name
        destination.rename(previous)
    try:
        candidate.rename(destination)
    except BaseException:
        if previous is not None:
            previous.rename(destination)
        raise
    if previous is not None:
        print(f'Previous model preserved: {previous}', flush=True)


def export_model(model):
    if platform.system() != 'Linux' or platform.machine().lower() not in ('aarch64', 'arm64'):
        raise RuntimeError('This pinned exporter requires Linux ARM64 (Raspberry Pi 5, 64-bit OS)')
    model = model.resolve(strict=True)
    if model.suffix.lower() != '.pt' or not model.is_file():
        raise ValueError(f'Expected a .pt model: {model}')
    cli = Path(sys.executable).parent / 'yolo'
    if not cli.is_file():
        raise RuntimeError(f'YOLO CLI missing: {cli}. Run make module first.')
    logs = ROOT / 'logs'
    # Stage beside the model so activation uses a same-filesystem rename.
    with tempfile.TemporaryDirectory(prefix='.ncnn-export-', dir=model.parent) as directory:
        stage = Path(directory)
        install_converter(logs / 'pnnx', stage)
        staged_pt = stage / model.name
        shutil.copy2(model, staged_pt)
        env = os.environ.copy()
        # v8.3.217 selects ./pnnx but launches it by name: PATH must include stage.
        # Bare pip subprocesses must also use this virtualenv, not system Python.
        env['PATH'] = os.pathsep.join((str(stage), str(cli.parent), env.get('PATH', '')))
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONFAULTHANDLER'] = '1'
        print(f'Exporting {model} with PNNX {PNNX_VERSION}', flush=True)
        subprocess.run([sys.executable, str(cli), 'export', f'model={staged_pt}',
                        'format=ncnn'], cwd=stage, env=env, check=True)
        candidate = stage / (model.stem + '_ncnn_model')
        for filename in ('model.ncnn.param', 'model.ncnn.bin', 'metadata.yaml'):
            file = candidate / filename
            if not file.is_file() or not file.stat().st_size:
                raise RuntimeError(f'Export missing or empty: {file}')
        # A native crash is confined to this process; the old model remains intact.
        subprocess.run([sys.executable, '-X', 'faulthandler', '-u', '-c', SMOKE_TEST,
                        str(candidate)], cwd=stage, env=env, check=True, timeout=180)
        destination = model.with_name(model.stem + '_ncnn_model')
        publish(candidate, destination, logs / 'ncnn-backups')
        print(f'Validated NCNN model activated: {destination}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    args = parser.parse_args()
    try:
        export_model(args.model)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile,
            subprocess.SubprocessError) as exc:
        print(f'NCNN export FAILED: {exc}', file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
