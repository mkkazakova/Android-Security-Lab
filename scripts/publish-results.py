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
            target.unlink(missing_ok=True)
            screenshots[(api, kind)] = 'Нет скриншота текущего запуска'


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
