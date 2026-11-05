// Managed by project-update.yml - Stage 3
package org.example.securitylab.client

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.provider.DocumentsContract
import android.util.Log
import android.widget.TextView
import org.json.JSONObject
import java.io.File
import java.io.FileNotFoundException

class StorageProbeActivity : Activity() {
    private val requestOpen = 8301

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        when (intent.getStringExtra("experiment_id")) {
            "F2" -> checkCrossAppRead()
            "F3" -> openDocumentPicker()
            else -> emit("UNKNOWN", "ALLOW", "ERROR", "Unknown experiment ID")
        }
    }

    private fun checkCrossAppRead() {
        var observed = "ERROR"
        var detail = ""
        try {
            val path = File(
                Environment.getExternalStorageDirectory(),
                "Android/data/org.example.securitylab.owner/files/ASL_OWNER_EXTERNAL_FIXTURE.txt"
            )
            val data = path.readText()
            observed = if (data == "ASL_STAGE3_OWNER_FIXTURE") "ALLOW" else "INCORRECT_DATA"
            detail = "Direct cross-app read unexpectedly returned content"
        } catch (e: FileNotFoundException) {
            observed = "DENY"
            detail = "Direct cross-app read rejected: FileNotFoundException; F1 verifies fixture"
        } catch (e: SecurityException) {
            observed = "DENY"
            detail = "Direct cross-app read rejected: SecurityException; F1 verifies fixture"
        } catch (e: Exception) {
            detail = "${e.javaClass.simpleName}: ${e.message}"
        }
        emit("F2", "DENY", observed, detail)
    }

    private fun openDocumentPicker() {
        try {
            val picker = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                putExtra(
                    DocumentsContract.EXTRA_INITIAL_URI,
                    Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADownload")
                )
            }
            startActivityForResult(picker, requestOpen)
        } catch (e: Exception) {
            emit("F3", "ALLOW", "ERROR", "Picker launch failed: ${e.javaClass.simpleName}")
        }
    }

    @Deprecated("Used for reproducible system document picker test")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != requestOpen) return
        if (resultCode != RESULT_OK || data?.data == null) {
            emit("F3", "ALLOW", "ERROR", "User/document picker did not return a URI")
            return
        }
        var observed = "ERROR"
        var detail = ""
        try {
            val uri = data.data!!
            val content = contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
                ?: error("ContentResolver returned no stream")
            observed = if (content == "ASL_STAGE3_SAF_DOCUMENT") "ALLOW" else "INCORRECT_DATA"
            detail = "System picker provided URI; ContentResolver read selected document"
        } catch (e: Exception) {
            detail = "${e.javaClass.simpleName}: ${e.message}"
        }
        emit("F3", "ALLOW", observed, detail)
    }

    private fun emit(id: String, expected: String, observed: String, detail: String) {
        val result = JSONObject()
            .put("id", id).put("expected", expected)
            .put("observed", observed).put("pass", observed == expected)
            .put("detail", detail)
        Log.i("SecurityLab", "ASL_STORAGE_RESULT:$result")
        setContentView(TextView(this).apply {
            text = "$id: $observed"
            textSize = 23f
        })
    }
}
