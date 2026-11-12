package com.banglavoice.studio

import android.app.Activity
import android.os.Bundle
import android.content.Intent
import android.net.Uri
import android.media.MediaPlayer
import android.graphics.Color
import android.widget.*
import java.net.HttpURLConnection
import java.net.URL
import java.io.File
import java.util.UUID
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private lateinit var server: EditText
    private lateinit var words: EditText
    private lateinit var status: TextView
    private lateinit var language: Spinner
    private var sample: Uri? = null
    private var output: File? = null
    private var player: MediaPlayer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 36, 32, 24)
            setBackgroundColor(Color.rgb(247,249,252))
        }
        setContentView(ScrollView(this).apply { addView(root) })
        fun heading(s: String) = TextView(this).apply {
            text = s; textSize = 18f; setTextColor(Color.rgb(22,38,65))
            setPadding(0,14,0,10); root.addView(this)
        }
        fun button(s: String, action: () -> Unit) {
            root.addView(Button(this).apply { text = s; setOnClickListener { action() } })
        }
        heading("বাংলা Voice Studio")
        heading("AI server URL (HTTPS)")
        server = EditText(this).apply {
            hint = "https://your-server.example"
            setSingleLine(true)
            setText(getPreferences(0).getString("server", ""))
            root.addView(this)
        }
        heading("ভাষা")
        language = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity,
                android.R.layout.simple_spinner_dropdown_item, listOf("বাংলা", "English"))
            root.addView(this)
        }
        heading("টেক্সট")
        words = EditText(this).apply {
            hint = "এখানে বাংলা বা ইংরেজি লিখুন"
            minLines = 5
            root.addView(this)
        }
        button("Voice sample নির্বাচন (ঐচ্ছিক)") {
            startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                type = "audio/*"; addCategory(Intent.CATEGORY_OPENABLE)
            }, 101)
        }
        heading("শুধু নিজের বা অনুমতি পাওয়া কণ্ঠ ক্লোন করুন।")
        button("Generate Voice") { generate() }
        button("Play") {
            val file = output
            if (file == null) show("আগে অডিও তৈরি করুন")
            else try {
                player?.release()
                player = MediaPlayer().apply { setDataSource(file.absolutePath); prepare(); start() }
            } catch (e: Exception) { show(e.message ?: "Playback failed") }
        }
        button("Save WAV") {
            if (output == null) show("আগে অডিও তৈরি করুন")
            else startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                type = "audio/wav"
                putExtra(Intent.EXTRA_TITLE, "bangla-voice.wav")
                addCategory(Intent.CATEGORY_OPENABLE)
            }, 102)
        }
        status = TextView(this).apply { text = "Ready"; setPadding(0,18,0,0); root.addView(this) }
    }

    private fun show(message: String) { runOnUiThread { status.text = message } }

    private fun generate() {
        val base = server.text.toString().trim().trimEnd('/')
        val text = words.text.toString().trim()
        if (!base.startsWith("https://")) { show("HTTPS server URL দিন"); return }
        if (text.isEmpty()) { show("টেক্সট লিখুন"); return }
        getPreferences(0).edit().putString("server", base).apply()
        val lang = if (language.selectedItemPosition == 0) "bengali" else "english"
        val chosen = sample
        show("Generating...")
        thread {
            var conn: HttpURLConnection? = null
            try {
                val url = if (chosen != null)
                    URL("$base/clone?text=${java.net.URLEncoder.encode(text, "UTF-8")}&lang=$lang&style=default")
                else URL("$base/synthesize")
                conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 30000; readTimeout = 300000; doOutput = true
                }
                if (chosen != null) {
                    val boundary = "----VoiceStudio" + UUID.randomUUID()
                    conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                    conn.outputStream.use { out ->
                        out.write("--$boundary\r\nContent-Disposition: form-data; name=\"speaker_wav\"; filename=\"sample.wav\"\r\nContent-Type: audio/wav\r\n\r\n".toByteArray())
                        contentResolver.openInputStream(chosen)!!.use { it.copyTo(out) }
                        out.write("\r\n--$boundary--\r\n".toByteArray())
                    }
                } else {
                    conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    val json = org.json.JSONObject().put("text", text).put("lang", lang)
                        .put("style", "default").toString()
                    conn.outputStream.use { it.write(json.toByteArray(Charsets.UTF_8)) }
                }
                if (conn.responseCode !in 200..299)
                    throw Exception("Server error ${conn.responseCode}")
                if ((conn.contentType ?: "").contains("json"))
                    throw Exception("Server did not return audio")
                val file = File(cacheDir, "voice-${System.currentTimeMillis()}.wav")
                conn.inputStream.use { input -> file.outputStream().use { input.copyTo(it) } }
                output = file
                show("অডিও তৈরি হয়েছে!")
            } catch (e: Exception) { show("সমস্যা: ${e.message}") }
            finally { conn?.disconnect() }
        }
    }

    @Deprecated("Legacy result API")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK) return
        if (requestCode == 101) {
            sample = data?.data
            show("Voice sample selected")
        }
        if (requestCode == 102) {
            val dest = data?.data
            val file = output
            if (dest != null && file != null) try {
                contentResolver.openOutputStream(dest)?.use { out ->
                    file.inputStream().use { it.copyTo(out) }
                }
                show("Saved")
            } catch (e: Exception) { show("Save failed: ${e.message}") }
        }
    }

    override fun onDestroy() { player?.release(); super.onDestroy() }
}
