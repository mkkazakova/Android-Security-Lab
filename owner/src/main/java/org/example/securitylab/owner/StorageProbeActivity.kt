// Managed by project-update.yml - Stage 3
package org.example.securitylab.owner

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import org.json.JSONObject
import java.io.File

class StorageProbeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val expected = "ALLOW"
        var observed = "ERROR"
        var detail = ""
        try {
            val dir = getExternalFilesDir(null) ?: error("External app-specific directory is unavailable")
            val fixture = File(dir, "ASL_OWNER_EXTERNAL_FIXTURE.txt")
            fixture.writeText("ASL_STAGE3_OWNER_FIXTURE")
            val content = fixture.readText()
            observed = if (content == "ASL_STAGE3_OWNER_FIXTURE") "ALLOW" else "INCORRECT_DATA"
            detail = "Read own app-specific external file via getExternalFilesDir"
        } catch (e: Exception) {
            detail = "${e.javaClass.simpleName}: ${e.message}"
        }
        val passed = observed == expected
        val result = JSONObject()
            .put("id", "F1").put("expected", expected)
            .put("observed", observed).put("pass", passed)
            .put("detail", detail)
        Log.i("SecurityLab", "ASL_STORAGE_RESULT:$result")
        setContentView(TextView(this).apply {
            text = "Storage F1: $observed"
            textSize = 23f
        })
    }
}
