<!-- Managed by project-update.yml - Stage 3 -->
# Scoped Storage: методика F1–F3

Исследуются ограничения доступа к файлам на Android 13 и Android 16 при фиксированном `targetSdk=33`.

| ID | Действие | Ожидается |
|---|---|---|
| F1 | Owner создаёт и читает тестовый файл в `getExternalFilesDir(null)` | ALLOW |
| F2 | Client напрямую читает этот файл по пути `/storage/emulated/0/Android/data/<owner>/files/...` | DENY |
| F3 | Client вызывает `ACTION_OPEN_DOCUMENT`, выбирает синтетический документ в системном интерфейсе, затем читает выданный URI | ALLOW |

F1 является положительным контролем для F2: при его провале отрицательный тест не считается подтверждённым. Содержание файлов синтетическое, персональные данные не используются.

F3 действительно использует системный документный интерфейс Android, а не напрямую предоставленный из ADB URI. ADB используется только для подготовки тестового файла в папке Download и автоматизации нажатия на элемент интерфейса. Ошибка UI-автоматизации фиксируется как ERROR/FAIL, не как ошибка безопасности Android.

На эмуляторах не проверяется защита физической флеш-памяти и аппаратные механизмы.

Документация: https://developer.android.com/about/versions/11/privacy/storage ; https://developer.android.com/training/data-storage/shared/documents-files
