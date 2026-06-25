# Setup (Raspberry Pi)

> **Deploying durably on a Pi?** Use [`DEPLOY.md`](DEPLOY.md). It sets up a named
> Cloudflare tunnel (stable URL across reboots), Tailscale, and `systemd` services
> so the line self-heals after a power cut. This page is the quick-tunnel test path
> (good for a first call from your laptop) and the troubleshooting reference.

## 1. Twilio
- Buy a phone number (with **Voice**) in the [Twilio console](https://console.twilio.com).
- Credentials for `.env` come from the **Account Info** card on the console home
  dashboard: the **Account SID** (starts with `AC`) and the **Auth Token**.
  - Do **not** use the Phone Number SID (starts with `PN`) or an API Key SID
    (starts with `SK`). The app authenticates with the Account SID + Auth Token.
- Set the number's Voice webhook (**A call comes in → Webhook**) to
  `POST <BASE_URL>/call`, where `BASE_URL` is your tunnel URL from step 3.

## 2. Code + environment
```bash
git clone <your-repo> family-call-center-public
cd family-call-center-public
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Fill in .env: Twilio creds, BASE_URL (tunnel host), TAILNET_HOSTNAME,
# PUSHOVER_*, WEATHER_LAT/LON/PLACE_NAME, DATA_DIR.
```

## 3. Public ingress (so Twilio can reach the app)

Twilio needs a public HTTPS URL that forwards to the app on `localhost:8080`.

> **Recommended: Cloudflare Tunnel.** In testing, **Tailscale Funnel was
> unreliable for Twilio's webhooks** (intermittent HTTP 502 at the Funnel edge
> on Twilio's POSTs, even with a production server). Cloudflare Tunnel handled
> the same traffic cleanly. A quick tunnel needs no account:
> ```bash
> cloudflared tunnel --url http://localhost:8080
> # prints https://<random>.trycloudflare.com  -> use as BASE_URL
> ```
> For a stable URL on the Pi, set up a named Cloudflare tunnel (persists across
> restarts) instead of the quick tunnel. ngrok works too.

`BASE_URL` must be **exactly** the public host the tunnel gives you (https, no
trailing slash) or Twilio's request signature will not validate (you'll get
403s).

### Tailscale notes (the private inbox)
- `tailscale up` must show **logged in** (`tailscale status`); the menu-bar app
  being signed in does not guarantee the CLI daemon is.
- Set `TAILNET_HOSTNAME` to the Pi's MagicDNS name (e.g.
  `devbox-pi-1.tailXXXX.ts.net`) and open the inbox at
  `http://<TAILNET_HOSTNAME>:8080/` from any device on your tailnet. The `Host`
  gate 404s that same path on the public URL.
- For a laptop-only test with no tailnet, set `TAILNET_HOSTNAME=localhost` and
  reach the inbox at `http://localhost:8080/`.
- Putting the public door on **Cloudflare** and the private door on **Tailscale**
  means they are different hostnames, so the `Host` gate tells them apart cleanly.
  Tailscale **Funnel** would make the public URL and the tailnet name identical and
  the gate could not separate them, which is why the durable setup uses Cloudflare
  for the public side. See [`DEPLOY.md`](DEPLOY.md).

## 4. Run as a service
```bash
sudo cp deploy/family-ivr.service /etc/systemd/system/
# Edit the file: replace REPLACE_WITH_PI_USER and paths.
sudo systemctl daemon-reload
sudo systemctl enable --now family-ivr
systemctl status family-ivr
```

> **Server:** `run.py` serves the app with **waitress** (a production WSGI
> server), not Flask's development server. This matters: tunnels forward
> Twilio's webhook POSTs (which carry `Expect: 100-continue`) in a way the dev
> server mishandles, so the dev server returns 502 through a tunnel. waitress
> handles it. `run.py` defaults `HOST=0.0.0.0`; set `HOST=127.0.0.1` to bind
> loopback only. The inbox stays private regardless via the `Host` gate.

## 5. Verify
- Local: `curl http://localhost:8080/health`
- Public: `curl <BASE_URL>/health` (confirms the tunnel reaches the app from
  outside; on a tunnel's first start the TLS cert can take ~30-60s).
- Call the Twilio number: press 1 (voicemail), press 2 (weather).
- Inbox: open `http://<TAILNET_HOSTNAME>:8080/` from the matching host.

## Troubleshooting (gotchas we actually hit)

**Caller hears "an application error has occurred."** This means your webhook
returned an error or was unreachable; it is not a trial-account limit (trial
accounts still run your menu after a short notice). Find the real cause in
Twilio's debugger:
```bash
curl -s -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  "https://monitor.twilio.com/v1/Alerts?PageSize=5"
```
- **Error 11200, "Got HTTP 502"** → the tunnel reached a server that mishandled
  Twilio's POST. Use waitress (not the Flask dev server) and prefer Cloudflare
  Tunnel over Tailscale Funnel. See step 3.
- **403 in the app log ("invalid Twilio signature")** → `BASE_URL` does not
  exactly match the host Twilio called. Fix `BASE_URL` (https, no trailing
  slash) and restart.

**Read or change the number's webhook from the CLI** (no console needed):
```bash
# read current voice webhook
curl -s -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers.json?PhoneNumber=%2B1XXXXXXXXXX"
# update it (PNSID is the incoming-number SID from the call above)
curl -s -X POST -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers/<PNSID>.json" \
  --data-urlencode "VoiceUrl=<BASE_URL>/call" --data-urlencode "VoiceMethod=POST"
```

**Pushover notifications return HTTP 400.** Validate the credentials:
```bash
curl -s -X POST https://api.pushover.net/1/users/validate.json \
  --data-urlencode "token=$PUSHOVER_TOKEN" --data-urlencode "user=$PUSHOVER_USER"
```
- `"user key is invalid"` → `PUSHOVER_USER` must be your **30-character User
  Key** from the pushover.net dashboard, not a device name. The app token
  (`PUSHOVER_TOKEN`) is also 30 chars.
- Notifications are best-effort: a Pushover failure is logged and swallowed, and
  never breaks the recording or the call.

**`.env` notes.** `cp .env.template .env` overwrites the file, so re-fill it
after copying: `DATA_DIR` must be an absolute path, `FLASK_SECRET_KEY` a real
random string (`python3 -c "import secrets; print(secrets.token_hex(24))"`).
Values with spaces (e.g. `WEATHER_PLACE_NAME`) can be quoted; `python-dotenv`
strips the quotes.

## Weather and wardrobe rules

Press 2 reads a pre-computed clothing instruction, refreshed on a schedule.

- Edit `config/wardrobe.yml` to tune the outfit bands (school vs weekend),
  the UV / morning-jacket / rain thresholds, the morning/afternoon hour
  windows, and the `schedule` (an array of cron expressions, e.g.
  `"0 4 * * *"` for 4am). Ships with one 4am refresh; add more lines for more.
- Edit `config/day_overrides.yml` to mark school-calendar exceptions, e.g.
  `2026-09-07: weekend` for a holiday.
- Restart the service to pick up schedule changes
  (`sudo systemctl restart family-ivr`).
- The forecast comes from Open-Meteo (free, no API key); set `WEATHER_LAT`
  and `WEATHER_LON` in `.env`.

## Voice (Deepgram, optional)

The phone speaks with a Deepgram Aura voice when `DEEPGRAM_API_KEY` is set,
otherwise it falls back to Twilio's built-in voice (the app works either way).

- Set `DEEPGRAM_API_KEY` in `.env`. Pick a voice with `DEEPGRAM_TTS_MODEL`
  (default `aura-2-andromeda-en`); change the string to audition others.
- Prompts are synthesized once and cached under `data/audio/` (content-addressed
  by text), so each line is generated at most once. The daily weather line is
  rendered by the scheduler; the fixed prompts are warmed at startup.
- The mp3s are served publicly at `/audio/<file>` so Twilio can fetch them; only
  prompt/weather audio lives there (never voicemail recordings).
- The cache grows slowly: the static prompts are a fixed handful, but the daily weather line adds
  roughly one small mp3 per day under `data/audio/`; prune old files manually if it ever matters.
- Slow the voice for a child with `SPEECH_RATE` in `.env` (e.g. `0.85`). This
  time-stretches the audio with **ffmpeg** (pitch preserved), so install it on
  the Pi: `sudo apt install ffmpeg`. At `SPEECH_RATE=1.0` ffmpeg isn't used; if
  it's missing while a slowdown is set, the app logs a warning and serves
  normal-speed audio (no crash).
