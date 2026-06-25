# Family Call Center

> **Note:** This repository is unmaintained, unsupported, and shared as-is as untested example code.

A kid's landline built on a Raspberry Pi. When a caller dials your Twilio number they hear a warm, slowed voice (Deepgram Aura) ask them to press 1 or 2. Press 1 and they leave a voicemail: the recording saves to the Pi, Deepgram transcribes it, and a Pushover notification with the transcript lands on a parent's phone. Press 2 and they hear today's weather as a kid-friendly spoken line (date, a goofy weather joke, what to wear to school or on a weekend, jacket/sunscreen/rain flags, morning and afternoon temps), played twice then a friendly hang-up, with the same text texted to the parent. Voicemails are browsable on a private tailnet-only inbox page. Voice prompts are cached mp3s; if Deepgram is unavailable the app falls back to Twilio's built-in voice automatically.

![What happens when you call](docs/assets/call-flow.svg)

---

## Features

- Press 1 leaves a voicemail, saves it to the Pi, transcribes it with Deepgram nova-3, and fires a Pushover notification with the transcript
- Press 2 reads a kid-friendly daily weather line (built from Open-Meteo, no API key needed) then hangs up politely; parent gets the text too
- Warm, slowed voice via Deepgram Aura (configurable model and speed); Twilio built-in voice is the automatic fallback
- Pushover pings on every voicemail and weather check
- Private voicemail inbox accessible only over your Tailscale tailnet
- Edit outfit rules, temperature bands, and goofy jokes in `config/wardrobe.yml` without touching Python

---

## How it works

### The voice

Voice prompts are synthesized once by Deepgram Aura, time-stretched by ffmpeg at your chosen `SPEECH_RATE` (pitch is preserved), and cached as mp3s under `data/audio/`. Twilio fetches them at `/audio/<file>`. Static prompts warm at startup; the daily weather line renders on the scheduler run. If `DEEPGRAM_API_KEY` is empty, the app falls back to Twilio's built-in `<Say>` verb.

![How the voice is made](docs/assets/voice-pipeline.svg)

### The weather

Once a day (default 4am, configurable in `config/wardrobe.yml`), the scheduler pulls an Open-Meteo hourly forecast, selects morning and afternoon temperature windows, applies wardrobe rules from `config/wardrobe.yml` and school-day overrides from `config/day_overrides.yml`, picks a goofy weather joke, and renders a single spoken sentence. That sentence is synthesized into a cached mp3 and is ready before the first call of the day.

![The morning weather](docs/assets/weather-build.svg)

### Privacy and the inbox

Twilio's webhooks arrive over a Cloudflare Tunnel at a public URL. The voicemail inbox is a separate door: it only responds to requests whose `Host` header matches `TAILNET_HOSTNAME`, so it stays invisible to the public tunnel. Reach it from any device on your Tailscale tailnet at `http://<TAILNET_HOSTNAME>:8080/`.

![One app, two doors](docs/assets/trust-zones.svg)

---

## Quick start (fresh clone)

```bash
git clone <your-repo-url> family-call-center && cd family-call-center
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Install the system dependency for the voice slowdown:

```bash
# macOS
brew install ffmpeg
# Raspberry Pi / Debian
sudo apt install ffmpeg
```

Copy and fill in the environment file:

```bash
cp .env.template .env
# then open .env and fill in your keys (see "Accounts and keys" below)
```

Expose the app publicly so Twilio can reach it. A Cloudflare quick tunnel needs no account:

```bash
cloudflared tunnel --url http://localhost:8080
# prints something like: https://abc-123.trycloudflare.com
```

Put that URL in `.env` as `BASE_URL` (https, no trailing slash), then start the app:

```bash
python run.py   # serves via waitress on 0.0.0.0:8080
```

Finally, in the Twilio console set your phone number's Voice webhook to `<BASE_URL>/call` with method `POST`, then call the number from your phone.

---

## Accounts and keys

| Variable | What it is | Where to get it |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | Account SID (starts with `AC`) | [Twilio console](https://console.twilio.com) home, Account Info card |
| `TWILIO_AUTH_TOKEN` | Auth Token (same card) | Twilio console home |
| `TWILIO_PHONE_NUMBER` | Your Twilio voice number (E.164, e.g. `+15550001234`) | Twilio console, Phone Numbers |
| `BASE_URL` | Public tunnel URL (https, no trailing slash) | Printed by `cloudflared` or your named tunnel config |
| `TAILNET_HOSTNAME` | Tailscale MagicDNS hostname of the Pi, no scheme or port | `tailscale status` |
| `DEEPGRAM_API_KEY` | Single key used for both TTS and STT; leave empty to use Twilio voice only | [console.deepgram.com](https://console.deepgram.com) |
| `DEEPGRAM_TTS_MODEL` | Voice model, e.g. `aura-2-luna-en` | Deepgram TTS docs |
| `DEEPGRAM_STT_MODEL` | Transcription model, default `nova-3` | Deepgram STT docs |
| `SPEECH_RATE` | Playback speed (e.g. `0.85` for slower, child-friendly pace); requires ffmpeg when not `1.0` | Set to taste |
| `PUSHOVER_TOKEN` | App token (30 chars) | [pushover.net](https://pushover.net), your application |
| `PUSHOVER_USER` | User key (30 chars) | pushover.net dashboard |
| `WEATHER_LAT` / `WEATHER_LON` | Your coordinates; kept out of git | Maps / GPS app |
| `WEATHER_PLACE_NAME` | Display name for the location, e.g. `Home` | Your choice |
| `DATA_DIR` | Absolute path where recordings and audio cache are stored | Set to wherever you want data on the Pi |
| `FLASK_SECRET_KEY` | Random string; generate with `python3 -c "import secrets; print(secrets.token_hex(24))"` | Self-generated |

Open-Meteo requires no API key.

---

## Stumbling blocks (learned the hard way)

**Use the Account SID, not a Phone Number SID or API Key SID.** The Account SID starts with `AC` and lives on the Twilio console home dashboard. If you paste a `PN` (Phone Number SID) or `SK` (API Key SID) instead, calls may connect but recording downloads will fail silently.

**Upgrade your Twilio account off the trial before letting the family call.** On a Trial account only verified caller IDs can reach your number, and every call opens with a Twilio trial notice. Adding a payment method switches you to pay-as-you-go (roughly a dollar a month for the number plus a few pennies per call), and then any caller can reach the line.

**ffmpeg is required when `SPEECH_RATE` is not `1.0`.** Without it the app logs a warning and serves normal-speed audio; it does not crash. Install it before setting a slowdown value.

**Use Cloudflare Tunnel for the Twilio-facing webhook, not Tailscale Funnel.** Tailscale Funnel returned intermittent HTTP 502s on Twilio's webhook POSTs in testing. Cloudflare Tunnel handled the same traffic without issues. For a stable URL across Pi restarts, set up a named Cloudflare tunnel rather than the quick tunnel (whose URL is temporary).

**Run the app with `run.py`, not Flask's dev server.** `run.py` uses waitress. Twilio's webhook POSTs carry `Expect: 100-continue`; the Flask dev server mishandles this through a tunnel and the edge returns 502. waitress handles it correctly.

**`BASE_URL` must exactly match the public host** (https scheme, no trailing slash). If it drifts from what Twilio actually called, Twilio's request signature validation fails and the app returns 403.

**`PUSHOVER_USER` is your 30-character user key**, not a device name. Find it on the pushover.net dashboard under your account.

Full troubleshooting with copy-paste CLI commands for the Twilio debugger, Pushover validation, and webhook updates lives in [`SETUP.md`](SETUP.md).

---

## Docs

- [`docs/user-guide.html`](docs/user-guide.html) - read-cold, illustrated guide; open in a browser
- [`SETUP.md`](SETUP.md) - Raspberry Pi setup walkthrough, systemd service, and detailed troubleshooting

---

## Why this repo exists

This repo is a lightweight public wrapper around a personal project so people can see the rough implementation. A link to the full write-up will appear here once it is published.

---

## Project status and disclaimers

- This project is shared as an **example/sketch**, not production-ready software.
- I am **not providing support** for this repository.
- The code is **lightly tested / untested in many environments**.
- Reuse or adapt it at your own risk.
- Treat this as a starting point for experimentation, not a maintained package.
