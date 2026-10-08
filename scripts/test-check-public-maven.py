#!/usr/bin/env python3
"""无需网络/Gradle的最小回归：摘要、身份、snapshot、exact inventory 与完整 Mock HTTP 检查。"""
import hashlib
import importlib.util
import io
import json
import ssl
import tempfile
import urllib.error
from unittest.mock import patch
import zipfile
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'templates' / 'check-public-maven.py'
spec = importlib.util.spec_from_file_location('public_checker', path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def rejects(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError('Expected checker to reject invalid evidence')


def main():
    version, commit = '0.1.0-rc.1', 'a' * 40
    group, repo, module = 'com.github.gycrosskit.example', 'example', 'example-core'
    state = {'status': 'ok', 'isTag': True, 'private': False, 'version': version, 'commit': commit, 'modules': [module]}
    checker.validate_state(state, version, commit, [module])
    for update in ({'isTag': False}, {'private': True}, {'commit': 'b' * 40}, {'modules': [module, module]}):
        rejects(lambda update=update: checker.validate_state(dict(state, **update), version, commit, [module]))
    snapshot = dict(state, version='main-SNAPSHOT')
    rejects(lambda: checker.validate_state(snapshot, 'main-SNAPSHOT', commit, [module]))
    checker.validate_component({'group': group, 'module': module, 'version': version}, group, module, repo, version)
    checker.validate_component({'group': 'com.github.gycrosskit', 'module': repo, 'version': version}, group, module, repo, version)
    # 合法 JitPack 变换必须成对；不能把旧来源 group 与任意 publication 混在一起。
    rejects(lambda: checker.validate_component({'group': 'com.github.gycrosskit', 'module': module, 'version': version}, group, module, repo, version))
    rejects(lambda: checker.validate_component({'group': group, 'module': repo, 'version': version}, group, module, repo, version))
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED) as packed:
        packed.writestr('sample.txt', 'valid')
    data = archive.getvalue()
    item = {'name': module + '-' + version + '.jar', 'url': module + '-' + version + '.jar', 'size': len(data)}
    item.update({algorithm: hashlib.new(algorithm, data).hexdigest() for algorithm in checker.HASHES})
    checker.validate_file(item, data, 'https://example.test/artifact')
    rejects(lambda: checker.validate_file(dict(item, sha256='0' * 64), data, 'https://example.test/artifact'))
    damaged = bytearray(data)
    damaged[data.index(b'valid')] ^= 1
    corrupted_item = dict(item, **{algorithm: hashlib.new(algorithm, damaged).hexdigest() for algorithm in checker.HASHES})
    rejects(lambda: checker.validate_file(corrupted_item, bytes(damaged), 'https://example.test/artifact'))
    base = 'https://jitpack.io/' + group.replace('.', '/') + '/' + module + '/' + version + '/'
    prefix = base + module + '-' + version
    metadata = {'component': {'group': group, 'module': module, 'version': version},
                'variants': [{'name': 'metadataApiElements', 'files': [item]}]}
    pom = f'''<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>{group}</groupId><artifactId>{module}</artifactId><version>{version}</version><licenses><license><name>Apache License, Version 2.0</name><url>https://www.apache.org/licenses/LICENSE-2.0.txt</url><distribution>repo</distribution></license></licenses></project>'''.encode()
    responses = {'https://jitpack.io/api/builds/com.github.gycrosskit/' + repo + '/' + version: json.dumps(state).encode(),
                 prefix + '.module': json.dumps(metadata).encode(), prefix + '.pom': pom, base + item['name']: data}
    for url, content in list(responses.items()):
        if '/api/builds/' not in url:
            for algorithm in ('md5', 'sha1'):
                responses[url + '.' + algorithm] = hashlib.new(algorithm, content).hexdigest().encode()

    def fetch(url):
        if url in responses:
            return responses[url]
        raise urllib.error.HTTPError(url, 404, 'Missing', {}, None)

    with tempfile.TemporaryDirectory() as directory:
        proof = checker.audit(repo, version, commit, [module], Path(directory) / 'good', fetch=fetch)
        assert proof['moduleCount'] == 1 and proof['uniqueFileCount'] == 1
        assert not proof['publicHigherSidecarsComplete']
        assert len(proof['missingPublicHigherSidecars']) == 3
        assert all(result['verified'] == ['md5', 'sha1'] for result in proof['modules'][0]['sidecars'])
        responses[base + item['name'] + '.sha1'] = b'0' * 40
        rejects(lambda: checker.audit(repo, version, commit, [module], Path(directory) / 'bad-digest', fetch=fetch))
        assert not (Path(directory) / 'bad-digest' / 'proof.json').exists()
        failed_state = dict(state, isTag=False)
        responses[next(url for url in responses if '/api/builds/' in url)] = json.dumps(failed_state).encode()
        failed = Path(directory) / 'bad-state'
        rejects(lambda: checker.audit(repo, version, commit, [module], failed, fetch=fetch))
        assert json.loads((failed / 'jitpack-state-001.json').read_text()) == failed_state
        assert not (failed / 'proof.json').exists()

    class Response(io.BytesIO):
        def __init__(self, content, length=None):
            super().__init__(content)
            self.headers = {'Content-Length': str(len(content) if length is None else length)}

    transient = urllib.error.HTTPError('https://example.test', 503, 'Unavailable', {}, None)
    with patch.object(checker.urllib.request, 'urlopen', side_effect=[transient, Response(b'ok')]) as opening, \
            patch.object(checker.time, 'sleep'):
        assert checker.get_bytes('https://example.test') == b'ok' and opening.call_count == 2
    missing = urllib.error.HTTPError('https://example.test', 404, 'Missing', {}, None)
    with patch.object(checker.urllib.request, 'urlopen', side_effect=missing) as opening:
        try:
            checker.get_bytes('https://example.test')
            raise AssertionError('404 must fail')
        except urllib.error.HTTPError:
            assert opening.call_count == 1
    with patch.object(checker.urllib.request, 'urlopen', side_effect=[Response(b'bad', 5), Response(b'valid')]) as opening, \
            patch.object(checker.time, 'sleep'):
        assert checker.get_bytes('https://example.test') == b'valid' and opening.call_count == 2
    broken = Response(b'')
    broken.read1 = lambda size: (_ for _ in ()).throw(ssl.SSLEOFError('EOF during body read'))
    with patch.object(checker.urllib.request, 'urlopen', side_effect=[broken, Response(b'valid')]) as opening, \
            patch.object(checker.time, 'sleep'):
        assert checker.get_bytes('https://example.test') == b'valid' and opening.call_count == 2
    for certificate in [ssl.SSLCertVerificationError('untrusted'), urllib.error.URLError(ssl.SSLCertVerificationError('untrusted'))]:
        with patch.object(checker.urllib.request, 'urlopen', side_effect=certificate) as opening:
            try:
                checker.get_bytes('https://example.test')
                raise AssertionError('Certificate failure must stop')
            except (ssl.SSLCertVerificationError, urllib.error.URLError):
                assert opening.call_count == 1

    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary)
        clock = [0]
        def sleep(seconds):
            clock[0] += seconds
        states = iter([dict(state, status='building'), state])
        with patch.object(checker.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(checker.time, 'sleep', side_effect=sleep):
            ready = checker.ready_state('https://example.test', version, commit, [module], output,
                                        lambda url: json.dumps(next(states)).encode(), wait_seconds=2, poll_seconds=1)
        assert ready == state and json.loads((output / 'jitpack-state-001.json').read_text())['status'] == 'building'
        assert (output / 'jitpack-state-002.json').exists()
    for bad in [dict(state, status='error'), dict(state, commit='b' * 40)]:
        with tempfile.TemporaryDirectory() as temporary:
            calls = []
            def bad_fetch(url):
                calls.append(url)
                return json.dumps(bad).encode()
            rejects(lambda: checker.ready_state('https://example.test', version, commit, [module], Path(temporary),
                                                bad_fetch, wait_seconds=300))
            assert len(calls) == 1
    with tempfile.TemporaryDirectory() as temporary:
        states = iter([dict(state, status='none'), state])
        calls = []
        def bootstrap_fetch(url):
            calls.append(url)
            return b'<project/>' if url.endswith('.pom') else json.dumps(next(states)).encode()
        with patch.object(checker.time, 'sleep'):
            assert checker.ready_state('https://example.test/state', version, commit, [module], Path(temporary),
                                       bootstrap_fetch, wait_seconds=2, bootstrap_url='https://example.test/exact.pom') == state
        assert calls == ['https://example.test/state', 'https://example.test/exact.pom', 'https://example.test/state']
        assert json.loads((Path(temporary) / 'jitpack-trigger.json').read_text())['received_bytes'] == 10
    with tempfile.TemporaryDirectory() as temporary:
        clock, calls = [0], []
        def waiting(url):
            calls.append(url)
            return json.dumps(dict(state, status='none')).encode()
        with patch.object(checker.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(checker.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            rejects(lambda: checker.ready_state('https://example.test', version, commit, [module], Path(temporary),
                                                waiting, wait_seconds=2, poll_seconds=1))
        assert len(calls) == 3 and clock[0] == 2
    print('public Maven checker: state/identity/digest/ZIP CRC/mock HTTP/sidecar absence checks passed')


if __name__ == '__main__':
    main()
