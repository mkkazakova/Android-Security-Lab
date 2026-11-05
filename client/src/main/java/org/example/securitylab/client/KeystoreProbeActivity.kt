// ASL_VISUAL_EVIDENCE_V1
// Managed by project-update.yml - Stage 4 Android Keystore
package org.example.securitylab.client

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import org.json.JSONObject
import java.security.KeyStore

class KeystoreProbeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val alias = "asl_stage4_owner_aes"
        var observed = "ERROR"
        var detail = ""
        try {
            val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            val isVisible = store.containsAlias(alias)
            val retrieved = store.getKey(alias, null)
            observed = if (!isVisible && retrieved == null) "DENY" else "ALLOW"
            detail = "Client UID: alias visible=$isVisible, key accessible=${retrieved != null}"
        } catch (e: Exception) {
            detail = "${e.javaClass.simpleName}: ${e.message}"
        }
        val result = JSONObject()
            .put("id", "K3")
            .put("expected", "DENY")
            .put("observed", observed)
            .put("pass", observed == "DENY")
            .put("detail", detail)
        Log.i("SecurityLab", "ASL_KEYSTORE_RESULT:$result")
        EvidenceScreen.show(this, "SecurityClient • Android Keystore", listOf(result))
    }
}
