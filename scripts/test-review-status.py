#!/usr/bin/env python3
"""固定模板翻译与评论同步的离线回归；不会调用 GitHub。"""
import ast
import copy
import io
import json
import os
from pathlib import Path
import re
import tempfile
import textwrap
import unittest
from unittest.mock import patch


WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/review-status-zh.yml'
WORKFLOW_TEXT = WORKFLOW.read_text()
SOURCE = textwrap.dedent(WORKFLOW_TEXT.split('        run: |\n', 1)[1]).split("python3 - <<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
TREE = ast.parse(SOURCE)
NAMESPACE = {}
exec(compile(ast.Module(body=[n for n in TREE.body if isinstance(n, (ast.Import, ast.FunctionDef))], type_ignores=[]), '<translation>', 'exec'), NAMESPACE)
TRANSLATE = NAMESPACE['translate']
BOT = {'id': 199175422, 'login': 'chatgpt-codex-connector[bot]', 'type': 'Bot'}
SUMMARY = '''<!-- codex-pull-request-review-summary -->
## Codex Review Summary
This comment shows the latest Codex review activity on this pull request.
| Review | Status | Commit | Review trigger |
| **Code Review** | **Completed** <relative-time datetime="2026-10-09T08:35:31.239709Z">2026-10-09T08:35:31.239709Z</relative-time> | `oldcommit` | Manual request |
'''


class ReusableWorkflowTest(unittest.TestCase):
    def test_no_checkout_and_caller_context_with_minimum_permissions(self):
        self.assertIn('on:\n  workflow_call:\n', WORKFLOW_TEXT)
        self.assertIn('permissions:\n  pull-requests: write\n', WORKFLOW_TEXT)
        self.assertNotIn('uses:', WORKFLOW_TEXT)
        self.assertNotIn('secrets:', WORKFLOW_TEXT)
        self.assertIn('GH_TOKEN: ${{ github.token }}', WORKFLOW_TEXT)
        self.assertIn("os.environ['GITHUB_REPOSITORY']", SOURCE)
        self.assertIn("os.environ['GITHUB_EVENT_PATH']", SOURCE)
        self.assertIn('group: review-status-zh-${{ github.repository }}-${{ github.event.comment.id }}', WORKFLOW_TEXT)
        self.assertIn('cancel-in-progress: false', WORKFLOW_TEXT)
        for gate in ["github.event_name == 'issue_comment'", 'github.event.issue.pull_request',
                     'github.event.comment.user.id == 199175422',
                     "github.event.comment.user.login == 'chatgpt-codex-connector[bot]'",
                     "github.event.comment.user.type == 'Bot'"]:
            self.assertIn(gate, WORKFLOW_TEXT)

    def test_thin_consumer_wrapper_and_shared_pr_regression(self):
        root = WORKFLOW.parents[2]
        wrapper = (root / 'templates/review-status-zh.yml').read_text()
        self.assertIn('on:\n  issue_comment:\n    types: [created, edited]\n', wrapper)
        self.assertIn('permissions:\n  pull-requests: write\n', wrapper)
        calls = re.findall(r'^    uses: (.+)$', wrapper, re.MULTILINE)
        self.assertEqual(len(calls), 1)
        self.assertRegex(calls[0], r'\Agycrosskit/\.github/\.github/workflows/review-status-zh\.yml@[0-9a-f]{40}\Z')
        for forbidden in ['run:', 'steps:', 'secrets:', 'checkout', 'pull_request:', '@codex']:
            self.assertNotIn(forbidden, wrapper)
        regression = (WORKFLOW.parent / 'template-regression.yml').read_text()
        self.assertIn('  pull_request:\n', regression)
        self.assertIn('python3 scripts/test-review-status.py', regression)


class TranslationTest(unittest.TestCase):
    def test_status_time_commit_and_idempotence(self):
        result = TRANSLATE(SUMMARY)
        self.assertIn('## 评审结果', result)
        self.assertIn('**已完成**', result)
        self.assertIn('2026-10-09 16:35:31（北京时间）', result)
        self.assertIn('`oldcommit`', result)
        self.assertEqual(TRANSLATE(result), result)
        self.assertIn('**审查中**，开始于', TRANSLATE(SUMMARY.replace('**Completed**', '**Running** since')))

    def test_no_findings_and_preserved_actual_findings(self):
        source = "Codex Review: Didn't find any major issues. Keep it up!\n**Reviewed commit:** `abc123`"
        self.assertEqual(TRANSLATE(source), '评审结果：本次未发现重大问题。\n**已审查提交：** `abc123`')
        finding = 'Codex Review: Here are some suggestions.\n[P1] Keep this original finding\n`someApi()`'
        self.assertEqual(TRANSLATE(finding), finding)
        self.assertEqual(TRANSLATE('@codex review'), '@codex review')
        unmarked = SUMMARY.replace('<!-- codex-pull-request-review-summary -->', '<!-- other -->')
        self.assertEqual(TRANSLATE(unmarked), unmarked)

    def test_fixed_help_text_removes_bot_triggers(self):
        source = SUMMARY + '''- Comment "@codex review" or "@codex security review".
Codex can also answer questions or update the PR. Try commenting "@codex address that feedback".
'''
        self.assertNotIn('@codex', TRANSLATE(source))


class CommentSyncTest(unittest.TestCase):
    def setUp(self):
        self.repository = 'gycrosskit/scanner'
        self.source_url = f'https://api.github.com/repos/{self.repository}/issues/comments/123'
        self.comments_url = f'https://api.github.com/repos/{self.repository}/issues/34/comments'
        self.source = {'id': 123, 'node_id': 'SOURCE', 'user': BOT, 'body': SUMMARY, 'html_url': f'https://github.com/{self.repository}/pull/34#issuecomment-123'}
        self.mirrors = []
        self.writes = []
        self.advance_after_get = False
        self.second_page = False

    def open(self, request, timeout):
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-only-token')
        self.assertEqual(timeout, 30)
        method = request.get_method()
        if method == 'GET' and request.full_url == self.source_url:
            data = copy.deepcopy(self.source)
            if self.advance_after_get:
                self.source['body'] = SUMMARY.replace('oldcommit', 'newcommit')
                self.advance_after_get = False
        elif method == 'GET' and request.full_url.startswith(self.comments_url):
            if self.second_page and 'page=2' not in request.full_url:
                return self.response([], {'Link': f'<{self.comments_url}?per_page=100&page=2>; rel="next"'})
            data = self.mirrors
        else:
            payload = json.loads(request.data)
            self.writes.append((method, request.full_url, payload))
            if request.full_url == 'https://api.github.com/graphql':
                self.assertEqual(payload['variables'], {'id': 'SOURCE'})
                data = {'data': {'minimizeComment': {'minimizedComment': {'isMinimized': True}}}}
            elif method == 'POST' and request.full_url == self.comments_url:
                data = {'id': 456, 'url': self.comments_url + '/456', 'user': {'login': 'github-actions[bot]', 'type': 'Bot'}, **payload}
                self.mirrors.append(data)
            elif method == 'PATCH' and request.full_url == self.comments_url + '/456':
                self.mirrors[-1].update(payload)
                data = self.mirrors[-1]
            else:
                self.fail(f'不应写入原始评论：{method} {request.full_url}')
        return self.response(data)

    @staticmethod
    def response(data, headers=None):
        stream = io.BytesIO(json.dumps(data).encode())
        stream.headers = headers or {}
        return stream

    def run_sync(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / 'event.json'
            event.write_text(json.dumps({'comment': {'id': 123}, 'issue': {'comments_url': self.comments_url}}))
            with patch.dict(os.environ, {'GITHUB_EVENT_PATH': str(event), 'GITHUB_REPOSITORY': self.repository, 'GH_TOKEN': 'test-only-token'}), patch('urllib.request.urlopen', self.open), patch('sys.stdout', io.StringIO()):
                exec(compile(SOURCE, '<workflow>', 'exec'), {})

    def test_concurrent_source_update_is_not_overwritten(self):
        self.advance_after_get = True
        self.run_sync()
        self.assertIn('newcommit', self.source['body'])
        self.assertIn('oldcommit', self.mirrors[-1]['body'])
        self.run_sync()
        self.assertIn('newcommit', self.mirrors[-1]['body'])
        self.assertEqual(len(self.mirrors), 1)
        self.assertTrue(all(url != self.source_url for _, url, _ in self.writes))
        self.assertNotIn('@codex', self.mirrors[-1]['body'])

    def test_repeated_event_and_paginated_mirror_do_not_duplicate(self):
        self.run_sync()
        self.second_page = True
        self.run_sync()
        self.assertEqual(len(self.mirrors), 1)
        self.assertEqual(sum(method == 'POST' and url == self.comments_url for method, url, _ in self.writes), 1)

    def test_wrong_author_and_unrelated_body_are_not_written(self):
        for key, value in [('id', 1), ('login', 'human'), ('type', 'User')]:
            with self.subTest(key=key):
                self.source['user'] = {**BOT, key: value}
                with self.assertRaises(AssertionError):
                    self.run_sync()
        self.assertEqual(self.writes, [])
        self.source['user'] = BOT
        self.source['body'] = 'Codex Review: Here are some suggestions.\n[P1] Real issue'
        with self.assertRaises(SystemExit) as result:
            self.run_sync()
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(self.writes, [])

    def test_unknown_bot_trigger_is_rejected_before_publishing(self):
        self.source['body'] = SUMMARY + '\n@codex unknown new trigger'
        with self.assertRaises(AssertionError):
            self.run_sync()
        self.assertEqual(self.writes, [])


if __name__ == '__main__':
    unittest.main()
