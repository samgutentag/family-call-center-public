# Family Call Center (Public)
> **Note:** This repository is unmaintained, unsupported, and shared as-is as untested example code.
This is a small Flask + Twilio phone app for a kid's landline.
When a caller reaches `/call`, they hear a short menu:
- Press **1** to leave a voicemail.
- Press **2** to hear the local weather read aloud.

Voicemail audio is stored under `data/recordings/YYYY/MM/DD/`, logged in `data/ivr.db`, then deleted from Twilio so the Pi holds the only copy. A Pushover notification fires on a new voicemail (and on a weather check). Recordings are browsable from a small web inbox that is gated to your Tailscale tailnet and hidden from the public Funnel that Twilio uses.

## User guide
A read-cold, illustrated guide lives at [`docs/user-guide.html`](docs/user-guide.html) (open it in a browser). Setup steps are in [`SETUP.md`](SETUP.md).

## Why this repo exists
This repo is a lightweight public wrapper around my personal project so people can see the rough implementation.
I’ll add a link to the full write-up here once it’s published.

## Project status and disclaimers
- This project is shared as an **example/sketch**, not production-ready software.
- I am **not providing support** for this repository.
- The code is **lightly tested / untested in many environments**.
- Reuse or adapt it at your own risk.
- Treat this as a starting point for experimentation, not a maintained package.

## Setup
1. Copy the environment template:
```bash
cp .env.template .env
```
2. Fill in values in `.env`.
3. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
4. Run the app:
```bash
python run.py
```

## Twilio webhook
In Twilio phone number settings:
- Voice webhook URL: `https://your-public-hostname.example.com/call`
- Method: `POST`

## Endpoints
- `POST /call` — main menu (Press 1 for voicemail)
- `POST /call/route` — routes keypad selection
- `POST /voicemail` — starts recording
- `POST /voicemail/done` — thanks caller and hangs up
- `POST /voicemail/callback` — receives recording callback and saves audio
- `GET /health` — basic health check

## Optional macOS service files
Template files are included:
- `com.family.ivr.plist`
- `family-ivr.newsyslog.conf`

Replace placeholder paths before using them.