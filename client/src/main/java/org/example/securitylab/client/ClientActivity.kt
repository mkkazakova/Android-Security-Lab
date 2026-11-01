package org.example.securitylab.client

import android.app.Activity
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import org.json.JSONObject
import java.io.File

class ClientActivity : Activity() {
    private val records = mutableListOf<Triple<String, Boolean, String>>()
    private lateinit var statusView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        statusView = TextView(this).apply {
            textSize = 19f
            setPadding(28, 40, 18, 18)
            text = "SecurityClient\nRunning S2–S5..."
        }
        setContentView(statusView)
        Thread { runExperiments() }.start()
    }

    private fun report(id: String, expected: String, observed: String, detail: String) {
        val passed = expected == observed
        val result = JSONObject().put("id", id).put("expected", expected)
            .put("observed", observed).put("pass", passed).put("detail", detail.take(200))
        Log.i("SecurityLab", "ASL_RESULT:$result")
        synchronized(records) { records.add(Triple(id, passed, observed)) }
    }

    private data class Observation(val value: String, val detail: String)

    private fun providerRead(authority: String): Observation {
        return try {
            val cursor = contentResolver.query(Uri.parse("content://$authority/sample"), null, null, null, null)
            if (cursor == null) {
                Observation("INCONCLUSIVE", "Provider returned null cursor; this alone is not proof of access denial")
            } else {
                cursor.use {
                    if (it.moveToFirst() && it.getString(0) == "LAB_SAMPLE_NO_PERSONAL_DATA") {
                        Observation("ALLOW", "Expected test data returned from provider")
                    } else {
                        Observation("INCORRECT_DATA", "Provider did not return expected test content")
                    }
                }
            }
        } catch (e: SecurityException) {
            Observation("DENY", "Framework rejected query: ${e.javaClass.simpleName}")
        } catch (e: Exception) {
            Observation("ERROR", "Unexpected: ${e.javaClass.simpleName}: ${e.message}")
        }
    }

    private fun runExperiments() {
        // Positive control first: if exported provider is inaccessible, negatives are inconclusive.
        val public = providerRead("org.example.securitylab.owner.public")
        report("S4", "ALLOW", public.value, public.detail)

        val privateFile = try {
            val data = File("/data/user/0/org.example.securitylab.owner/files/secret.txt").readText()
            if (data == "LAB_SAMPLE_NO_PERSONAL_DATA") {
                Observation("ALLOW", "Another app unexpectedly read the owner private file")
            } else {
                Observation("INCORRECT_DATA", "Unexpected file content")
            }
        } catch (e: java.io.FileNotFoundException) {
            Observation("DENY", "Direct access rejected: ${e.javaClass.simpleName}; host verifies file exists")
        } catch (e: SecurityException) {
            Observation("DENY", "Direct access rejected: ${e.javaClass.simpleName}")
        } catch (e: Exception) {
            Observation("ERROR", "Unexpected: ${e.javaClass.simpleName}")
        }
        report("S2", "DENY", privateFile.value, privateFile.detail)

        val privateProvider = providerRead("org.example.securitylab.owner.private")
        report("S3", "DENY", privateProvider.value, privateProvider.detail)

        val guarded = providerRead("org.example.securitylab.owner.protected")
        report("S5", "DENY", guarded.value, guarded.detail)

        val results = synchronized(records) { records.sortedBy { it.first }.toList() }
        runOnUiThread {
            statusView.text = buildString {
                append("SecurityClient — Sandbox / IPC\n\n")
                results.forEach { (id, passed, observed) ->
                    append("$id: ${if (passed) "PASS" else "FAIL"} ($observed)\n")
                }
                append("\nDetailed records: GitHub Actions logs")
            }
        }
    }
}
