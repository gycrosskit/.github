#!/usr/bin/env python3
"""离线验证范围判断、真实子进程退出/下载停滞，以及纯文档PR的Git范围。"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'templates' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    changes, runner = load('ci-changes'), load('ci-run')
    assert changes.source_needed('pull_request', {}, ['README.md', 'docs/接入.md']) is False
    for path in ['scripts/ci-release.sh', '.github/workflows/regression.yml', 'gradle/libs.versions.toml',
                 'tests/fixtures/README.md', 'verification/build.gradle.kts', 'docs/probe.py', '.agents/skills/probe.py', 'unknown']:
        assert changes.source_needed('pull_request', {}, [path]), path
    assert changes.source_needed('pull_request', {}, None)
    assert not changes.source_needed('push', {})
    assert not changes.source_needed('release', {})
    assert changes.source_needed('workflow_dispatch', {'inputs': {}})
    assert not changes.source_needed('workflow_dispatch', {'inputs': {'version': '0.1.0'}})
    for value in (True, 'true'):
        assert not changes.source_needed('workflow_dispatch', {'inputs': {'warm_native_cache': value}})
    for value in (False, 'false'):
        assert changes.source_needed('workflow_dispatch', {'inputs': {'warm_native_cache': value}})
    assert changes.source_needed('unknown', {})
    progress = runner.Downloads()
    line = 'Downloading dependency for Kotlin Native: https://example.test/llvm.tar.gz (%d/100).'
    progress.observe(line % 10, 0)
    progress.observe(line % 10, 4)
    assert progress.stalled(5, 5)
    progress.observe(line % 20, 5)
    assert not progress.stalled(6, 5)
    progress.observe(line % 100, 7)
    assert not progress.stalled(100, 5)
    progress.observe(line % 10, 101)
    progress.observe('> Task :core:compileKotlinIosArm64', 102)
    assert not progress.stalled(200, 5)

    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        previous = Path.cwd()
        try:
            os.chdir(directory)
            module = directory / 'ohos/example-native'
            module.mkdir(parents=True)
            (module / 'oh-package.json5').write_text('{}')
            for name in ('README.md', 'CHANGELOG.md'):
                assert not changes.source_needed('pull_request', {}, [f'ohos/example-native/{name}'])
            for path in ('ohos/unknown/README.md', 'ohos/example-native/test/README.md',
                         'ohos/example-native/oh-package.json5', 'ohos/example-native/src/Main.ets'):
                assert changes.source_needed('pull_request', {}, [path]), path
            assert changes.source_needed('pull_request', {}, ['ohos/example-native/README.md', 'new.kt'])
        finally:
            os.chdir(previous)
        wrapper = ROOT / 'templates/ci-run.py'
        def execute(name, source, timeout=0.3):
            log = directory / (name + '.log')
            result = subprocess.run([sys.executable, str(wrapper), '--log', str(log),
                                     '--no-progress-seconds', str(timeout), '--', sys.executable, '-u', '-c', source],
                                    capture_output=True, timeout=8)
            return result, json.loads(log.with_suffix('.log.jsonl').read_text().splitlines()[-1]), log.read_text()
        result, receipt, log = execute('exit', 'print("test failure"); raise SystemExit(7)')
        assert result.returncode == 7 and receipt['exit_code'] == 7 and 'test failure' in log
        result, receipt, log = execute('quiet', 'import time; time.sleep(0.6); print("compiled")')
        assert result.returncode == 0 and not receipt['download_stall']
        result, receipt, log = execute('stalled', 'import time; print(' + repr(line % 10) + '); time.sleep(4)')
        assert result.returncode == 124 and receipt['download_stall'] and not receipt['automatic_build_retry']
        execute('repeated', 'print("one")')
        execute('repeated', 'print("two")')
        receipts = [json.loads(item) for item in (directory / 'repeated.log.jsonl').read_text().splitlines()]
        assert len(receipts) == 2 and 'one' in receipts[0]['command'][-1] and 'two' in receipts[1]['command'][-1]
        descendant_pid = directory / 'descendant.pid'
        child = '''import os, signal, time
pid = os.fork()
if pid == 0:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    open(%r, 'w').write(str(os.getpid()))
    while True: time.sleep(1)
while not os.path.exists(%r): time.sleep(0.01)
print(%r, flush=True)
while True: time.sleep(1)
''' % (str(descendant_pid), str(descendant_pid), line % 10)
        try:
            result, receipt, log = execute('descendant', child)
            assert result.returncode == 124
            pid = int(descendant_pid.read_text())
            status = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
            assert not status or status.startswith('Z'), ('Descendant still alive', pid, status)
        finally:
            if descendant_pid.exists():
                try:
                    os.kill(int(descendant_pid.read_text()), 9)
                except ProcessLookupError:
                    pass
        git = lambda *args: subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()
        git('init', '-q')
        git('config', 'user.name', 'CI helper test')
        git('config', 'user.email', 'ci-test@example.invalid')
        (directory / 'README.md').write_text('old')
        git('add', 'README.md'); git('commit', '-qm', 'baseline')
        base = git('rev-parse', 'HEAD')
        (directory / 'README.md').write_text('new')
        git('add', 'README.md'); git('commit', '-qm', 'documentation')
        event = directory / 'event.json'
        event.write_text(json.dumps({'pull_request': {'base': {'sha': base}, 'head': {'sha': git('rev-parse', 'HEAD')}}}))
        output = directory / 'output'
        environment = dict(os.environ, GITHUB_EVENT_NAME='pull_request', GITHUB_EVENT_PATH=str(event), GITHUB_OUTPUT=str(output))
        result = subprocess.run([sys.executable, str(ROOT / 'templates/ci-changes.py')], cwd=directory,
                                env=environment, capture_output=True, text=True, check=True)
        assert result.stdout == 'source=false\n' and output.read_text() == 'source=false\n'
        for ref, inputs in [('refs/heads/feature', {'warm_native_cache': True}),
                            ('refs/heads/main', {'warm_native_cache': True, 'version': '1.0.0'})]:
            event.write_text(json.dumps({'inputs': inputs}))
            environment.update(GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_REF=ref)
            result = subprocess.run([sys.executable, str(ROOT / 'templates/ci-changes.py')], cwd=directory,
                                    env=environment, capture_output=True, text=True)
            assert result.returncode != 0 and 'requires main' in result.stderr
    print('CI helpers: scope/Git diff/exit propagation/quiet compile/download stall checks passed')


if __name__ == '__main__':
    main()
