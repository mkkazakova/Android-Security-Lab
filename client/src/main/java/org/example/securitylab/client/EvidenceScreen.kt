// ASL_VISUAL_EVIDENCE_V1
package org.example.securitylab.client

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONObject

// Each card receives an observed JSON record emitted by the Android API test itself.
// No permission/access result is hardcoded in this visual component.
object EvidenceScreen {
    private fun dp(activity: Activity, number: Int): Int =
        (number * activity.resources.displayMetrics.density + 0.5f).toInt()

    private fun surface(activity: Activity, bg: Int, radius: Int): GradientDrawable =
        GradientDrawable().apply {
            setColor(bg)
            cornerRadius = dp(activity, radius).toFloat()
        }

    private fun label(activity: Activity, value: String, size: Float,
                      color: Int, bold: Boolean = false): TextView = TextView(activity).apply {
        text = value
        textSize = size
        setTextColor(color)
        if (bold) setTypeface(Typeface.DEFAULT, Typeface.BOLD)
        setLineSpacing(dp(activity, 2).toFloat(), 1f)
    }

    private fun operation(id: String): String = when (id) {
        "S1" -> "Создать файл во внутренней папке и прочитать его"
        "S2" -> "Прочитать чужой приватный файл по прямому пути"
        "S3" -> "Запросить закрытый ContentProvider"
        "S4" -> "Запросить открытый ContentProvider"
        "S5" -> "Запросить ContentProvider с ограничением доступа"
        "P1", "P2", "P3" -> "checkSelfPermission(CAMERA)"
        "F1" -> "getExternalFilesDir() и чтение собственного файла"
        "F2" -> "Чтение файла из Android/data другого приложения"
        "F3" -> "ACTION_OPEN_DOCUMENT и ContentResolver"
        "K1" -> "AES/GCM: шифрование и расшифрование"
        "K2" -> "SecretKey.getEncoded() и KeyInfo"
        "K3" -> "Доступ к имени ключа из другого UID"
        else -> "Операция Android API"
    }

    fun show(activity: Activity, title: String, records: List<JSONObject>) {
        val navy = Color.rgb(20, 36, 58)
        val gray = Color.rgb(82, 97, 112)
        val root = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(activity, 18), dp(activity, 23), dp(activity, 18), dp(activity, 25))
            setBackgroundColor(Color.rgb(243, 246, 250))
        }
        val scroll = ScrollView(activity).apply { isFillViewport = true }
        scroll.addView(root)
        activity.setContentView(scroll)

        root.addView(label(activity, "ANDROID SECURITY LAB", 12f, gray, true))
        root.addView(label(activity, title, 23f, navy, true).apply {
            setPadding(0, dp(activity, 4), 0, dp(activity, 6))
        })
        root.addView(label(activity, "Результаты операций внутри Android-приложения", 12f, gray))
        root.addView(label(activity, "Android API ${android.os.Build.VERSION.SDK_INT}  •  " +
            activity.packageName, 11f, gray).apply {
            setPadding(0, dp(activity, 6), 0, dp(activity, 15))
        })

        for (record in records) {
            val id = record.optString("id", "?")
            val expected = record.optString("expected", "?")
            val observed = record.optString("observed", "?")
            val passed = record.optBoolean("pass", false)
            val detail = record.optString("detail", "Нет диагностической информации")
            val status = if (passed) "СООТВЕТСТВУЕТ ОЖИДАНИЮ" else "ОШИБКА / НЕСОВПАДЕНИЕ"
            val accent = when {
                !passed -> Color.rgb(173, 40, 51)
                observed == "DENY" -> Color.rgb(145, 54, 38)
                else -> Color.rgb(20, 111, 78)
            }
            val card = LinearLayout(activity).apply {
                orientation = LinearLayout.VERTICAL
                background = surface(activity, Color.WHITE, 12)
                setPadding(dp(activity, 14), dp(activity, 12), dp(activity, 14), dp(activity, 15))
                elevation = dp(activity, 2).toFloat()
            }
            card.addView(label(activity, "$id  •  $status", 12f, accent, true))
            card.addView(label(activity, operation(id), 13f, navy).apply {
                setPadding(0, dp(activity, 6), 0, dp(activity, 5))
            })
            card.addView(label(activity, "Ожидалось: $expected     Получено: $observed",
                15f, navy, true).apply { setPadding(0, dp(activity, 6), 0, dp(activity, 7)) })
            card.addView(label(activity, detail, 13f, gray))
            if (record.has("security_level")) {
                card.addView(label(activity, record.optString("security_level"), 12f, gray).apply {
                    setPadding(0, dp(activity, 6), 0, 0)
                })
            }
            root.addView(card, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { bottomMargin = dp(activity, 10) })
        }
        root.addView(label(activity,
            "Запись создаётся после фактического обращения к Android API; полный протокол сохраняется в Logcat и JSON.",
            11f, gray).apply { setPadding(0, dp(activity, 6), 0, 0) })
    }
}
