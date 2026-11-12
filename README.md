# Bangla Voice Studio

Android client for a self-hosted, open-source Bengali/English text-to-speech and consent-based voice-cloning API.

## Build APK
Open the **Actions** tab, select **Build Android APK**, run the workflow, then download the `BanglaVoiceStudio-debug-apk` artifact.

## Important
This APK is a client, **not** an AI server. Enter the URL of a server implementing `POST /synthesize` (JSON: `text`, `lang`) and `POST /clone` (multipart speaker_wav and query text/lang). No paid API is built into the app, but hosting and compute may cost money. Bengali voice quality and cloning require a compatible server and model. Use only voices you own or have permission to clone.
