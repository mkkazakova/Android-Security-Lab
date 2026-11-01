#!/usr/bin/env bash
set -euo pipefail
API="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
OUT="results/stage1-api-${API}"
mkdir -p "$OUT"
adb install -r owner/build/outputs/apk/debug/owner-debug.apk
adb install -r client/build/outputs/apk/debug/client-debug.apk
adb logcat -c
adb shell am start -W -n org.example.securitylab.owner/.OwnerActivity
sleep 3
adb exec-out screencap -p > "$OUT/owner.png"
# run-as is used ONLY as a host-side fixture check. It is NOT the client access test.
adb shell run-as org.example.securitylab.owner cat files/secret.txt > "$OUT/fixture.txt"
adb shell am start -W -n org.example.securitylab.client/.ClientActivity
for attempt in $(seq 1 50); do
  if adb logcat -d -v raw -s SecurityLab:I '*:S' | grep 'ASL_RESULT:.*"id":"S5"' >/dev/null; then
    break
  fi
  sleep 2
done
sleep 2
adb exec-out screencap -p > "$OUT/client.png"
adb logcat -d -v raw -s SecurityLab:I '*:S' > "$OUT/lab-logcat.txt"
export OUT API
python3 - <<'PY_RESULTS'
import json, os, re, sys
from pathlib import Path
out = Path(os.environ['OUT'])
text = (out / 'lab-logcat.txt').read_text(encoding='utf-8', errors='replace')
records = {}
for line in text.splitlines():
    found = re.search(r'ASL_RESULT:(\{.*\})', line)
    if not found:
        continue
    try:
        obj = json.loads(found.group(1))
    except json.JSONDecodeError:
        continue
    if obj.get('id') in {'S1', 'S2', 'S3', 'S4', 'S5'}:
        records[obj['id']] = obj
fixture = (out / 'fixture.txt').read_text(encoding='utf-8', errors='replace').strip()
fixture_ok = fixture == 'LAB_SAMPLE_NO_PERSONAL_DATA'
valid = all(key in records for key in ('S1', 'S2', 'S3', 'S4', 'S5'))
# A negative result is only meaningful after the fixture and exported positive control passed.
if not fixture_ok or records.get('S4', {}).get('pass') is not True:
    for key in ('S2', 'S3', 'S5'):
        if key in records:
            records[key]['pass'] = False
            records[key]['detail'] += '; positive control or test fixture unavailable'
statuses = [records.get(f'S{i}', {}).get('pass') is True for i in range(1, 6)]
status = 'PASS' if valid and fixture_ok and all(statuses) else 'FAIL'
report = {
    'stage': 'sandbox_ipc',
    'api': int(os.environ['API']),
    'android_release': os.popen('adb shell getprop ro.build.version.release').read().strip(),
    'target_sdk': 33,
    'fixture_verified_from_owner_identity': fixture_ok,
    'status': status,
    'results': [records.get(f'S{i}', {'id':f'S{i}','pass':False,'observed':'MISSING'}) for i in range(1,6)]
}
(out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
if status != 'PASS':
    sys.exit('Some Stage-1 checks failed or were inconclusive; see report.json')
PY_RESULTS
