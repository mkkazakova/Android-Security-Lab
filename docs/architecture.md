# Структура Android Security Lab

## Компоненты

- `owner/` — приложение **SecurityOwner**. Создаёт тестовые файлы и ContentProvider, использует Android Keystore, выполняет контрольные операции от своего UID.
- `client/` — независимое приложение **SecurityClient** с другим UID. Выполняет попытки доступа к чужим данным, проверяет состояние CAMERA и доступ к выбранному через системный интерфейс документу.
- `scripts/run-stage1.sh` — проверки S1–S5: Sandbox и IPC.
- `scripts/run-stage2.sh` — дополнительно P1–P3: Runtime Permissions.
- `scripts/run-stage3.sh` и `scripts/storage-tests.py` — дополнительно F1–F3: Scoped Storage.
- `scripts/run-stage4.sh` и `scripts/keystore-tests.py` — дополнительно K1–K3: Android Keystore.
- `scripts/run-tests.sh` — точка входа для полного запуска всех 14 сценариев.
- `scripts/publish-results.py` — обновляет сохранённые JSON, изображения и сводную таблицу README, не перезаписывая постоянные инструкции.
- `.github/workflows/android-tests.yml` — сборка двух APK, запуск Android Emulator API 33 и API 36 и публикация результатов.
- `results/` — сохранённые сводные JSON для каждого API и итоговая сводка.
- `docs/screenshots/` — сохранённые изображения. Дополнительные логи доступны в Artifacts запуска.

## Последовательность испытаний

`android-tests.yml` → сборка `owner` и `client` → запуск эмулятора → `scripts/run-tests.sh` → Android-приложения → JSON и скриншоты → `scripts/publish-results.py` → README и `results/`.

## Условия достоверности

- Тесты выполняются на Android 13 (API 33) и Android 16 (API 36) с `targetSdk=33` для обоих приложений.
- Доступ проверяется из процессов самих приложений, а не от привилегированного пользователя ADB-shell. ADB используется для подготовки среды, выдачи/отзыва разрешения CAMERA и управления испытаниями.
- Отказ доступа (`DENY`) является успешным результатом только там, где именно такой отказ ожидался.
- Эксперименты не проверяют аппаратную защиту смартфона. Для Android Keystore зафиксирован программный уровень `securityLevel=0`.

Подробное описание каждого сценария, порядок действий, ожидаемое поведение и результаты приведены в [README](../README.md).
