// Managed by project-update.yml - Stage 4 Android Keystore
package org.example.securitylab.owner

import android.app.Activity
import android.os.Bundle
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import android.util.Log
import android.widget.TextView
import org.json.JSONObject
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec

class KeystoreProbeActivity : Activity() {
    private val alias = "asl_stage4_owner_aes"
    private val sample = "ASL_STAGE4_K1_AES_GCM_PAYLOAD"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val scenario = intent.getStringExtra("experiment_id") ?: "UNKNOWN"
        var observed = "ERROR"
        var detail = ""
        var securityLevel: String? = null
        val expected = if (scenario == "K2") "DENY" else "ALLOW"

        try {
            val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            when (scenario) {
                "K1" -> {
                    if (!store.containsAlias(alias)) {
                        val generator = KeyGenerator.getInstance(
                            KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
                        )
                        val spec = KeyGenParameterSpec.Builder(
                            alias,
                            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                        )
                            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                            .setKeySize(256)
                            .build()
                        generator.init(spec)
                        generator.generateKey()
                    }
                    val key = store.getKey(alias, null) as? SecretKey
                        ?: error("Owner key missing after generation")
                    val encrypt = Cipher.getInstance("AES/GCM/NoPadding")
                    encrypt.init(Cipher.ENCRYPT_MODE, key)
                    val ciphertext = encrypt.doFinal(sample.toByteArray(Charsets.UTF_8))
                    val iv = encrypt.iv ?: error("GCM IV unavailable")
                    val decrypt = Cipher.getInstance("AES/GCM/NoPadding")
                    decrypt.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, iv))
                    val plaintext = decrypt.doFinal(ciphertext).toString(Charsets.UTF_8)
                    observed = if (plaintext == sample && iv.isNotEmpty()) "ALLOW" else "INCORRECT_DATA"
                    detail = "AES-256/GCM encrypt-decrypt round-trip; ciphertext and IV generated in app"
                }
                "K2" -> {
                    val key = store.getKey(alias, null) as? SecretKey
                        ?: error("Owner key missing; K1 must run first")
                    val encoded = key.encoded
                    observed = if (encoded == null) "DENY" else "ALLOW"
                    detail = "SecretKey.getEncoded()=" +
                        (if (encoded == null) "null" else "non-null") +
                        "; export via JCA denied only when null"
                    try {
                        val factory = SecretKeyFactory.getInstance("AES", "AndroidKeyStore")
                        val info = factory.getKeySpec(key, KeyInfo::class.java) as KeyInfo
                        securityLevel = "KeyInfo.securityLevel=" + info.securityLevel
                        detail += "; " + securityLevel
                    } catch (e: Exception) {
                        detail += "; security level not established: " + e.javaClass.simpleName
                    }
                }
                "K3_CONTROL" -> {
                    val key = store.getKey(alias, null) as? SecretKey
                    observed = if (store.containsAlias(alias) && key != null) "ALLOW" else "DENY"
                    detail = "Owner can still resolve original alias after cross-app negative test"
                }
                else -> detail = "Unknown experiment ID"
            }
        } catch (e: Exception) {
            detail = "${e.javaClass.simpleName}: ${e.message}"
        }

        val result = JSONObject()
            .put("id", scenario)
            .put("expected", expected)
            .put("observed", observed)
            .put("pass", observed == expected)
            .put("detail", detail)
        if (securityLevel != null) result.put("security_level", securityLevel)
        Log.i("SecurityLab", "ASL_KEYSTORE_RESULT:$result")
        setContentView(TextView(this).apply {
            text = "Keystore $scenario: $observed"
            textSize = 23f
            setPadding(24, 42, 20, 20)
        })
    }
}
