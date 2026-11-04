#!/usr/bin/env bash
# Managed by project-update.yml - Stage 2

set -euo pipefail

# Execute existing Sandbox and IPC tests (S1-S5).
bash scripts/run-stage1.sh

# Execute Runtime Permissions tests (P1-P3).
python3 - <<'PY_PERMISSIONS'
import json
import re
import subprocess
import sys
import time
from pathlib import Path

pkg = 'org.example.securitylab.client'
perm = 'android.permission.CAMERA'

api = subprocess.check_output(
    [
        'adb',
        'shell',
        'getprop',
        'ro.build.version.sdk'
    ],
    text=True
).strip()

folder = Path('results') / f'stage1-api-{api}'
report_path = folder / 'report.json'

report = json.loads(
    report_path.read_text(encoding='utf-8')
)

observations = []
all_logs = []

def adb(*arguments, timeout=35):
    command = ['adb', *arguments]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode:
        raise RuntimeError(
            f'{" ".join(command)}: '
            f'{result.stderr.strip() or result.stdout.strip()}'
        )

    return result.stdout

def check(test_id, operation):
    expected = (
        'ALLOW' if test_id == 'P2' else 'DENY'
    )

    try:
        # Stop the previous application process.
        adb(
            'shell',
            'am',
            'force-stop',
            pkg
        )

        # Prepare permission state.
        adb(
            'shell',
            'pm',
            operation,
            pkg,
            perm
        )

        # Clear logs before this experiment.
        adb('logcat', '-c')

        # Start the permission probe.
        adb(
            'shell',
            'am',
            'start',
            '-W',
            '-n',
            f'{pkg}/.PermissionProbeActivity',
            '--es',
            'experiment_id',
            test_id
        )

        found = None
        last_log = ''

        for _ in range(30):
            last_log = adb(
                'logcat',
                '-d',
                '-v',
                'raw',
                '-s',
                'SecurityLab:I',
                '*:S'
            )

            for line in last_log.splitlines():
                match = re.search(
                    r'ASL_PERMISSION_RESULT:(\{.*\})',
                    line
                )

                if not match:
                    continue

                candidate = json.loads(
                    match.group(1)
                )

                if candidate.get('id') == test_id:
                    found = candidate
                    break

            if found is not None:
                break

            time.sleep(1)

        all_logs.append(
            f'=== {test_id} ===\n{last_log}'
        )

        if found is None:
            raise RuntimeError(
                'No application result received'
            )

        if found.get('expected') != expected:
            raise RuntimeError(
                'Inconsistent expected result'
            )

        return found

    except Exception as exc:
        return {
            'id': test_id,
            'expected': expected,
            'observed': 'ERROR',
            'pass': False,
            'detail': str(exc)[:500]
        }

scenarios = [
    ('P1', 'revoke'),
    ('P2', 'grant'),
    ('P3', 'revoke')
]

for test_id, operation in scenarios:
    result = check(test_id, operation)

    observations.append(result)

    print(
        json.dumps(
            result,
            ensure_ascii=False
        )
    )

(folder / 'permission-logcat.txt').write_text(
    '\n\n'.join(all_logs) + '\n',
    encoding='utf-8'
)

report['stage'] = (
    'sandbox_ipc_runtime_permissions'
)

report['permissions_control_method'] = (
    'ADB pm grant/revoke; '
    'checkSelfPermission inside application'
)

report['results'].extend(observations)

report['status'] = (
    'PASS'
    if report.get('status') == 'PASS'
    and all(
        r.get('pass') is True
        for r in observations
    )
    else 'FAIL'
)

report_path.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ) + '\n',
    encoding='utf-8'
)

if report['status'] != 'PASS':
    sys.exit(
        'Stage 2 checks failed. '
        'Inspect report.json.'
    )

PY_PERMISSIONS
