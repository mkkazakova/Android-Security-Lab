# Managed by project-update.yml - report generator shared across stages.
"""Publish only observed CI results, preserving non-managed README sections."""
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

START = '<!-- ANDROID_STAGE1_START -->'
END = '<!-- ANDROID_STAGE1_END -->'
README = Path('README.md')
CATALOG = json.loads(Path('experiments/catalog.json').read_text(encoding='utf-8'))
TESTS = CATALOG['experiments']
IMAGES = Path('docs/screenshots')
IMAGES.mkdir(parents=True, exist_ok=True)
RESULTS = Path('results')
RESULTS.mkdir(parents=True, exist_ok=True)
reports = {}
screenshots = {}


# ASL_FINAL_PUBLISH_GUARD: do not replace successful evidence on an incomplete run.
for _api in (33, 36):
    _p = Path('downloaded') / f'securitylab-api-{_api}' / 'report.json'
    if not _p.is_file():
        raise SystemExit(f'Missing current test report: {_p}. Keeping last successful snapshot.')
    _data = json.loads(_p.read_text(encoding='utf-8'))
    _items = _data.get('results', [])
    _ids = [r.get('id') for r in _items if isinstance(r, dict)]
    _expected = [t['id'] for t in TESTS]
    if (int(_data.get('api', -1)) != _api or _data.get('status') != 'PASS'
            or _ids != _expected or int(_data.get('target_sdk', -1)) != 33
            or not all(r.get('pass') is True and r.get('observed') == r.get('expected') for r in _items)):
        raise SystemExit(f'Incomplete/failed current report for API {_api}. Keeping last successful snapshot.')

for api, version in ((33, '13'), (36, '16')):
    folder = Path('downloaded') / f'securitylab-api-{api}'
    try:
        data = json.loads((folder / 'report.json').read_text(encoding='utf-8'))
        if not isinstance(data, dict) or int(data.get('api', -1)) != api:
            raise ValueError('Wrong or absent API level in report')
        reports[api] = data
        (RESULTS / f'latest-api-{api}.json').write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (ValueError, OSError, TypeError):
        reports[api] = None
        (RESULTS / f'latest-api-{api}.json').unlink(missing_ok=True)

    for kind in ('owner', 'client', 'f3-picker'):
        filename = f'{kind}.png'
        source = folder / filename
        target = IMAGES / f'stage3-api-{api}-{kind}.png'
        if reports[api] is not None and source.is_file() and source.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            shutil.copyfile(source, target)
            screenshots[(api, kind)] = f'<img src="{target.as_posix()}" width="220" alt="{kind}, Android {version}">'
        else:
            if target.is_file():
                screenshots[(api, kind)] = ('<img src="' + target.as_posix() + '" width="220" alt="' + kind + '" >')
            else:
                screenshots[(api, kind)] = 'Нет сохранённого скриншота'


def row_for(api, test_id):
    data = reports[api]
    if not data:
        return ('НЕТ ОТЧЁТА', 'Эксперимент не выполнялся или отсутствует отчёт')
    match = next((x for x in data.get('results', [])
                  if isinstance(x, dict) and x.get('id') == test_id), None)
    if not match:
        return ('НЕ ВЫПОЛНЕН', 'Нет записи об эксперименте')
    observed = str(match.get('observed', '?')).replace('|', '/').replace('\n', ' ').replace('\r', ' ')
    detail = str(match.get('detail', '')).replace('|', '/').replace('\n', ' ').replace('\r', ' ')
    status = 'PASS' if match.get('pass') is True else ('ERROR' if observed == 'ERROR' else 'FAIL')
    return (f'{status} ({observed})', detail[:240])


def total(api):
    data = reports[api]
    if not data:
        return 'NO REPORT'
    ids = {x.get('id') for x in data.get('results', []) if isinstance(x, dict)}
    expected = {x['id'] for x in TESTS}
    if not expected.issubset(ids):
        return 'INCOMPLETE'
    return 'PASS' if all(row_for(api, x['id'])[0].startswith('PASS') for x in TESTS) else 'FAIL'


url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
when = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
lines = [
    START,
    '## Экспериментальные результаты Android Security Lab',
    '',
    f'Обновлено: **{when}**. [Запуск GitHub Actions]({url}).',
    '',
    '| Проверка | Android 13 (API 33) | Android 16 (API 36) |',
    '|---|---|---|',
]
for test in TESTS:
    tid = test['id']
    lines.append(f"| **{tid}** — {test['title']} | {row_for(33, tid)[0]} | {row_for(36, tid)[0]} |")
lines.extend([
    '',
    f'**Сводный статус:** Android 13 — {total(33)}; Android 16 — {total(36)}.',
    '',
    '### Наблюдения и интерпретация',
    '',
    '| Сценарий | Android 13: наблюдение | Android 16: наблюдение |',
    '|---|---|---|',
])
for test in TESTS:
    tid = test['id']
    lines.append(f"| {tid} | {row_for(33, tid)[1]} | {row_for(36, tid)[1]} |")
lines.extend([
    '',
    '### Скриншоты из Android Emulator',
    '',
    '| Материал | Android 13 | Android 16 |',
    '|---|---|---|',
])
for kind, label in (('owner', 'SecurityOwner'), ('client', 'SecurityClient'), ('f3-picker', 'Системный выбор документа F3')):
    lines.append(f"| {label} | {screenshots[(33, kind)]} | {screenshots[(36, kind)]} |")
lines.extend([
    '',
    '> PASS означает совпадение наблюдаемого поведения с гипотезой, в том числе при отказе в доступе. ',
    '> Инфраструктурная ошибка не считается подтверждением механизма безопасности. ',
    '> Тесты выполняются в эмуляторах, без выводов об аппаратной защите физического смартфона.',
    '',
    'Подробные машинно-читаемые данные находятся в [`results/`](results/), а журналы и дополнительные файлы — в Artifacts запуска.',
    '',
    END,
])
block = '\n'.join(lines)
original = README.read_text(encoding='utf-8') if README.is_file() else '# Android Security Lab\n'
if START in original and END in original:
    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    updated = before.rstrip() + '\n\n' + block + after
elif START not in original and END not in original:
    updated = original.rstrip() + '\n\n' + block + '\n'
else:
    raise SystemExit('README has one missing management marker; no replacement performed')
README.write_text(updated.rstrip() + '\n', encoding='utf-8')
(RESULTS / 'summary.json').write_text(json.dumps({
    'generated_at_utc': when,
    'workflow_run_url': url,
    'expected_scenarios': [x['id'] for x in TESTS],
    'api_33': total(33),
    'api_36': total(36),
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Published', len(TESTS), 'unique scenarios: Android 13', total(33), '/ Android 16', total(36))

# ASL_VISUAL_EVIDENCE_V1 - extend successful result publication with verified UI captures.
# This code runs after the existing guarded publisher. It never alters the measured JSON.
from pathlib import Path as _ASLPath
_ASL_SRC = _ASLPath('downloaded')
_ASL_DST = _ASLPath('docs/screenshots')
_ASL_DST.mkdir(parents=True, exist_ok=True)
_ASL_NAMES = (
    'installed-apps.png', 'camera-permission-dialog.png',
    'evidence-p1.png','evidence-p2.png','evidence-p3.png',
    'evidence-f1.png','evidence-f2.png',
    'evidence-k1.png','evidence-k2.png','evidence-k3.png',
)
for _api in (33, 36):
    _folder = _ASL_SRC / f'securitylab-api-{_api}'
    for _name in _ASL_NAMES:
        _src = _folder / _name
        _dst = _ASL_DST / f'api-{_api}-{_name}'
        if _src.is_file() and _src.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            _dst.write_bytes(_src.read_bytes())
            print(f'Published system/app screenshot: {_dst}')
        elif _dst.is_file():
            print(f'Retaining last verified screenshot: {_dst}')


# Refresh legacy Stage 1 image references as well: these are real, newly
# captured Owner/Client screens, not stale PASS-only screenshots.
for _api, _version in ((33, '13'), (36, '16')):
    for _role in ('owner', 'client'):
        _src = _ASL_SRC / f'securitylab-api-{_api}' / f'{_role}.png'
        _dst = _ASL_DST / f'stage1-android-{_version}-{_role}.png'
        if _src.is_file() and _src.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            _dst.write_bytes(_src.read_bytes())
            print(f'Refreshed Stage 1 UI: {_dst}')


def _asl_img(api, name, alt):
    _p = _ASL_DST / f'api-{api}-{name}'
    return (f'<img src="{_p.as_posix()}" width="245" alt="{alt}">'
            if _p.is_file() else 'Нет подтверждённого изображения')


_asl_rows = [
    ('Установленные приложения в системном меню', 'installed-apps.png'),
    ('Системный запрос доступа к CAMERA', 'camera-permission-dialog.png'),
    ('P1: разрешение CAMERA отсутствует', 'evidence-p1.png'),
    ('P2: разрешение CAMERA предоставлено', 'evidence-p2.png'),
    ('P3: разрешение CAMERA отозвано', 'evidence-p3.png'),
    ('F1: чтение собственного файла', 'evidence-f1.png'),
    ('F2: запрет чтения чужого файла', 'evidence-f2.png'),
    ('K1: шифрование и расшифрование', 'evidence-k1.png'),
    ('K2: отказ в экспорте ключа', 'evidence-k2.png'),
    ('K3: межприложенная изоляция ключа', 'evidence-k3.png'),
]
_asl_lines = [
    '<!-- ASL_VISUAL_GALLERY_START -->',
    '| Наблюдение | Android 13 | Android 16 |',
    '|---|---|---|',
]
for _title, _name in _asl_rows:
    _asl_lines.append(
        f'| {_title} | {_asl_img(33, _name, _title + " API 33")} | '
        f'{_asl_img(36, _name, _title + " API 36")} |'
    )
_asl_lines += [
    '',
    'S1 и S2–S5: реальные результаты операций показаны на экранах Owner/Client ниже; '
    'ошибки Android дополнительно подтверждаются `detail` в JSON и Logcat. '
    'F3: подлинный системный выбор документа показан в разделе файловых испытаний.',
    '',
    'Для отказов в доступе Android не всегда показывает системное окно: '
    'приложение получает исключение или ответ API. '
    'Диагностические экраны отображают именно эти ответы, а не системные уведомления.',
    '<!-- ASL_VISUAL_GALLERY_END -->',
]
_asl_readme = _ASLPath('README.md')
_asl_text = _asl_readme.read_text(encoding='utf-8')
_asl_start = '<!-- ASL_VISUAL_GALLERY_START -->'
_asl_end = '<!-- ASL_VISUAL_GALLERY_END -->'
if _asl_text.count(_asl_start)!=1 or _asl_text.count(_asl_end)!=1:
    raise SystemExit('Cannot update visual gallery: README markers missing or duplicated')
_asl_before, _asl_rest = _asl_text.split(_asl_start,1)
_, _asl_after = _asl_rest.split(_asl_end,1)
_asl_new = _asl_before + '\n'.join(_asl_lines) + _asl_after
_asl_new = _asl_new.replace('Это рабочая документация экспериментов, а не текст курсового отчёта.', '')
_asl_readme.write_text(_asl_new, encoding='utf-8')
