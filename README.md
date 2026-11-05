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
## Экспериментальные результаты Android Security Lab

Обновлено: **2026-11-05 11:06 UTC**. [Запуск GitHub Actions](https://github.com/mkkazakova/Android-Security-Lab/actions/runs/42015734525).

| Проверка | Android 13 (API 33) | Android 16 (API 36) |
|---|---|---|
| **S1** — Владелец читает собственный приватный файл | PASS (ALLOW) | PASS (ALLOW) |
| **S2** — Другой UID не читает приватный файл | PASS (DENY) | PASS (DENY) |
| **S3** — Закрытый ContentProvider отклоняет запрос | PASS (DENY) | PASS (DENY) |
| **S4** — Открытый ContentProvider предоставляет данные | PASS (ALLOW) | PASS (ALLOW) |
| **S5** — ContentProvider защищён разрешением | PASS (DENY) | PASS (DENY) |
| **P1** — CAMERA: разрешение отсутствует | PASS (DENY) | PASS (DENY) |
| **P2** — CAMERA: разрешение выдано | PASS (ALLOW) | PASS (ALLOW) |
| **P3** — CAMERA: разрешение отозвано | PASS (DENY) | PASS (DENY) |
| **F1** — Владелец читает свой app-specific внешний файл | PASS (ALLOW) | PASS (ALLOW) |
| **F2** — Другому приложению запрещён прямой доступ к app-specific файлу | PASS (DENY) | PASS (DENY) |
| **F3** — Доступ к документу через системный выбор файла | ERROR (ERROR) | ERROR (ERROR) |

**Сводный статус:** Android 13 — FAIL; Android 16 — FAIL.

### Наблюдения и интерпретация

| Сценарий | Android 13: наблюдение | Android 16: наблюдение |
|---|---|---|
| S1 | Own private file created and read via application context | Own private file created and read via application context |
| S2 | Direct access rejected: FileNotFoundException; host verifies file exists | Direct access rejected: FileNotFoundException; host verifies file exists |
| S3 | Framework rejected query: SecurityException | Framework rejected query: SecurityException |
| S4 | Expected test data returned from provider | Expected test data returned from provider |
| S5 | Framework rejected query: SecurityException | Framework rejected query: SecurityException |
| P1 | CAMERA state checked inside SecurityClient | CAMERA state checked inside SecurityClient |
| P2 | CAMERA state checked inside SecurityClient | CAMERA state checked inside SecurityClient |
| P3 | CAMERA state checked inside SecurityClient | CAMERA state checked inside SecurityClient |
| F1 | Read own app-specific external file via getExternalFilesDir | Read own app-specific external file via getExternalFilesDir |
| F2 | Direct cross-app read rejected: FileNotFoundException; F1 verifies fixture | Direct cross-app read rejected: FileNotFoundException; F1 verifies fixture |
| F3 | No application-side result for F3 | No application-side result for F3 |

### Скриншоты из Android Emulator

| Материал | Android 13 | Android 16 |
|---|---|---|
| SecurityOwner | <img src="docs/screenshots/stage3-api-33-owner.png" width="220" alt="owner, Android 13"> | <img src="docs/screenshots/stage3-api-36-owner.png" width="220" alt="owner, Android 16"> |
| SecurityClient | <img src="docs/screenshots/stage3-api-33-client.png" width="220" alt="client, Android 13"> | <img src="docs/screenshots/stage3-api-36-client.png" width="220" alt="client, Android 16"> |
| Системный выбор документа F3 | <img src="docs/screenshots/stage3-api-33-f3-picker.png" width="220" alt="f3-picker, Android 13"> | <img src="docs/screenshots/stage3-api-36-f3-picker.png" width="220" alt="f3-picker, Android 16"> |

> PASS означает совпадение наблюдаемого поведения с гипотезой, в том числе при отказе в доступе. 
> Инфраструктурная ошибка не считается подтверждением механизма безопасности. 
> Тесты выполняются в эмуляторах, без выводов об аппаратной защите физического смартфона.

Подробные машинно-читаемые данные находятся в [`results/`](results/), а журналы и дополнительные файлы — в Artifacts запуска.

<!-- ANDROID_STAGE1_END -->

<!-- RESEARCH_DOCS_LINKS_START -->
## Документация курсовой работы

- [План курсовой](docs/project-plan.md)
- [Архитектура испытательного стенда](docs/architecture.md)
- [Методика: 14 экспериментов](experiments/test-plan.md)
- [Проект официального задания](docs/course-assignment.md)

<!-- RESEARCH_DOCS_LINKS_END -->
