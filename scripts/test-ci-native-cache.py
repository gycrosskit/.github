#!/usr/bin/env python3
"""离线验证缓存身份、版本漂移、最小探针与可信 main 入口。"""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_cache', ROOT / 'templates/ci-native-cache.py')
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / 'gradle').mkdir()
        config = root / 'gradle/native-toolchain.properties'
        config.write_text('kotlin=2.2.21-1.0.0\ntargets=ios_arm64,ios_x64,ios_simulator_arm64,ohos_arm64\nrevision=1\n')
        build = root / 'build.gradle.kts'
        build.write_text('plugins { kotlin("multiplatform") version "2.2.21-1.0.0" }')
        key = cache.cache_key(root, 'Xcode 26 build A')
        (root / 'README.md').write_text('documentation changed')
        build.write_text(build.read_text() + '\nversion = "0.1.99"')
        assert cache.cache_key(root, 'Xcode 26 build A') == key
        assert cache.cache_key(root, 'Xcode 26 build B') != key
        with patch.object(cache.platform, 'machine', return_value='other-cpu'):
            assert cache.cache_key(root, 'Xcode 26 build A') != key
        config.write_text(config.read_text().replace('revision=1', 'revision=2'))
        assert cache.cache_key(root, 'Xcode 26 build A') != key

        def build_probe(command, **kwargs):
            probe = Path(command[command.index('-p') + 1])
            text = (probe / 'build.gradle.kts').read_text()
            settings = (probe / 'settings.gradle.kts').read_text()
            assert 'dependencyResolutionManagement { repositories {' in settings
            assert settings.count('mavenCentral()') == 2
            assert 'ohosArm64().binaries.sharedLib()' in text and 'iosX64().binaries.framework()' in text
            assert (probe / 'src/commonMain/kotlin/Warmup.kt').read_text().endswith('42\n')
            assert 'linkDebugSharedOhosArm64' in command and kwargs['check'] is True
            assert kwargs['cwd'] == root and 'includeBuild' not in text

        with patch.dict(os.environ, GITHUB_ACTIONS='true', GITHUB_REF='refs/heads/main',
                        GITHUB_EVENT_NAME='workflow_dispatch'), patch.object(cache.subprocess, 'run', side_effect=build_probe) as run:
            cache.warm(root)
            assert run.call_count == 1
        with patch.dict(os.environ, GITHUB_ACTIONS='true', GITHUB_REF='refs/pull/1/merge',
                        GITHUB_EVENT_NAME='pull_request'), patch.object(cache.subprocess, 'run') as run:
            try:
                cache.warm(root)
                raise AssertionError('PR warmup was accepted')
            except ValueError as error:
                assert 'explicit main' in str(error)
            run.assert_not_called()
        build.write_text(build.read_text().replace('2.2.21-1.0.0', '2.2.22-1.0.0'))
        try:
            cache.cache_key(root, 'Xcode 26')
            raise AssertionError('Compiler drift was accepted')
        except ValueError as error:
            assert 'differs from project' in str(error)
    print('Native cache: identity/stable inputs/compiler drift/probe/trusted main checks passed')


if __name__ == '__main__':
    main()
