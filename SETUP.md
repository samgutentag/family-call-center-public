# Setup (Raspberry Pi)

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
# Fill in .env: Twilio creds, BASE_URL (Funnel host), TAILNET_HOSTNAME,
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

### Tailscale notes (still used for the private inbox)
- `tailscale up` must show **logged in** (`tailscale status`); the menu-bar app
  being signed in does not guarantee the CLI daemon is.
- With Tailscale, **the Funnel public URL and the tailnet MagicDNS name are the
  same hostname**. The inbox `Host` gate therefore cannot distinguish public
  Funnel traffic from private tailnet traffic on its own. If you serve the inbox
  over the tailnet, do **not** also Funnel `/` publicly. Safe options: leave
  `TAILNET_HOSTNAME` blank to disable the inbox during a webhook-only test, or
  reach the inbox locally with `TAILNET_HOSTNAME=localhost` and
  `http://localhost:8080/`.
- First-time Funnel must be enabled once per tailnet; `tailscale funnel` prints
  a `login.tailscale.com/f/funnel?...` link to click.

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
