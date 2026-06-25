import logging

from flask import Blueprint, render_template, send_from_directory

from app.utils.db import list_recordings
from app.utils.tailnet import require_tailnet
from config import Config

logger = logging.getLogger(__name__)
inbox_bp = Blueprint("inbox", __name__)


@inbox_bp.get("/")
@require_tailnet
def inbox():
    return render_template("inbox.html", recordings=list_recordings())


@inbox_bp.get("/recordings/<path:filename>")
@require_tailnet
def serve_recording(filename):
    return send_from_directory(Config.RECORDINGS_DIR, filename)
