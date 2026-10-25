#!/usr/bin/env python3
"""Governance entry uses the existing fixed-CI template, not a second scheduler."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENTRY = Path(__file__).with_name('remote-verify.py')


class FixedCIEntryTest(unittest.TestCase):
    def test_unbound_entry_fails_before_git_or_network(self):
        result = subprocess.run([sys.executable, '-B', str(ENTRY), '--list'], env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('独立可信 CI 检出', result.stderr)

    def test_exact_template_delegates_and_rejects_wrong_sha_or_dirty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()/'ci'
            root.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, env={'PATH': '/usr/bin:/bin', 'HOME': directory, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull, 'PYTHONDONTWRITEBYTECODE': '1'})
            git('init', '-q'); git('config', 'user.name', 'fixture'); git('config', 'user.email', 'fixture@example.invalid')
            (root/'jenkins').mkdir(); (root/'jenkins/component_remote_verify.py').write_text('# offline fixture\n')
            (root/'ci.py').write_text('import json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            git('add', '.'); git('commit', '-qm', 'fixed fixture')
            sha = git('rev-parse', 'HEAD').decode().strip()
            env = {'PATH': '/usr/bin:/bin', 'GYC_COMPONENT_CI_ROOT': str(root), 'GYC_COMPONENT_CI_COMMIT': sha, 'PYTHONDONTWRITEBYTECODE': '1'}
            args = ['toast', '--parallel', '2', '--output', '/private/state.json', '--resume', '--recover-build', 'toast=5']
            def run():
                return subprocess.run([sys.executable, '-B', str(ENTRY), *args], env=env, capture_output=True, text=True, cwd='/')
            result = run(); self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(['component', *args], json.loads(result.stdout))
            env['GYC_COMPONENT_CI_COMMIT'] = 'f'*40
            self.assertNotEqual(0, run().returncode)
            env['GYC_COMPONENT_CI_COMMIT'] = sha
            (root/'untracked').write_text('dirty')
            self.assertNotEqual(0, run().returncode)
            (root/'untracked').unlink()
            git('update-index', '--assume-unchanged', 'ci.py')
            self.assertNotEqual(0, run().returncode)
            git('update-index', '--no-assume-unchanged', 'ci.py')
            git('update-index', '--skip-worktree', 'ci.py')
            self.assertNotEqual(0, run().returncode)
            git('update-index', '--no-skip-worktree', 'ci.py')
            git('config', 'filter.fixture.clean', '/usr/bin/false')
            self.assertNotEqual(0, run().returncode)
            git('config', '--unset', 'filter.fixture.clean')
            link = root.parent/'linked-ci'; link.symlink_to(root, target_is_directory=True)
            env['GYC_COMPONENT_CI_ROOT'] = str(link)
            self.assertNotEqual(0, run().returncode)
            env['GYC_COMPONENT_CI_ROOT'] = str(root)
            for name in ('commondir', 'config.worktree', 'objects/info/alternates'):
                forbidden = root/'.git'/name
                forbidden.parent.mkdir(parents=True, exist_ok=True)
                forbidden.write_text('fixture-only external path')
                self.assertNotEqual(0, run().returncode, name)
                forbidden.unlink()
            git('update-index', '--add', '--cacheinfo', '160000,'+sha+',fixture-module')
            self.assertNotEqual(0, run().returncode)
            git('update-index', '--force-remove', 'fixture-module')
            original_blob = git('hash-object', 'ci.py').decode().strip()
            replacement_source = root.parent/'replacement.py'; replacement_source.write_text('untrusted replacement tree\n')
            replacement_blob = git('hash-object', '-w', str(replacement_source)).decode().strip()
            git('update-index', '--cacheinfo', '100644,'+replacement_blob+',ci.py')
            replacement_tree = git('write-tree').decode().strip()
            git('update-index', '--cacheinfo', '100644,'+original_blob+',ci.py')
            replacement_commit = git('commit-tree', replacement_tree, '-m', 'fixture replacement').decode().strip()
            git('replace', sha, replacement_commit)
            self.assertTrue(git('status', '--porcelain'))
            self.assertEqual(0, run().returncode)  # The trusted entry disables replacement objects.
            git('replace', '-d', sha)
            external = root.parent/'external.config'; external.write_text('[fixture]\nvalue = external\n')
            git('config', 'include.path', str(external))
            self.assertNotEqual(0, run().returncode)
            git('config', '--no-includes', '--unset', 'include.path')
            # A .git file is the worktree form; never weaken the independent-checkout rule.
            saved_git = root.parent/'saved-git'; (root/'.git').rename(saved_git)
            (root/'.git').write_text('gitdir: '+str(saved_git)+'\n')
            self.assertNotEqual(0, run().returncode)
            (root/'.git').unlink(); saved_git.rename(root/'.git')
            self.assertEqual(0, run().returncode)
            git('rm', '-q', 'jenkins/component_remote_verify.py')
            git('commit', '-qm', 'fixture missing required entry')
            env['GYC_COMPONENT_CI_COMMIT'] = git('rev-parse', 'HEAD').decode().strip()
            self.assertNotEqual(0, run().returncode)


if __name__ == '__main__':
    unittest.main()
