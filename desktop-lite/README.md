# Bangla Voice Studio Lite (Windows)
This is a **separate offline neural TTS edition** for Windows 10/11, targeting CPU machines with 16 GB RAM.

- Bengali model: [facebook/mms-tts-ben](https://huggingface.co/facebook/mms-tts-ben)
- English model: [facebook/mms-tts-eng](https://huggingface.co/facebook/mms-tts-eng)
- No paid API, no server URL.
- **First use requires internet** to download model files from Hugging Face; subsequent uses can work offline from the local cache.
- Model licenses and voice quality should be reviewed before redistribution or commercial use. MMS model license is CC-BY-NC 4.0 (non-commercial).
- Naturalness is not guaranteed. This edition does **not** clone voices.
- CPU generation may be slow; long paragraphs may need splitting into shorter sentences.

## Run from source
Install Python 3.11, then:
```powershell
pip install -r desktop-lite/requirements.txt
python desktop-lite/main.py
```

## Windows EXE
GitHub Actions workflow **Build Windows Lite EXE** packages the client and its runtime dependencies. Download its artifact from the Actions tab after a successful build. Model weights are not included; the first launch requires internet.
