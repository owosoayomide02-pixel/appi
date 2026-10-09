package dev.appi.runtime

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder

/**
 * Persistent heartbeat service. Requires a visible notification.
 * Does not use AccessibilityService. Does not bypass MFA or system dialogs.
 * Files, browser, terminal, and assistant control are not implemented on Android yet.
 */
class AppiForegroundService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val channelId = "appi.runtime"
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(channelId, "Appi runtime", NotificationManager.IMPORTANCE_LOW)
            )
        }
        val body = "Placeholder runtime. Android agent is not implemented yet."
        val notification = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, channelId)
                .setContentTitle("Appi")
                .setContentText(body)
                .setSmallIcon(android.R.drawable.ic_btn_speak_now)
                .build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setContentTitle("Appi")
                .setContentText(body)
                .setSmallIcon(android.R.drawable.ic_btn_speak_now)
                .build()
        }
        startForeground(1, notification)
        return START_STICKY
    }
}
