# Deploy to a Raspberry Pi (durable)

This is the setup that runs unattended: a stable public URL that survives reboots, the private inbox on your tailnet, and everything under `systemd` so a power cut self-heals. It is the production version of the quick-tunnel walkthrough in [`SETUP.md`](SETUP.md). If you just want to test a call from your laptop, start there instead.

What you end up with:

- A caller dials your Twilio number. Twilio webhooks a **named Cloudflare tunnel** at a fixed hostname (e.g. `callcenter.example.com`) that forwards to the app on the Pi.
- The named tunnel keeps the **same URL across reboots**, so the Twilio webhook never goes stale (the quick tunnel's URL changes every restart, which is the failure this fixes).
- The voicemail **inbox** is reachable only over your **Tailscale** tailnet, never the public URL.
- `family-ivr` and `cloudflared` run as `systemd` services, enabled on boot.

## Prerequisites

- A Raspberry Pi on your network, SSH access, and `sudo`.
- A Twilio number with Voice (see [`SETUP.md`](SETUP.md) step 1 for which SID to use).
- A Cloudflare account with a domain (zone) you control, for the named tunnel.
- A Tailscale account, for the private inbox.

All commands below run on the Pi over SSH.

## 1. Base packages

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv python3-pip ffmpeg curl
```

`ffmpeg` is what slows the voice for a child (`SPEECH_RATE`); the app still runs without it, just at normal speed.

## 2. Clone, build the venv, fill `.env`

```bash
cd ~
git clone https://github.com/samgutentag/family-call-center-public.git
cd family-call-center-public
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.template .env
```

Fill `.env` (the app loads it automatically via `python-dotenv`). Set these now:

- Twilio creds, `PUSHOVER_*`, `DEEPGRAM_API_KEY`, `WEATHER_LAT/LON/PLACE_NAME`, `FLASK_SECRET_KEY`.
- `DATA_DIR=/home/pi/family-call-center-public/data`
- `SCHEDULER_ENABLED=true` (so the 4am weather refresh runs on the durable host).
- Leave `BASE_URL` and `TAILNET_HOSTNAME` for now; you set them in steps 3 and 4.

## 3. Tailscale (the private inbox)

```bash
curl -fsSL https://tailscale.com/install.sh | sudo sh
sudo tailscale up --hostname=devbox-pi-1 --accept-dns=true
```

`tailscale up` prints a `login.tailscale.com/a/...` URL. Open it and approve the machine into your tailnet. Then read the Pi's MagicDNS name:

```bash
tailscale status --json | python3 -c "import sys,json; print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))"
# e.g. devbox-pi-1.tailXXXX.ts.net
```

Put that in `.env` as `TAILNET_HOSTNAME` (no scheme, no port). The inbox will answer only on that hostname.

```bash
sed -i "s|^TAILNET_HOSTNAME=.*|TAILNET_HOSTNAME=devbox-pi-1.tailXXXX.ts.net|" .env
```

## 4. cloudflared named tunnel (the public ingress)

Install cloudflared (arm64 Pi):

```bash
curl -fsSL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i /tmp/cloudflared.deb && rm /tmp/cloudflared.deb
```

Authorize, create the tunnel, and route a hostname to it:

```bash
cloudflared tunnel login                                   # opens a browser; pick your zone
cloudflared tunnel create family-call-center               # writes ~/.cloudflared/<UUID>.json
cloudflared tunnel route dns family-call-center callcenter.example.com
```

`cloudflared tunnel create` prints the tunnel **UUID** and the path to its credentials file. Use both in the config:

```bash
sudo mkdir -p /etc/cloudflared
sudo tee /etc/cloudflared/config.yml >/dev/null <<'EOF'
tunnel: <UUID>
credentials-file: /home/pi/.cloudflared/<UUID>.json
no-autoupdate: true
ingress:
  - hostname: callcenter.example.com
    service: http://localhost:8080
  - service: http_status:404
EOF
```

Set `BASE_URL` to the tunnel hostname (https, no trailing slash). It must match exactly or Twilio's signature check returns 403:

```bash
sed -i "s|^BASE_URL=.*|BASE_URL=https://callcenter.example.com|" ~/family-call-center-public/.env
```

## 5. Both services under systemd

The app service (the repo ships a template with `REPLACE_WITH_PI_USER`):

```bash
sed "s/REPLACE_WITH_PI_USER/pi/g" ~/family-call-center-public/deploy/family-ivr.service \
  | sudo tee /etc/systemd/system/family-ivr.service >/dev/null
```

The tunnel service:

```bash
sudo tee /etc/systemd/system/cloudflared.service >/dev/null <<'EOF'
[Unit]
Description=cloudflared tunnel for family-call-center
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/cloudflared --config /etc/cloudflared/config.yml --no-autoupdate tunnel run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start both:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared family-ivr
```

## 6. Point Twilio at the stable URL

In the Twilio console, set the number's Voice webhook to `POST https://callcenter.example.com/call`. Or from the CLI (see [`SETUP.md`](SETUP.md) for the full snippet):

```bash
set -a; . ~/family-call-center-public/.env; set +a
PNSID=$(curl -s -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers.json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['incoming_phone_numbers'][0]['sid'])")
curl -s -X POST -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers/$PNSID.json" \
  --data-urlencode "VoiceUrl=$BASE_URL/call" --data-urlencode "VoiceMethod=POST"
```

## 7. Verify, then prove it is durable

```bash
# services up
systemctl is-active family-ivr cloudflared tailscaled
# local and public health
curl -s http://localhost:8080/health
curl -s https://callcenter.example.com/health
```

Two-door check: the inbox should answer on the tailnet and 404 on the public URL.

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://devbox-pi-1.tailXXXX.ts.net:8080/   # expect 200
curl -s -o /dev/null -w '%{http_code}\n' https://callcenter.example.com/             # expect 404
```

Then reboot and confirm it comes back with no hands:

```bash
sudo reboot
# wait a minute, then:
curl -s https://callcenter.example.com/health   # ok again, served by systemd
```

Call the number, press 1 (voicemail) and 2 (weather). Open the inbox from a phone on your tailnet. Done.

## Notes

- **Updating the code:** `cd ~/family-call-center-public && git pull && ./.venv/bin/pip install -r requirements.txt && sudo systemctl restart family-ivr`.
- **Logs:** `journalctl -u family-ivr -f` and `journalctl -u cloudflared -f`.
- **DHCP drift:** give the Pi a reservation on your router so its LAN IP stops moving. The public URL and the tailnet name do not change regardless.
- Troubleshooting (Twilio 502s, signature 403s, Pushover 400s) lives in [`SETUP.md`](SETUP.md).
