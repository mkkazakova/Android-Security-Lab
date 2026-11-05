# Managed by project-update.yml - Stage 4 Android Keystore
"""K1-K3: app-observed Android Keystore experiments with an owner control."""
import json
import subprocess
import sys
import time
from pathlib import Path

OWNER = 'org.example.securitylab.owner'
CLIENT = 'org.example.securitylab.client'
MARKER = 'ASL_KEYSTORE_RESULT:'
API = subprocess.check_output(
    ['adb', 'shell', 'getprop', 'ro.build.version.sdk'], text=True
).strip()
OUT = Path('results') / f'stage1-api-{API}'
REPORT = OUT / 'report.json'
report = json.loads(REPORT.read_text(encoding='utf-8'))
records = []
evidence = []


def adb(*args, timeout=35):
    cmd = ['adb', *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(
            f'{" ".join(cmd)}: {result.stderr.strip() or result.stdout.strip()}'
        )
    return result.stdout


def collect_record(test_id, seconds=20):
    deadline = time.monotonic() + seconds
    last = ''
    while time.monotonic() < deadline:
        last = adb('logcat', '-d', '-v', 'raw', '-s', 'SecurityLab:I', '*:S')
        for line in reversed(last.splitlines()):
            if MARKER not in line:
                continue
            try:
                record = json.loads(line.split(MARKER, 1)[1])
            except json.JSONDecodeError:
                continue
            if record.get('id') == test_id:
                evidence.append(f'{test_id}\n{last}\n')
                return record
        time.sleep(0.5)
    evidence.append(f'{test_id}: timeout\n{last}\n')
    raise RuntimeError(f'No app-side result for {test_id}')


def run(test_id, package, expected):
    try:
        adb('shell', 'am', 'force-stop', package)
        adb('logcat', '-c')
        adb(
            'shell', 'am', 'start', '-W', '-n', f'{package}/.KeystoreProbeActivity',
            '--es', 'experiment_id', test_id
        )
        record = collect_record(test_id)
        if record.get('expected') != expected or record.get('observed') != expected:
            record['pass'] = False
        if record.get('pass') is not True:
            record['pass'] = False
        return record
    except Exception as exc:
        return {
            'id': test_id,
            'expected': expected,
            'observed': 'ERROR',
            'pass': False,
            'detail': str(exc)[:450],
        }


def print_record(record):
    print(json.dumps(record, ensure_ascii=False), flush=True)


try:
    k1 = run('K1', OWNER, 'ALLOW')
    records.append(k1)
    print_record(k1)

    if k1['pass']:
        k2 = run('K2', OWNER, 'DENY')
    else:
        k2 = {
            'id': 'K2', 'expected': 'DENY', 'observed': 'ERROR',
            'pass': False, 'detail': 'K1 positive control failed',
        }
    records.append(k2)
    print_record(k2)

    if k1['pass']:
        k3 = run('K3', CLIENT, 'DENY')
        control = run('K3_CONTROL', OWNER, 'ALLOW')
        evidence.append('K3_OWNER_CONTROL ' + json.dumps(control, ensure_ascii=False))
        if not control.get('pass'):
            k3['pass'] = False
            k3['detail'] = str(k3.get('detail', '')) + \
                '; owner alias positive control failed: ' + str(control.get('detail', ''))
        else:
            k3['detail'] = str(k3.get('detail', '')) + \
                '; owner alias remains accessible (positive control)'
    else:
        k3 = {
            'id': 'K3', 'expected': 'DENY', 'observed': 'ERROR',
            'pass': False, 'detail': 'Owner alias not verified by K1',
        }
    records.append(k3)
    print_record(k3)
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'keystore-logcat.txt').write_text(
        '\n\n'.join(evidence) + '\n', encoding='utf-8'
    )

report['stage'] = 'sandbox_ipc_permissions_storage_keystore'
report['results'].extend(records)
expected_ids = {
    *(f'S{i}' for i in range(1, 6)),
    *(f'P{i}' for i in range(1, 4)),
    *(f'F{i}' for i in range(1, 4)),
    *(f'K{i}' for i in range(1, 4)),
}
seen_ids = {x.get('id') for x in report['results'] if isinstance(x, dict)}
report['status'] = (
    'PASS' if expected_ids.issubset(seen_ids)
    and len(seen_ids & expected_ids) == len(expected_ids)
    and all(x.get('pass') is True for x in report['results'])
    else 'FAIL'
)
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
if report['status'] != 'PASS':
    sys.exit('Android Keystore experiment failed; inspect K1-K3 and keystore-logcat.txt')
