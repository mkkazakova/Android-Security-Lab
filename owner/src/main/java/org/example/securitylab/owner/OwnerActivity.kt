package org.example.securitylab.owner

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import org.json.JSONObject

class OwnerActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val data = "LAB_SAMPLE_NO_PERSONAL_DATA"
        val observed: String
        val detail: String
        try {
            openFileOutput("secret.txt", MODE_PRIVATE).bufferedWriter().use { it.write(data) }
            observed = openFileInput("secret.txt").bufferedReader().use { it.readText() }
            detail = "Own private file created and read via application context"
        } catch (e: Exception) {
            Log.e("SecurityLab", "Owner file operation failed", e)
            val result = JSONObject().put("id", "S1").put("expected", "ALLOW")
                .put("observed", "ERROR").put("pass", false)
                .put("detail", e.javaClass.simpleName)
            Log.i("SecurityLab", "ASL_RESULT:$result")
            setContentView(TextView(this).apply { text = "SecurityOwner: error\n${e.message}"; textSize = 20f })
            return
        }
        val passed = observed == data
        val result = JSONObject().put("id", "S1").put("expected", "ALLOW")
            .put("observed", if (passed) "ALLOW" else "INCORRECT_DATA")
            .put("pass", passed).put("detail", detail)
        Log.i("SecurityLab", "ASL_RESULT:$result")
        setContentView(TextView(this).apply {
            text = "SecurityOwner\n\nS1: " + (if (passed) "PASS" else "FAIL")
            textSize = 24f
            setPadding(28, 48, 16, 16)
        })
    }
}
