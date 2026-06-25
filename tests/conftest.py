import os
import tempfile

# Dummy env MUST be set before importing config/app (import-time require_env).
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-token")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15550000000")
os.environ.setdefault("BASE_URL", "https://funnel.example.ts.net")
os.environ.setdefault("TWILIO_VALIDATION_ENABLED", "false")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("TAILNET_HOSTNAME", "pi.tailtest.ts.net")
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="ivr-test-"))

import pytest
from app import create_app


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
