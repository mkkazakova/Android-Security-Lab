// ASL_VISUAL_EVIDENCE_V1
// Managed by project-update.yml - Stage 2
package org.example.securitylab.client

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import org.json.JSONObject

class PermissionProbeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val testId =
            intent.getStringExtra("experiment_id") ?: "UNKNOWN"

        val expected =
            if (testId == "P2") "ALLOW" else "DENY"

        val granted =
            checkSelfPermission(Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED

        val observed =
            if (granted) "ALLOW" else "DENY"

        val passed =
            testId in setOf("P1", "P2", "P3") &&
                observed == expected

        val result = JSONObject()
            .put("id", testId)
            .put("expected", expected)
            .put("observed", observed)
            .put("pass", passed)
            .put(
                "detail",
                "CAMERA state checked inside SecurityClient"
            )

        Log.i(
            "SecurityLab",
            "ASL_PERMISSION_RESULT:$result"
        )

        EvidenceScreen.show(this, "SecurityClient • Разрешение CAMERA", listOf(result))
    }
}
