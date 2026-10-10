#!/usr/bin/env python3
"""离线验证队列上限、run/SHA 身份、中断恢复与 HTTP 边界；不触发构建。"""
import copy
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('remote-verify.py')
spec = importlib.util.spec_from_file_location('remote_verify', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
SHA = 'a' * 40


class GitHub:
    def __init__(self, failure=None):
        self.runs = {}
        self.dispatched = []
        self.peak = 0
        self.failure = failure

    def api(self, endpoint, payload=None):
        component = endpoint.split('/')[2]
        if '/commits/' in endpoint:
            return {'sha': SHA}
        if endpoint.endswith('/dispatches'):
            inputs = {'warm_native_cache': False}
            if component not in verify.SPLIT_CI:
                inputs['version'] = ''
            assert payload == {'ref': 'main', 'inputs': inputs}
            self.dispatched.append(component)
            self.runs[component] = True
            self.peak = max(self.peak, sum(self.runs.values()))
            return {'workflow_run_id': len(self.dispatched)}
        if '/jobs?' in endpoint:
            return {'jobs': [{'name': name, 'conclusion': 'success', 'steps': []}
                             for name in verify.REQUIRED_JOBS]}
        if '/actions/runs/' in endpoint:
            self.runs[component] = False
            return {'head_sha': SHA, 'status': 'completed', 'event': 'workflow_dispatch',
                    'path': '.github/workflows/regression.yml', 'run_attempt': 1,
                    'conclusion': 'failure' if component == self.failure else 'success',
                    'updated_at': '2026-10-10T00:00:00Z'}
        return {'state': 'active', 'path': '.github/workflows/regression.yml'}


def batch(names, parallel=2):
    return {'schema': 1, 'status': 'running', 'parallel': parallel,
            'items': [{'component': name, 'ref': 'main', 'expected_sha': SHA,
                       'status': 'pending', 'run_id': None} for name in names]}


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        github = GitHub(failure='toast')
        value = batch(['toast', 'diagnostics', 'compose-webview'])
        report = root / 'results.json'
        with patch.object(verify, 'api', github.api), patch.object(verify.time, 'sleep'):
            assert verify.run_batch(value, report, 0) == 1
        assert github.peak == 2 and github.dispatched == ['toast', 'diagnostics', 'compose-webview']
        assert value['status'] == 'completed' and value['items'][2]['outcome'] == 'success'
        assert json.loads(report.read_text()) == value
        assert 'failure' in report.with_suffix('.md').read_text()

        github = GitHub()
        polls = {}
        def queued_api(endpoint, payload=None):
            if '/actions/runs/' in endpoint and '/jobs?' not in endpoint:
                component = endpoint.split('/')[2]
                polls[component] = polls.get(component, 0) + 1
                if polls[component] <= 2:
                    return {'head_sha': SHA, 'status': 'queued'}
            return github.api(endpoint, payload)
        value = batch(['toast', 'diagnostics', 'compose-webview'])
        with patch.object(verify, 'api', queued_api), patch.object(verify.time, 'sleep'):
            assert verify.run_batch(value, report, 0) == 0
        assert github.peak == 2 and all(count == 3 for count in polls.values()), 'queued runs must keep their slots'

        github = GitHub()
        value = batch(['toast', 'diagnostics', 'compose-webview'], parallel=1)
        with patch.object(verify, 'api', github.api), patch.object(verify.time, 'sleep'):
            assert verify.run_batch(value, report, 0) == 0 and github.peak == 1

        item = batch(['toast'])['items'][0]
        github = GitHub()
        with patch.object(verify, 'api', github.api):
            verify.dispatch(item)
        good = github.api('repos/gycrosskit/toast/actions/runs/1')
        good_jobs = github.api('repos/gycrosskit/toast/actions/runs/1/jobs?')
        for field, bad_value in [('head_sha', 'b' * 40), ('event', 'push'), ('path', '.github/workflows/other.yml')]:
            run = {**good, field: bad_value}
            probe = copy.deepcopy(item)
            with patch.object(verify, 'api', side_effect=[run, good_jobs]):
                verify.poll(probe)
            assert probe['outcome'] == 'identity_mismatch', field
        for jobs in [{'jobs': []}, {'jobs': [
            {**job, 'steps': [{'name': 'Explain lightweight completion', 'conclusion': 'success'}]}
            for job in good_jobs['jobs']]}]:
            probe = copy.deepcopy(item)
            with patch.object(verify, 'api', side_effect=[good, jobs]):
                verify.poll(probe)
            assert probe['outcome'] == 'incomplete'
        probe = copy.deepcopy(item)
        combined_jobs = {'jobs': good_jobs['jobs'] + [{'name': 'release-native', 'conclusion': 'success',
                        'steps': [{'name': 'Explain lightweight completion', 'conclusion': 'success'}]}]}
        with patch.object(verify, 'api', side_effect=[good, combined_jobs]):
            verify.poll(probe)
        assert probe['outcome'] == 'success', 'source mode intentionally leaves release jobs lightweight'
        with patch.object(verify, 'api', side_effect=[good, RuntimeError('read interrupted')]):
            try:
                verify.poll(item)
                assert False
            except RuntimeError:
                pass
        assert item['status'] == 'queued', 'job API error must leave the run resumable'
        class InterruptedJobs(list):
            def __iter__(self):
                raise KeyboardInterrupt
        probe = copy.deepcopy(item)
        with patch.object(verify, 'api', side_effect=[good, {'jobs': InterruptedJobs(good_jobs['jobs'])}]):
            try:
                verify.poll(probe)
                assert False
            except KeyboardInterrupt:
                pass
        assert probe['status'] == 'queued' and 'outcome' not in probe
        interrupt_line = next(number for number, line in enumerate(SCRIPT.read_text().splitlines(), 1)
                              if line.strip().startswith("if run['head_sha'] !="))
        def interrupt(frame, event, arg):
            if frame.f_code == verify.poll.__code__ and event == 'line' and frame.f_lineno == interrupt_line:
                raise KeyboardInterrupt
            return interrupt
        probe = copy.deepcopy(item)
        try:
            with patch.object(verify, 'api', side_effect=[good, good_jobs]):
                sys.settrace(interrupt)
                verify.poll(probe)
                assert False
        except KeyboardInterrupt:
            pass
        finally:
            sys.settrace(None)
        assert probe['status'] == 'queued' and 'outcome' not in probe, 'completion must be committed atomically'
        with patch.object(verify, 'api', return_value={'sha': 'b' * 40}) as api:
            probe = batch(['toast'])['items'][0]
            verify.dispatch(probe)
            assert probe['outcome'] == 'ref_changed' and api.call_count == 1

        # 恢复只读已有 run；读失败/不确定 POST 不允许占用被释放或自动重发。
        value = batch(['toast'])
        value['items'][0] = item
        with patch.object(verify, 'api', side_effect=[good, good_jobs]) as api, patch.object(verify.time, 'sleep'):
            assert verify.run_batch(value, report, 0) == 0
            assert all(call.args[0].find('/dispatches') == -1 for call in api.call_args_list)
        value['items'][0].update(status='dispatching', run_id=None)
        try:
            verify.validate_batch(value)
            assert False
        except RuntimeError as error:
            assert '不确定' in str(error)

        try:
            verify.validate_batch(batch(['toast', 'diagnostics', 'compose-webview'], parallel=3))
            assert False, 'resume must reject a batch exceeding the component limit'
        except RuntimeError:
            pass

        with patch.object(verify.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')) as execute:
            verify.api('repos/gycrosskit/toast/actions/workflows/regression.yml/dispatches', {'ref': 'main'})
            args, kwargs = execute.call_args
            assert '--hostname' in args[0] and 'github.com' in args[0] and 'X-GitHub-Api-Version: 2026-03-10' in args[0]
            assert '--input' in args[0] and json.loads(kwargs['input']) == {'ref': 'main'}
            assert not kwargs.get('shell')

        cache = root / 'cache'
        github = GitHub()
        with patch.object(verify, 'CACHE', cache), patch.object(verify, 'api', github.api):
            assert verify.main(['--all', '--dry-run', '--output', str(root / 'plan')]) == 0
            assert len(json.loads((root / 'plan/results.json').read_text())['items']) == 14
            assert json.loads((root / 'plan/results.json').read_text())['parallel'] == 2
            assert not github.dispatched and not (cache / 'active-batch').exists()
            with (cache / 'batch.lock').open('a') as held, patch.object(verify, 'plan') as plan:
                verify.fcntl.flock(held, verify.fcntl.LOCK_EX)
                try:
                    verify.main(['toast'])
                    assert False, 'a second local batch must be refused before planning'
                except RuntimeError as error:
                    assert '已有' in str(error)
                plan.assert_not_called()
            for args in [['--parallel', '0', 'toast'], ['--parallel', '3', '--all'], ['unknown'], ['toast', 'toast'], ['--all', 'toast']]:
                try:
                    verify.main(args)
                    assert False, args
                except SystemExit as error:
                    assert error.code == 2
            incomplete = root / 'interrupted.json'
            value = batch(['toast'])
            incomplete.write_text(json.dumps(value))
            (cache / 'active-batch').write_text(str(incomplete))
            with patch.object(verify, 'plan') as plan:
                try:
                    verify.main(['toast'])
                    assert False
                except RuntimeError as error:
                    assert '--resume' in str(error)
                plan.assert_not_called()
            original_write = Path.write_text
            def interrupted_write(path, text, *args, **kwargs):
                if path.name == 'active-batch.tmp':
                    original_write(path, text[:3])
                    raise KeyboardInterrupt
                return original_write(path, text, *args, **kwargs)
            with patch.object(Path, 'write_text', interrupted_write):
                try:
                    verify.main(['--resume', str(incomplete)])
                    assert False
                except KeyboardInterrupt:
                    pass
            assert (cache / 'active-batch').read_text() == str(incomplete)
            assert not github.dispatched, 'interrupted registry write must not dispatch'
            with patch.object(verify.time, 'sleep'):
                assert verify.main(['--resume', str(incomplete)]) == 0
            assert github.dispatched == ['toast']
            assert not (cache / 'active-batch').exists(), 'completed reports must not block future batches'


if __name__ == '__main__':
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        main()
    print('remote-verify: queue, identity, evidence, resume, interruption, API and CLI checks passed')
