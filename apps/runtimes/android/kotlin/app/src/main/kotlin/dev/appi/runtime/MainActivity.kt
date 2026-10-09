package dev.appi.runtime

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        val text = TextView(this).apply {
            text = (
                "Appi on Android is a placeholder in this milestone.\n\n" +
                    "This app keeps a visible notification so a future runtime can stay alive. " +
                    "It cannot open files, Chrome, the terminal, or act as your phone assistant yet.\n\n" +
                    "The working assistant is the Windows background runtime. " +
                    "Say Appi there after you pair the laptop."
                )
            textSize = 16f
            setPadding(48, 48, 48, 48)
        }
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(text)
        }
        setContentView(layout)
        startForegroundService(Intent(this, AppiForegroundService::class.java))
    }
}
