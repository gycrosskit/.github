#!/usr/bin/env python3
"""执行真实 composite shell，核验调用项目路径、范围输出与失败退出码。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def shell(action):
    return textwrap.dedent((ROOT / 'actions' / action / 'action.yml').read_text().split('      run: |\n', 1)[1].split('    - ', 1)[0])


def main():
    with tempfile.TemporaryDirectory(prefix='ci action ') as temporary:
        workspace = Path(temporary) / 'component with spaces'
        workspace.mkdir()
        environment = dict(os.environ, GITHUB_WORKSPACE=str(workspace),
                           SHARED_ACTION_PATH=str(ROOT / 'actions/ci-tools'))
        subprocess.run(['bash', '-c', shell('ci-tools')], env=environment, check=True)
        for name in ('ci-changes.py', 'ci-run.py', 'ci-native-cache.py'):
            assert (workspace / 'scripts' / name).read_bytes() == (ROOT / 'templates' / name).read_bytes()
        manifest = workspace / 'gradle/native-toolchain.properties'
        manifest.parent.mkdir()
        manifest.write_text('kotlin=2.0.21-1.0.0\ntargets=ios_arm64\n')
        (workspace / 'build.gradle.kts').write_text('plugins { kotlin("multiplatform") version "2.0.21-1.0.0" }')
        bin_dir = workspace / 'bin'
        bin_dir.mkdir()
        xcode = bin_dir / 'xcodebuild'
        xcode.write_text('#!/bin/sh\nprintf "Xcode 16.4\\nBuild version test\\n"\n')
        xcode.chmod(0o755)
        environment['PATH'] = str(bin_dir) + os.pathsep + environment['PATH']
        key = subprocess.check_output([sys.executable, str(workspace / 'scripts/ci-native-cache.py'), '--key'],
                                      cwd=temporary, env=environment, text=True)
        assert key.startswith('key=konan-v2-'), key
        manifest.write_text('kotlin=2.0.21-1.0.0\ntargets=ios_arm64,ios_x64\n')
        second = subprocess.check_output([sys.executable, str(workspace / 'scripts/ci-native-cache.py'), '--key'],
                                         cwd=temporary, env=environment, text=True)
        assert key != second, 'Cache identity must follow the calling component manifest'
        event = workspace / 'event.json'
        event.write_text('{}')
        output = workspace / 'output'
        environment.update(GITHUB_EVENT_NAME='push', GITHUB_EVENT_PATH=str(event), GITHUB_OUTPUT=str(output))
        result = subprocess.run([sys.executable, str(workspace / 'scripts/ci-changes.py')],
                                cwd=workspace, env=environment, capture_output=True, text=True, check=True)
        assert result.stdout == output.read_text() == 'source=false\n'
        event.write_text('{malformed')
        environment['GITHUB_EVENT_NAME'] = 'pull_request'
        result = subprocess.run([sys.executable, str(workspace / 'scripts/ci-changes.py')],
                                cwd=workspace, env=environment, capture_output=True, text=True, check=True)
        assert result.stdout == 'source=true\n', 'Uncertain PR scope must run source checks'
        log = workspace / 'ci-diagnostics/failure.log'
        result = subprocess.run([sys.executable, str(workspace / 'scripts/ci-run.py'), '--log', str(log),
                                 '--', sys.executable, '-c', 'raise SystemExit(7)'], cwd=workspace, env=environment)
        assert result.returncode == 7
        assert json.loads(log.with_suffix('.log.jsonl').read_text().splitlines()[-1])['exit_code'] == 7
        environment.update(GITHUB_JOB='native', JOB_STATUS='failure')
        subprocess.run(['bash', '-c', shell('ci-diagnostics')], cwd=workspace, env=environment, check=True)
        assert (workspace / 'ci-diagnostics/native.txt').read_text() == 'job=native\nstatus=failure\n'
        assert log.exists(), 'Diagnostics must preserve the original failure log'
    print('Shared CI actions: caller root/cache identity/scope/exit code/failure diagnostics passed')


if __name__ == '__main__':
    main()
