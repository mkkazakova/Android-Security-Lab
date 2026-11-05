# ASL_VISUAL_EVIDENCE_V1
"""Capture actual emulator UI, not generated/mock screenshots.
Only record app displays after confirming a matching Android-side Logcat observation.
"""
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

OWNER = 'org.example.securitylab.owner'
CLIENT = 'org.example.securitylab.client'
PERM = 'android.permission.CAMERA'
API = subprocess.check_output(
    ['adb','shell','getprop','ro.build.version.sdk'], text=True
).strip()
OUT = Path('results') / f'stage1-api-{API}'
REPORT = json.loads((OUT / 'report.json').read_text(encoding='utf-8'))
EXPECTED = {r['id']: r for r in REPORT.get('results', [])}
LOG = []


def adb(*args, timeout=35, check=True):
    result = subprocess.run(['adb', *args], text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'adb {" ".join(args)}: {result.stderr or result.stdout}')
    return result.stdout


def screenshot(name):
    path = OUT / name
    proc = subprocess.run(['adb','exec-out','screencap','-p'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
    if proc.returncode or not proc.stdout.startswith(b'\x89PNG\r\n\x1a\n'):
        raise RuntimeError(f'No valid screencap for {name}: {proc.stderr[:200]!r}')
    path.write_bytes(proc.stdout)
    LOG.append(f'SAVED {name} ({len(proc.stdout)} bytes)')
    return path


def dump_ui():
    # Pull actual system UI hierarchy for validation of screenshots.
    adb('shell','uiautomator','dump','/sdcard/asl_visual.xml', timeout=30)
    return adb('exec-out','cat','/sdcard/asl_visual.xml', timeout=15)


def click_demo(test_id, package, activity, marker, operation=None):
    if operation:
        adb('shell','pm',operation,package,PERM)
    adb('shell','am','force-stop',package)
    adb('logcat','-c')
    adb('shell','am','start','-W','-n',f'{package}/{activity}',
        '--es','experiment_id',test_id)
    record = None
    for _ in range(30):
        lines = adb('logcat','-d','-v','raw','-s','SecurityLab:I','*:S')
        for line in reversed(lines.splitlines()):
            if marker in line:
                try:
                    candidate = json.loads(line.split(marker,1)[1])
                except json.JSONDecodeError:
                    continue
                if candidate.get('id') == test_id:
                    record = candidate
                    break
        if record is not None:
            break
        time.sleep(0.5)
    if not record or not record.get('pass'):
        raise RuntimeError(f'No PASS from actual Android Activity for {test_id}')
    expected = EXPECTED.get(test_id)
    if not expected or expected.get('observed') != record.get('observed'):
        raise RuntimeError(f'Live observation differs from report for {test_id}')
    time.sleep(0.6)
    screenshot(f'evidence-{test_id.lower()}.png')


def capture_launcher():
    # Both apps have a MAIN/LAUNCHER Activity. Capture the actual app drawer.
    size = adb('shell','wm','size')
    dims = re.findall(r'(\d+)x(\d+)', size)
    if not dims:
        raise RuntimeError(f'Unable to determine emulator display size: {size}')
    width, height = [int(x) for x in dims[-1]]
    mid = width // 2
    adb('shell','input','keyevent','KEYCODE_HOME')
    time.sleep(1.3)
    for attempt in range(12):
        if attempt == 0:
            adb('shell','input','swipe',str(mid),str(int(height*.82)),
                str(mid),str(int(height*.27)),'480')
        else:
            adb('shell','input','swipe',str(mid),str(int(height*.77)),
                str(mid),str(int(height*.45)),'400')
        time.sleep(0.9)
        xml = dump_ui()
        if 'SecurityOwner' in xml and 'SecurityClient' in xml:
            (OUT / 'installed-apps-ui.xml').write_text(xml, encoding='utf-8')
            screenshot('installed-apps.png')
            return
    (OUT / 'installed-apps-ui.xml').write_text(xml, encoding='utf-8')
    raise RuntimeError('Launcher drawer did not show both app labels; no evidence screenshot is claimed')


def camera_dialog():
    adb('shell','pm','revoke',CLIENT,PERM)
    adb('shell','pm','clear-permission-flags',CLIENT,PERM,'user-set','user-fixed', check=False)
    adb('shell','am','force-stop',CLIENT)
    adb('shell','am','start','-W','-n',f'{CLIENT}/.PermissionDialogDemoActivity')
    time.sleep(1.3)
    xml = dump_ui()
    (OUT / 'camera-permission-ui.xml').write_text(xml, encoding='utf-8')
    # Verify a real OS permission controller dialog rather than the app's own UI.
    if 'permissioncontroller' not in xml.lower() and 'permission_allow' not in xml.lower():
        raise RuntimeError('System permission dialog not detected in UI hierarchy')
    screenshot('camera-permission-dialog.png')
    adb('shell','input','keyevent','KEYCODE_BACK',check=False)


if REPORT.get('status') != 'PASS' or len(EXPECTED) != 14:
    raise SystemExit('Capture requires a complete successful run of 14 experiments')

# Screenshots are optional evidence, never substitute for the actual 14 assertions.
for label, operation in [
    ('installed apps', capture_launcher),
    ('system CAMERA dialog', camera_dialog),
]:
    try:
        operation()
        LOG.append(f'OK {label}')
    except Exception as exc:
        LOG.append(f'WARNING {label}: {exc}')
        print(f'WARNING visual capture: {label}: {exc}', flush=True)

for test_id, package, activity, marker, operation in [
    ('P1', CLIENT,'.PermissionProbeActivity','ASL_PERMISSION_RESULT:', 'revoke'),
    ('P2', CLIENT,'.PermissionProbeActivity','ASL_PERMISSION_RESULT:', 'grant'),
    ('P3', CLIENT,'.PermissionProbeActivity','ASL_PERMISSION_RESULT:', 'revoke'),
    ('F1', OWNER,'.StorageProbeActivity','ASL_STORAGE_RESULT:', None),
    ('F2', CLIENT,'.StorageProbeActivity','ASL_STORAGE_RESULT:', None),
    ('K1', OWNER,'.KeystoreProbeActivity','ASL_KEYSTORE_RESULT:', None),
    ('K2', OWNER,'.KeystoreProbeActivity','ASL_KEYSTORE_RESULT:', None),
    ('K3', CLIENT,'.KeystoreProbeActivity','ASL_KEYSTORE_RESULT:', None),
]:
    try:
        click_demo(test_id,package,activity,marker,operation)
    except Exception as exc:
        LOG.append(f'WARNING evidence {test_id}: {exc}')
        print(f'WARNING {test_id}: {exc}', flush=True)

(OUT / 'visual-evidence-log.txt').write_text('\n'.join(LOG)+'\n', encoding='utf-8')
print('Visual evidence summary:\n'+'\n'.join(LOG), flush=True)
