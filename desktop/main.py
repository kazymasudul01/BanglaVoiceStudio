"""Bangla Voice Studio desktop client for a user-hosted TTS API."""
import json
import threading
import urllib.request
import urllib.parse
import uuid
import mimetypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bangla Voice Studio")
        self.geometry("720x620")
        self.sample = None
        self.audio = None
        self.url = tk.StringVar()
        self.language = tk.StringVar(value="bengali")
        self.status = tk.StringVar(value="Ready")
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Bangla Voice Studio", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="HTTPS AI server URL").pack(anchor="w", pady=(16,0))
        ttk.Entry(frame, textvariable=self.url).pack(fill="x")
        ttk.Label(frame, text="Language").pack(anchor="w", pady=(12,0))
        ttk.Combobox(frame, textvariable=self.language, values=["bengali", "english"], state="readonly").pack(fill="x")
        ttk.Label(frame, text="Text to speech").pack(anchor="w", pady=(12,0))
        self.words = tk.Text(frame, height=10, wrap="word")
        self.words.pack(fill="both", expand=True)
        ttk.Button(frame, text="Select voice sample (optional)", command=self.pick).pack(fill="x", pady=5)
        ttk.Label(frame, text="Clone only your own voice or one you have permission to use.", wraplength=650).pack(anchor="w")
        ttk.Button(frame, text="Generate audio", command=self.generate).pack(fill="x", pady=5)
        ttk.Button(frame, text="Save WAV", command=self.save).pack(fill="x", pady=5)
        ttk.Label(frame, textvariable=self.status, wraplength=650).pack(anchor="w", pady=10)

    def pick(self):
        self.sample = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3 *.flac"), ("All files", "*.*")]) or None
        self.status.set("Sample: " + (Path(self.sample).name if self.sample else "none"))

    def generate(self):
        base = self.url.get().strip().rstrip("/")
        text = self.words.get("1.0", "end").strip()
        if not base.startswith("https://") or not text:
            messagebox.showerror("Missing input", "Enter an HTTPS server URL and text.")
            return
        self.status.set("Generating...")
        threading.Thread(target=self.request_audio, args=(base, text), daemon=True).start()

    def request_audio(self, base, text):
        try:
            lang = self.language.get()
            if self.sample:
                boundary = "VoiceStudio" + uuid.uuid4().hex
                filename = Path(self.sample).name
                audio = Path(self.sample).read_bytes()
                header = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"speaker_wav\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
                data = header + audio + f"\r\n--{boundary}--\r\n".encode()
                url = base + "/clone?" + urllib.parse.urlencode({"text": text, "lang": lang, "style": "default"})
                content_type = "multipart/form-data; boundary=" + boundary
            else:
                url = base + "/synthesize"
                data = json.dumps({"text": text, "lang": lang, "style": "default"}).encode("utf-8")
                content_type = "application/json"
            req = urllib.request.Request(url, data=data, headers={"Content-Type": content_type}, method="POST")
            with urllib.request.urlopen(req, timeout=300) as response:
                if "json" in response.headers.get("Content-Type", ""):
                    raise ValueError("Server returned JSON instead of audio")
                self.audio = response.read()
            self.after(0, lambda: self.status.set("Audio ready. Click Save WAV."))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: self.status.set("Error: " + msg))

    def save(self):
        if not self.audio:
            messagebox.showinfo("No audio", "Generate audio first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if path:
            Path(path).write_bytes(self.audio)
            self.status.set("Saved: " + path)

if __name__ == "__main__":
    Studio().mainloop()
