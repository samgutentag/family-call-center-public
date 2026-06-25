import os

from waitress import serve

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Serve with waitress (a production WSGI server) rather than Flask's
    # development server. Tailscale Funnel / Cloudflare tunnels send Twilio's
    # webhook POSTs with "Expect: 100-continue", which the dev server mishandles
    # through a tunnel (the edge returns 502). waitress handles it correctly.
    serve(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
