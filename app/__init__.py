import logging
import time
from flask import Flask, jsonify
from config import Config

START_TIME = time.time()


def create_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from app.routes.ivr import ivr_bp
    from app.routes.voicemail import voicemail_bp
    from app.routes.weather import weather_bp
    from app.routes.inbox import inbox_bp
    from app.routes.audio import audio_bp

    app.register_blueprint(ivr_bp)
    app.register_blueprint(voicemail_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(inbox_bp)
    app.register_blueprint(audio_bp)

    @app.get("/health")
    def health():
        uptime_seconds = int(time.time() - START_TIME)
        return jsonify({"status": "ok", "uptime_seconds": uptime_seconds})

    if Config.SCHEDULER_ENABLED:
        from app.services import scheduler
        scheduler.start(app)

    if Config.SCHEDULER_ENABLED and Config.DEEPGRAM_API_KEY:
        from app.services import voice
        voice.start_warmup()

    return app
