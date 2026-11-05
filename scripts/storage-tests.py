# Managed by project-update.yml - Stage 3
"""Validate F1-F3 using Android app observations; F3 uses the actual system picker."""
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PKG_OWNER = 'org.example.securitylab.owner'
PKG_CLIENT = 'org.example.securitylab.client'
MARKER = 'ASL_STORAGE_RESULT:'
DOCUMENT = 'ASL_STAGE3_DOCUMENT.txt'
CONTENT = 'ASL_STAGE3_SAF_DOCUMENT'
API = subprocess.check_output(
    ['adb', 'shell', 'getprop', 'ro.build.version.sdk'], text=True
).strip()
OUT = Path('results') / f'stage1-api-{API}'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / 'report.json'
report = json.loads(REPORT.read_text(encoding='utf-8'))
records = []
f3_trace = []


def adb(*args, timeout=35):
    cmd = ['adb', *args]
    response = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if response.returncode:
        raise RuntimeError(
            f"{' '.join(cmd)}: {response.stderr.strip() or response.stdout.strip()}"
        )
    return response.stdout


def note(message):
    line = f'{time.strftime("%H:%M:%S")} {message}'
    f3_trace.append(line)
    print('F3:', line, flush=True)


def read_record(case):
    logs = adb('logcat', '-d', '-v', 'raw', '-s', 'SecurityLab:I', '*:S')
    for line in reversed(logs.splitlines()):
        if MARKER not in line:
            continue
        try:
            record = json.loads(line.split(MARKER, 1)[1])
        except ValueError:
            continue
        if record.get('id') == case:
            return record
    return None


def wait_record(case, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        record = read_record(case)
        if record is not None:
            return record
        time.sleep(0.6)
    raise RuntimeError(f'No application-side result for {case}')


def launch(component, case=None):
    adb('logcat', '-c')
    command = ['shell', 'am', 'start', '-W', '-n', component]
    if case:
        command += ['--es', 'experiment_id', case]
    adb(*command)


def failed(case, expected, exc):
    return {
        'id': case, 'expected': expected, 'observed': 'ERROR',
        'pass': False, 'detail': str(exc)[:450],
    }


def simple(case, component, expected):
    try:
        launch(component, case if case == 'F2' else None)
        record = wait_record(case)
        if record.get('expected') != expected or record.get('observed') != expected:
            record['pass'] = False
        return record
    except Exception as exc:
        return failed(case, expected, exc)


def screenshot(name):
    try:
        (OUT / name).write_bytes(
            subprocess.check_output(['adb', 'exec-out', 'screencap', '-p'], timeout=25)
        )
    except Exception as exc:
        note(f'Could not save screenshot {name}: {exc}')


def hierarchy():
    try:
        adb('shell', 'uiautomator', 'dump', '/sdcard/f3-window.xml', timeout=25)
        xml = adb('shell', 'cat', '/sdcard/f3-window.xml')
        (OUT / 'f3-ui.xml').write_text(xml, encoding='utf-8')
        return list(ET.fromstring(xml).iter('node'))
    except Exception as exc:
        note(f'UI hierarchy unavailable: {exc}')
        return []


def label(node):
    return ' '.join((node.get('text', ''), node.get('content-desc', ''))).strip()


def tap(node):
    nums = [int(n) for n in re.findall(r'\d+', node.get('bounds', ''))]
    if len(nums) != 4 or nums[2] <= nums[0] or nums[3] <= nums[1]:
        return False
    adb('shell', 'input', 'tap', str((nums[0] + nums[2]) // 2),
        str((nums[1] + nums[3]) // 2))
    return True


def choose(nodes, predicate):
    matches = [n for n in nodes if predicate(label(n).casefold())]
    matches.sort(key=lambda n: n.get('clickable') != 'true')
    return matches[0] if matches else None


def exact_document_node(nodes):
    """Select the document's filename, never a 'Preview the file ...' button.

    DocumentsUI can expose both a preview action and the filename. A fuzzy
    substring match accidentally clicks the preview, which opens Android's
    'Open with Chrome / HTML Viewer' chooser instead of returning the URI.
    """
    matches = [
        n for n in nodes
        if n.get('text', '').strip() == DOCUMENT
        or n.get('content-desc', '').strip() == DOCUMENT
    ]
    # Prefer the visible filename text. Its center is inside the document row.
    matches.sort(key=lambda n: n.get('text', '').strip() != DOCUMENT)
    return matches[0] if matches else None


def save_diagnostics():
    screenshot('f3-last-screen.png')
    try:
        (OUT / 'f3-logcat.txt').write_text(
            adb('logcat', '-d', '-v', 'time', '-t', '1000'), encoding='utf-8'
        )
        (OUT / 'f3-activity.txt').write_text(
            adb('shell', 'dumpsys', 'activity', 'activities'), encoding='utf-8'
        )
    except Exception as exc:
        note(f'Could not save all diagnostics: {exc}')
    (OUT / 'f3-debug.log').write_text('\n'.join(f3_trace) + '\n', encoding='utf-8')


def picker():
    case, expected = 'F3', 'ALLOW'
    try:
        local = OUT / DOCUMENT
        local.write_text(CONTENT, encoding='utf-8')
        adb('shell', 'mkdir', '-p', '/sdcard/Download')
        adb('push', str(local), f'/sdcard/Download/{DOCUMENT}')
        actual = adb('shell', 'cat', f'/sdcard/Download/{DOCUMENT}').strip()
        if actual != CONTENT:
            raise RuntimeError('Test document was not created correctly in Download')
        note('Test document verified at /sdcard/Download')
        launch(PKG_CLIENT + '/.StorageProbeActivity', case)
        note('ACTION_OPEN_DOCUMENT launched by client activity')

        attempted = set()
        clicked_file = False
        file_clicks = 0
        last_file_click = 0.0
        unexpected_chooser_count = 0
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            result = read_record(case)
            if result is not None:
                if result.get('expected') != expected or result.get('observed') != expected:
                    result['pass'] = False
                note('Received application-side F3 result')
                return result

            nodes = hierarchy()
            if not nodes:
                time.sleep(1)
                continue
            # Use the UI hierarchy rather than force-granting any URI.
            screen = ' | '.join(label(n) for n in nodes if label(n))
            fingerprint = screen[:1500]
            note('Picker items: ' + screen[:350])

            # 'Open with' is a viewer chooser, not an ACTION_OPEN_DOCUMENT result.
            # If it appears, the user-selection operation did not complete.
            if any(label(n).casefold() == 'open with' for n in nodes):
                screenshot('f3-unexpected-viewer.png')
                unexpected_chooser_count += 1
                note('Unexpected viewer chooser detected; returning to picker')
                if unexpected_chooser_count > 1:
                    raise RuntimeError(
                        'Android opened a viewer chooser instead of returning '
                        'the selected document URI; inspect f3-unexpected-viewer.png '
                        'and f3-ui.xml'
                    )
                adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
                last_file_click = 0.0
                clicked_file = False
                time.sleep(1)
                continue

            file_node = exact_document_node(nodes)
            now = time.monotonic()
            if file_node is not None and file_clicks < 2 and (
                not clicked_file or now - last_file_click > 12
            ):
                screenshot('f3-picker.png')
                if tap(file_node):
                    clicked_file = True
                    file_clicks += 1
                    last_file_click = now
                    note('Tapped exact filename node (excluded preview icon)')
                    time.sleep(2)
                    continue

            if clicked_file:
                # Some system pickers select a row first and then require Open.
                open_node = choose(nodes, lambda s: s in {
                    'open', 'select', 'choose', 'открыть', 'выбрать'
                })
                if open_node is not None and ('confirm', fingerprint) not in attempted:
                    attempted.add(('confirm', fingerprint))
                    if tap(open_node):
                        note('Tapped picker confirmation')
                        time.sleep(2)
                        continue

            downloads = choose(nodes, lambda s: s in {
                'downloads', 'download', 'загрузки'
            })
            if downloads is not None and ('downloads', fingerprint) not in attempted:
                attempted.add(('downloads', fingerprint))
                if tap(downloads):
                    note('Navigated to Downloads')
                    time.sleep(1.5)
                    continue

            roots = choose(nodes, lambda s: any(k in s for k in (
                'show roots', 'show navigation', 'open navigation',
                'navigation drawer', 'browse files', 'показать меню',
                'показать корни', 'обзор файлов'
            )))
            if roots is not None and ('roots', fingerprint) not in attempted:
                attempted.add(('roots', fingerprint))
                if tap(roots):
                    note('Opened navigation menu')
                    time.sleep(1.5)
                    continue

            browse = choose(nodes, lambda s: s in {'browse', 'обзор'})
            if browse is not None and ('browse', fingerprint) not in attempted:
                attempted.add(('browse', fingerprint))
                if tap(browse):
                    note('Opened Browse tab')
                    time.sleep(1.5)
                    continue

            search = choose(nodes, lambda s: s in {'search', 'поиск', 'search files'})
            if search is not None and ('search', fingerprint) not in attempted:
                attempted.add(('search', fingerprint))
                if tap(search):
                    note('Searching via system picker UI')
                    adb('shell', 'input', 'text', DOCUMENT)
                    adb('shell', 'input', 'keyevent', '66')
                    time.sleep(2)
                    continue

            time.sleep(1)

        raise RuntimeError(
            'No application-side result for F3 after picker UI automation; '
            'inspect f3-ui.xml, f3-last-screen.png, f3-debug.log'
        )
    except Exception as exc:
        note(f'F3 ERROR: {exc}')
        return failed(case, expected, exc)
    finally:
        save_diagnostics()


for case, component, expected in (
    ('F1', PKG_OWNER + '/.StorageProbeActivity', 'ALLOW'),
):
    result = simple(case, component, expected)
    records.append(result)
    print(json.dumps(result, ensure_ascii=False), flush=True)

if records[0].get('pass') is True:
    f2 = simple('F2', PKG_CLIENT + '/.StorageProbeActivity', 'DENY')
else:
    f2 = failed('F2', 'DENY', 'F1 positive control failed')
records.append(f2)
print(json.dumps(f2, ensure_ascii=False), flush=True)

f3 = picker()
records.append(f3)
print(json.dumps(f3, ensure_ascii=False), flush=True)

report['stage'] = 'sandbox_ipc_permissions_storage'
report['results'].extend(records)
all_ids = {f'S{i}' for i in range(1, 6)} | {f'P{i}' for i in range(1, 4)} | {f'F{i}' for i in range(1, 4)}
found = {x.get('id') for x in report['results'] if isinstance(x, dict)}
report['status'] = ('PASS' if all_ids.issubset(found)
                    and all(x.get('pass') is True for x in report['results'])
                    else 'FAIL')
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
if report['status'] != 'PASS':
    sys.exit('Storage experiments failed. Inspect F3 artifacts and report.json')
