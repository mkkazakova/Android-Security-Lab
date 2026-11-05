<!-- Managed by project-update.yml - Stage 4 Android Keystore -->
# Android Keystore: методика K1–K3

Объект: два разных приложения (`SecurityOwner` и `SecurityClient`) с различными UID в Android Emulator API 33 и API 36. Во всех испытаниях `targetSdk = 33`.

| ID | Метод | Ожидаемое наблюдение |
|---|---|---|
| K1 | Owner создаёт ключ AES-256 через `AndroidKeyStore` и выполняет AES/GCM/NoPadding encrypt/decrypt | ALLOW: восстановлен исходный текст |
| K2 | Owner вызывает `SecretKey.getEncoded()` для ключа K1 | DENY: API возвращает `null`, байты ключа не выдаются |
| K3 | Client с другим UID ищет алиас ключа Owner в собственном `AndroidKeyStore` | DENY: алиас отсутствует, `getKey` возвращает `null` |

Для K3 дополнительно повторно проверяется наличие исходного ключа в Owner: это положительный контроль, исключающий ложноуспешный запрет из-за удаления ключа.

Результат собирается из Logcat самого Android-приложения с меткой `ASL_KEYSTORE_RESULT`, а не по выводу внешней утилиты. Исключения и отсутствие ответа фиксируются как `ERROR` и никогда не считаются подтверждением защиты.

K2 проверяет невозможность извлечь байты через стандартный JCA API, а не математическую неуязвимость ключа ко всем атакам. `KeyInfo.securityLevel`, когда доступен, сохраняется как диагностический признак. Результаты Android Emulator не являются подтверждением аппаратной защиты TEE/StrongBox.

Источники: https://developer.android.com/privacy-and-security/keystore ; https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec ; https://developer.android.com/reference/android/security/keystore/KeyInfo
