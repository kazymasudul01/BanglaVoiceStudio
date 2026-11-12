"""Offline neural TTS for Bengali and English (MMS VITS)."""
import threading
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

MODELS = {"বাংলা": "facebook/mms-tts-ben", "English": "facebook/mms-tts-eng"}

class Lite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bangla Voice Studio Lite - Offline Neural Voice")
        self.geometry("730x590")
        self.language = tk.StringVar(value="বাংলা")
        self.delivery = tk.StringVar(value="Inspirational")
        self.status = tk.StringVar(value="Ready. First generation downloads an open-source model.")
        self.models = {}
        self.audio = None
        self.sample_rate = None
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Bangla Voice Studio Lite", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(root, text="বাংলা / English - Neural Text to Speech").pack(anchor="w", pady=8)
        ttk.Combobox(root, textvariable=self.language, values=list(MODELS), state="readonly").pack(fill="x", pady=8)
        ttk.Label(root, text="Narration pacing (pauses, not true emotion synthesis)").pack(anchor="w")
        ttk.Combobox(root, textvariable=self.delivery, values=["Inspirational", "Calm", "Neutral"], state="readonly").pack(fill="x", pady=6)
        self.input = tk.Text(root, height=13, wrap="word", font=("Segoe UI", 12))
        self.input.pack(fill="both", expand=True, pady=8)
        self.input.insert("1.0", "জীবনে সফল হতে হলে সব সময় বড় কিছু দিয়ে শুরু করতে হয় না।")
        self.generate_btn = ttk.Button(root, text="Generate Natural Voice", command=self.generate)
        self.generate_btn.pack(fill="x", pady=6)
        ttk.Button(root, text="Save WAV", command=self.save).pack(fill="x", pady=6)
        ttk.Label(root, textvariable=self.status, wraplength=660).pack(anchor="w", pady=10)
        ttk.Label(root, text="First run needs internet to download models. Later runs can be offline. Voice quality varies.", wraplength=660).pack(anchor="w")

    def set_status(self, value):
        self.after(0, lambda: self.status.set(value))

    def generate(self):
        text = self.input.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Text needed", "Please enter text.")
            return
        lang = self.language.get()
        self.generate_btn.config(state="disabled")
        self.status.set("Loading neural voice model; first run may take several minutes...")
        threading.Thread(target=self.worker, args=(lang, text, self.delivery.get()), daemon=True).start()

    def worker(self, lang, text, delivery):
        try:
            import torch
            from transformers import VitsModel, AutoTokenizer
            model_id = MODELS[lang]
            if model_id not in self.models:
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = VitsModel.from_pretrained(model_id)
                model.eval()
                self.models[model_id] = (tokenizer, model)
            tokenizer, model = self.models[model_id]
            self.set_status("Generating audio on CPU...")
            import numpy as np
            clauses = re.findall(r"[^।.!?\\n]+[।.!?]?", text)
            clauses = [c.strip() for c in clauses if c.strip()]
            if not clauses:
                raise ValueError("No readable sentences found")
            rate = int(model.config.sampling_rate)
            pause_ms = {"Inspirational": 480, "Calm": 600, "Neutral": 220}[delivery]
            pieces = []
            for i, clause in enumerate(clauses):
                self.set_status(f"Generating sentence {i + 1}/{len(clauses)}...")
                inputs = tokenizer(clause, return_tensors="pt")
                with torch.no_grad():
                    chunk = model(**inputs).waveform[0].cpu().numpy()
                pieces.append(chunk)
                if i < len(clauses) - 1:
                    extra = 200 if clause.endswith(("!", "?", "।")) and delivery == "Inspirational" else 0
                    pieces.append(np.zeros(int(rate * (pause_ms + extra) / 1000), dtype=np.float32))
            self.audio = np.concatenate(pieces)
            self.sample_rate = rate
            self.set_status("Audio ready. Click Save WAV.")
        except Exception as exc:
            self.set_status("Error: " + str(exc))
        finally:
            self.after(0, lambda: self.generate_btn.config(state="normal"))

    def save(self):
        if self.audio is None:
            messagebox.showinfo("No audio", "Generate audio first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Audio", "*.wav")])
        if path:
            import numpy as np
            from scipy.io.wavfile import write
            pcm = (np.clip(self.audio, -1, 1) * 32767).astype(np.int16)
            write(path, self.sample_rate, pcm)
            self.status.set("Saved: " + str(Path(path)))

if __name__ == "__main__":
    Lite().mainloop()
