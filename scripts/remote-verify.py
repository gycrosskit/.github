#!/usr/bin/env python3
"""固定 CI 独立检出中的唯一 Jenkins 入口；不实现第二套执行器。"""
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


def require(ok):
    if not ok:
        raise ValueError('可信 CI 路径、配置或固定 SHA 检出不符')


try:
    root = Path(os.environ.get('GYC_COMPONENT_CI_ROOT', '')).expanduser()
    sha = os.environ.get('GYC_COMPONENT_CI_COMMIT', '')
    require(root.is_absolute() and root == root.resolve() and re.fullmatch(r'[0-9a-f]{40}', sha)
            and not any(path.is_symlink() for path in (root, *root.parents)))
    git_dir, config = root / '.git', root / '.git/config'
    require(git_dir.is_dir() and not git_dir.is_symlink())
    info = config.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 1024 ** 2)
    require(not any((git_dir / name).exists() or (git_dir / name).is_symlink()
                    for name in ('commondir', 'config.worktree', 'objects/info/alternates')))
    with tempfile.TemporaryDirectory(prefix='component-entry-home-') as temporary:
        environment = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if key in os.environ}
        environment.update(HOME=temporary, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
            GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1', GIT_GRAFT_FILE=os.devnull,
            GIT_CEILING_DIRECTORIES=str(Path(temporary).resolve()))
        def git(*arguments, cwd=root):
            result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
                '-c', 'credential.helper=', '-C', str(cwd), *arguments], env=environment,
                capture_output=True, timeout=30)
            require(result.returncode == 0 and len(result.stdout) <= 1024 ** 2)
            return result.stdout
        keys = git('config', '--no-includes', '--file', str(config), '--null', '--name-only', '--list', cwd=temporary).decode().split('\0')
        require(not any(key == 'include.path' or key.startswith('includeif.')
                or re.fullmatch(r'filter\..*\.(clean|process)', key) for key in keys))
        require(git('rev-parse', '--show-toplevel').decode().strip() == str(root)
                and git('rev-parse', '--verify', 'HEAD').decode().strip() == sha)
        require(all(item.startswith(b'H ') for item in git('ls-files', '-v', '-z').split(b'\0') if item))
        require(not any(item.startswith(b'160000 ') for item in git('ls-files', '--stage', '-z').split(b'\0')))
        require(not git('status', '--porcelain', '--untracked-files=normal'))
        git('ls-files', '--error-unmatch', '--', 'ci.py', 'jenkins/component_remote_verify.py')
except (ValueError, OSError, subprocess.SubprocessError):
    raise SystemExit('请配置无外部 Git 配置、无未提交改动的独立可信 CI 检出及完整固定 SHA')

os.execv(sys.executable, [sys.executable, str(root / 'ci.py'), 'component', *sys.argv[1:]])
