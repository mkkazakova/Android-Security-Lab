# Методика 14 экспериментов

Все сценарии выполнены на Android 13 (API 33) и Android 16 (API 36), при `targetSdk=33`. Последний проверенный успешный прогон содержит 28 результатов PASS.

## Как повторить

Запустить **Actions → Android Security Lab - Complete Experiments → Run workflow** на ветке `master`. Просмотреть оба задания Android API 33/36 и итоговую публикацию. Результаты — в [`results/`](../results/), журналы — в Artifacts соответствующего запуска.

## Сценарии

| ID | Проверяемое действие | Ожидаемое наблюдение | API 33 | API 36 |
|---|---|---|---|---|
| [S1](../README.md) | Чтение собственного приватного файла | `ALLOW` | PASS | PASS |
| [S2](../README.md) | Попытка чтения чужого приватного файла | `DENY` | PASS | PASS |
| [S3](../README.md) | Доступ к закрытому ContentProvider | `DENY` | PASS | PASS |
| [S4](../README.md) | Доступ к открытому ContentProvider | `ALLOW` | PASS | PASS |
| [S5](../README.md) | ContentProvider с проверкой разрешения | `DENY` | PASS | PASS |
| [P1](../README.md) | Камера: разрешение не выдано | `DENY` | PASS | PASS |
| [P2](../README.md) | Камера: разрешение выдано | `ALLOW` | PASS | PASS |
| [P3](../README.md) | Камера: разрешение отозвано | `DENY` | PASS | PASS |
| [F1](../README.md) | Чтение собственного файла во внешнем хранилище | `ALLOW` | PASS | PASS |
| [F2](../README.md) | Прямой доступ к файлу другого приложения | `DENY` | PASS | PASS |
| [F3](../README.md) | Чтение документа через системный выбор файла | `ALLOW` | PASS | PASS |
| [K1](../README.md) | Шифрование и расшифрование с Android Keystore | `ALLOW` | PASS | PASS |
| [K2](../README.md) | Попытка извлечения секретного ключа | `DENY` | PASS | PASS |
| [K3](../README.md) | Межприложенная изоляция ключа | `DENY` | PASS | PASS |

Конкретная последовательность действий и пояснение каждого результата приведены в **[README](../README.md)**. Тесты P1–P3 используют ADB для подготовки состояния разрешения, но проверяют его внутри приложения. Эксперимент F3 использует `ACTION_OPEN_DOCUMENT`; K2 подтверждает неэкспортируемость ключа через `getEncoded()`, но не наличие аппаратной защиты.

Дополнительные методики: [Runtime Permissions](permissions.md), [Scoped Storage](storage.md), [Android Keystore](keystore.md).
