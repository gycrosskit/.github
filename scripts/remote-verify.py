#!/usr/bin/env python3
"""通过现有 GitHub Actions 验证远程源码；本机只调用 gh API、等待并保存回执。"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote

COMPONENTS = (
    'compose-webview', 'live-sdk', 'toast', 'location', 'media', 'scanner',
    'permission', 'system-actions', 'sound', 'diagnostics', 'jverification',
    'wechat', 'debug-tools', 'customer-service',
)
WORKFLOW = 'regression.yml'
CACHE = Path.home() / '.cache/gycrosskit/remote-validation'
REQUIRED_JOBS = {'changes', 'contracts', 'android', 'native'}
SPLIT_CI = {'compose-webview', 'live-sdk', 'jverification', 'wechat', 'debug-tools', 'customer-service'}


def api(endpoint, payload=None):
    command = ['gh', 'api', '--hostname', 'github.com', endpoint,
               '-H', 'Accept: application/vnd.github+json',
               '-H', 'X-GitHub-Api-Version: 2026-03-10']
    if payload is not None:
        command += ['--method', 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, timeout=60,
                            env={**os.environ, 'GH_PROMPT_DISABLED': '1'})
    if result.returncode:
        raise RuntimeError(f'{endpoint}: {result.stderr.strip()}')
    return json.loads(result.stdout)


def endpoint(item):
    return 'repos/gycrosskit/' + item['component']


def plan(components, ref):
    items = []
    for component in components:
        item = {'component': component, 'ref': ref, 'status': 'pending', 'run_id': None}
        base = endpoint(item)
        workflow = api(f'{base}/actions/workflows/{WORKFLOW}')
        if workflow['state'] != 'active' or workflow['path'] != '.github/workflows/' + WORKFLOW:
            raise RuntimeError(f'{component}: regression workflow 未启用或路径不符')
        item['expected_sha'] = api(f'{base}/commits/{quote(ref, safe="")}')['sha']
        items.append(item)
    return items


def markdown(value):
    return re.sub(r'[\x00-\x1f\x7f]', ' ', str(value)).replace('|', '\\|')


def save(batch, report):
    temporary = report.with_suffix('.tmp')
    temporary.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(report)
    lines = ['# 远程源码验证', '',
             f'批次状态：{batch["status"]}；最大并发组件：{batch["parallel"]}。', '',
             '仅验证记录的远程 commit；不包含本地未提交文件、发布消费者或真机验收。', '',
             '| 组件 | 预期 SHA | 实际 SHA | 状态 | 结果 | Actions |',
             '| --- | --- | --- | --- | --- | --- |']
    for item in batch['items']:
        link = f'[run {item["run_id"]}]({item["url"]})' if item.get('url') else '—'
        cells = [item['component'], item['expected_sha'], item.get('actual_sha', '—'),
                 item['status'], item.get('outcome', '—'), link]
        lines.append('| ' + ' | '.join(markdown(cell) for cell in cells) + ' |')
    for item in batch['items']:
        failed = [job for job in item.get('jobs', []) if job['conclusion'] not in ('success', 'skipped')]
        if item.get('error') or failed:
            lines += ['', f'## {item["component"]}', '']
            if item.get('error'):
                lines.append(markdown(item['error']))
            for job in failed:
                steps = [step['name'] for step in job['steps'] if step['conclusion'] == 'failure']
                lines.append(f'- {markdown(job["name"])}: {markdown(job["conclusion"])}; '
                             + markdown(', '.join(steps)))
    report.with_suffix('.md').write_text('\n'.join(lines) + '\n')


def dispatch(item):
    base = endpoint(item)
    # 分支可移动，触发前复核、触发后验实际 SHA；不把新提交算作原计划的通过。
    sha = api(f'{base}/commits/{quote(item["ref"], safe="")}')['sha']
    if sha != item['expected_sha']:
        item.update(status='completed', outcome='ref_changed', error='远程 ref 已移动，请重新规划')
        return
    inputs = {'warm_native_cache': False}
    if item['component'] not in SPLIT_CI:
        inputs['version'] = ''
    result = api(f'{base}/actions/workflows/{WORKFLOW}/dispatches', {'ref': item['ref'], 'inputs': inputs})
    run_id = result.get('workflow_run_id')
    if type(run_id) is not int or run_id <= 0:
        raise RuntimeError('dispatch 未返回明确 run ID；不要重试 POST，请到 Actions 确认运行')
    item.update(run_id=run_id, url=f'https://github.com/gycrosskit/{item["component"]}/actions/runs/{run_id}',
                status='queued')


def poll(item):
    base = endpoint(item)
    run = api(f'{base}/actions/runs/{item["run_id"]}')
    if run['status'] != 'completed':
        item.update(actual_sha=run['head_sha'], status=run['status'])
        return
    jobs = []
    page = 1
    while True:
        entries = api(f'{base}/actions/runs/{item["run_id"]}/jobs?filter=latest&per_page=100&page={page}')['jobs']
        jobs.extend({'name': job['name'], 'conclusion': job['conclusion'],
                     'steps': [{'name': step['name'], 'conclusion': step['conclusion']} for step in job.get('steps', [])]}
                    for job in entries)
        if len(entries) < 100:
            break
        page += 1
    result = dict(actual_sha=run['head_sha'], status=run['status'], jobs=jobs,
                  conclusion=run['conclusion'], run_attempt=run['run_attempt'],
                  started_at=run.get('run_started_at'), updated_at=run['updated_at'])
    if run['head_sha'] != item['expected_sha'] or run['event'] != 'workflow_dispatch' or run['path'].split('@')[0] != '.github/workflows/' + WORKFLOW:
        result.update(outcome='identity_mismatch', error='实际 commit、事件或 workflow 与计划不符')
    elif run['conclusion'] != 'success':
        result['outcome'] = run['conclusion'] or 'unknown'
    elif not REQUIRED_JOBS.issubset({job['name'] for job in jobs if job['conclusion'] == 'success'}):
        result.update(outcome='incomplete', error='缺少成功的 changes/contracts/android/native job')
    elif any(step['name'] == 'Explain lightweight completion' and step['conclusion'] == 'success'
             for job in jobs if job['name'] in REQUIRED_JOBS for step in job['steps']):
        result.update(outcome='incomplete', error='发现轻量完成，不能算完整源码验证')
    else:
        result['outcome'] = 'success'
    item.update(result)


def run_batch(batch, report, poll_seconds):
    while True:
        active = [item for item in batch['items'] if item['run_id'] and item['status'] != 'completed']
        for item in active:
            previous = item['status']
            poll(item)
            save(batch, report)
            if item['status'] != previous:
                print(f'{item["component"]}: {item["status"]} {item.get("outcome", "")} {item["url"]}', flush=True)
        active = [item for item in batch['items'] if item['run_id'] and item['status'] != 'completed']
        pending = [item for item in batch['items'] if item['status'] == 'pending']
        for item in pending[:max(0, batch['parallel'] - len(active))]:
            # 先落盘。网络超时可能发生在 GitHub 接受 POST 后，恢复时禁止自动重复触发。
            item['status'] = 'dispatching'
            save(batch, report)
            dispatch(item)
            save(batch, report)
            print(f'{item["component"]}: {item["status"]} {item.get("url", item.get("error", ""))}', flush=True)
        if all(item['status'] == 'completed' for item in batch['items']):
            batch['status'] = 'completed'
            save(batch, report)
            return 0 if all(item['outcome'] == 'success' for item in batch['items']) else 1
        time.sleep(poll_seconds)


def validate_batch(batch):
    if batch.get('schema') != 1 or not 1 <= batch['parallel'] <= 2 or not batch['items']:
        raise RuntimeError('批次回执格式不符')
    names = [item['component'] for item in batch['items']]
    if len(names) != len(set(names)) or not set(names).issubset(COMPONENTS):
        raise RuntimeError('批次含未知或重复组件')
    for item in batch['items']:
        if not re.fullmatch(r'[0-9a-f]{40}', item['expected_sha']) or not isinstance(item['ref'], str) or not item['ref']:
            raise RuntimeError('批次 commit/ref 不符')
        if item['run_id'] is not None and (type(item['run_id']) is not int or item['run_id'] <= 0):
            raise RuntimeError('批次 run ID 不符')
        if item['run_id']:
            item['url'] = f'https://github.com/gycrosskit/{item["component"]}/actions/runs/{item["run_id"]}'
        if item['status'] == 'dispatching' or (item['status'] not in ('pending', 'completed') and not item['run_id']):
            raise RuntimeError(f'{item["component"]}: 触发结果不确定，先到 Actions 确认 run ID 并补入回执；不可重发')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('components', nargs='*', help='组件名，见 --list')
    parser.add_argument('--all', action='store_true', help='选择全部 14 个组件')
    parser.add_argument('--list', action='store_true', help='仅列出组件，不联网')
    parser.add_argument('--ref', default='main', help='已存在的远程分支或 tag，默认 main')
    parser.add_argument('--parallel', type=int, choices=(1, 2), default=2, help='最多同时运行的组件数，默认 2，上限 2')
    parser.add_argument('--dry-run', action='store_true', help='读取 workflow/ref 并保存计划，不触发')
    parser.add_argument('--output', type=Path, help='新建结果目录，默认 ~/.cache/gycrosskit/remote-validation/<批次>')
    parser.add_argument('--resume', type=Path, help='继续已有 results.json，不重复触发已记录运行')
    parser.add_argument('--poll-seconds', type=int, default=30)
    args = parser.parse_args(argv)
    if args.list:
        print('\n'.join(COMPONENTS))
        return 0
    if args.poll_seconds < 5:
        parser.error('--poll-seconds 至少 5')
    if args.resume and (args.components or args.all or args.output or args.dry_run):
        parser.error('--resume 不与组件选择、--output 或 --dry-run 混用')
    if not args.resume and (args.all == bool(args.components) or len(set(args.components)) != len(args.components)):
        parser.error('指定组件列表或 --all，且不要重复组件')
    if not set(args.components).issubset(COMPONENTS):
        parser.error('未知组件：' + ', '.join(sorted(set(args.components) - set(COMPONENTS))))
    CACHE.mkdir(parents=True, exist_ok=True)
    marker = CACHE / 'active-batch'
    with (CACHE / 'batch.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('本机已有统一验证批次运行；等待该批次完成')
        if marker.exists() and not args.dry_run:
            previous = Path(marker.read_text().strip()).resolve()
            if not previous.exists():
                raise RuntimeError(f'未完成回执缺失：{previous}，先恢复该文件，不要重复触发')
            prior = json.loads(previous.read_text())
            if prior['status'] != 'completed' and (not args.resume or args.resume.resolve() != previous):
                raise RuntimeError(f'存在未完成批次，请使用 --resume {previous}')
        if args.resume:
            report = args.resume.resolve()
            batch = json.loads(report.read_text())
            validate_batch(batch)
            if batch['status'] == 'planned':
                raise RuntimeError('dry-run 计划不能恢复；请重新选择组件执行')
        else:
            batch = {'schema': 1, 'status': 'planned' if args.dry_run else 'running',
                     'parallel': args.parallel, 'items': plan(list(COMPONENTS) if args.all else args.components, args.ref)}
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
            directory = (args.output or CACHE / stamp).resolve()
            directory.mkdir(parents=True, exist_ok=False)
            report = directory / 'results.json'
        save(batch, report)
        print(f'回执：{report}', flush=True)
        if args.dry_run:
            for item in batch['items']:
                print(f'{item["component"]}: {item["ref"]} {item["expected_sha"]} {WORKFLOW}')
            return 0
        marker_temp = marker.with_suffix('.tmp')
        marker_temp.write_text(str(report) + '\n')
        marker_temp.replace(marker)
        try:
            batch['status'] = 'running'
            result = run_batch(batch, report, args.poll_seconds)
            marker.unlink()
            return result
        except (Exception, KeyboardInterrupt):
            batch['status'] = 'interrupted'
            save(batch, report)
            print(f'未自动取消远程运行。继续跟踪：python3 {Path(__file__).resolve()} --resume {report}', file=sys.stderr)
            raise


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as error:
        print('本机轮询已中断，远程运行继续。' if isinstance(error, KeyboardInterrupt) else f'错误：{error}', file=sys.stderr)
        sys.exit(130 if isinstance(error, KeyboardInterrupt) else 1)
