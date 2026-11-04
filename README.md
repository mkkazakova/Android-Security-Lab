# Android-Security-Lab

<!-- ANDROID_READINESS_RESULTS_START -->
## Результаты последней проверки эмуляторов

Обновлено: **2026-11-01 21:20 UTC**. [Открыть запуск GitHub Actions](https://github.com/mkkazakova/Android-Security-Lab/actions/runs/41351349897).

| Параметр | Android 13 (API 33) | Android 16 (API 36) |
|---|---|---|
| Состояние инфраструктурного теста | PASS | PASS |
| Фактическая версия Android | 13 | 16 |
| Фактический API | 33 | 36 |
| SELinux (наблюдаемое состояние) | Enforcing | Enforcing |
| Шифрование (состояние эмулятора) | encrypted | encrypted |
| Тип шифрования (эмулятор) | file | file |
| Verified Boot (свойство эмулятора) | — | — |
| Загрузка Android завершена | PASS | PASS |
| Версия API соответствует ожидаемой | PASS | PASS |
| Получен настоящий PNG | PASS | PASS |

### Скриншоты виртуальных устройств

| Android 13 | Android 16 |
|---|---|
| <img src="docs/screenshots/android-13.png" alt="Android 13: реальный экран эмулятора" width="240"> | <img src="docs/screenshots/android-16.png" alt="Android 16: реальный экран эмулятора" width="240"> |

> Примечание: это проверка запуска **эмулятора**, а не испытания изоляции приложений, IPC, Keystore или аппаратного Verified Boot. Значения системных свойств не доказывают эффективность защиты на физическом смартфоне. Подробные журналы и JSON доступны в Artifacts соответствующего запуска.

<!-- ANDROID_READINESS_RESULTS_END -->

<!-- ANDROID_STAGE1_START -->
## Эксперименты: Application Sandbox и IPC

Обновлено: **2026-11-04 21:07 UTC**. [Запуск GitHub Actions](https://github.com/mkkazakova/Android-Security-Lab/actions/runs/41912275087).

| Сценарий | Android 13 (API 33) | Android 16 (API 36) |
|---|---|---|
| **S1** — Owner читает собственный приватный файл | PASS (ALLOW) | PASS (ALLOW) |
| **S2** — Client пытается прочитать приватный файл Owner | PASS (DENY) | PASS (DENY) |
| **S3** — Client обращается к закрытому ContentProvider | PASS (DENY) | PASS (DENY) |
| **S4** — Client обращается к открытому ContentProvider | PASS (ALLOW) | PASS (ALLOW) |
| **S5** — Client обращается к Provider с signature-разрешением | PASS (DENY) | PASS (DENY) |

**Итог:** Android 13 — PASS; Android 16 — PASS.

### Скриншоты последнего запуска

| Приложение | Android 13 | Android 16 |
|---|---|---|
| SecurityOwner | <img src="docs/screenshots/stage1-android-13-owner.png" width="240" alt="owner, Android 13"> | <img src="docs/screenshots/stage1-android-16-owner.png" width="240" alt="owner, Android 16"> |
| SecurityClient | <img src="docs/screenshots/stage1-android-13-client.png" width="240" alt="client, Android 13"> | <img src="docs/screenshots/stage1-android-16-client.png" width="240" alt="client, Android 16"> |

> Данные получены из Android Emulator; аппаратные механизмы защиты смартфона здесь не проверяются.
> Отсутствующий отчёт не считается успешным экспериментом. Полные журналы доступны в Artifacts запуска.

<!-- ANDROID_STAGE1_END -->

<!-- RESEARCH_DOCS_LINKS_START -->
## Документация курсовой работы

- [План курсовой](docs/project-plan.md)
- [Архитектура испытательного стенда](docs/architecture.md)
- [Методика: 14 экспериментов](experiments/test-plan.md)
- [Проект официального задания](docs/course-assignment.md)

<!-- RESEARCH_DOCS_LINKS_END -->
