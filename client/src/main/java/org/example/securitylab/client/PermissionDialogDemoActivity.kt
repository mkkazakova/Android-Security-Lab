// ASL_VISUAL_EVIDENCE_V1
package org.example.securitylab.client

import android.Manifest
import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class PermissionDialogDemoActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply {
            text = "SecurityClient\n\nДемонстрация системного запроса CAMERA\n" +
                "Разрешение будет запрошено у Android."
            textSize = 19f
            setPadding(24, 40, 20, 20)
        })
        requestPermissions(arrayOf(Manifest.permission.CAMERA), 9113)
    }
}
