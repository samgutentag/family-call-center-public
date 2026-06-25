import logging
from functools import wraps

from flask import abort, request

from config import Config

logger = logging.getLogger(__name__)


def require_tailnet(f):
    """Allow only requests whose Host matches TAILNET_HOSTNAME; else 404.

    404 (not 403) keeps these routes invisible from the public Funnel host.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        host = request.host.split(":")[0]
        allowed = Config.TAILNET_HOSTNAME.split(":")[0] if Config.TAILNET_HOSTNAME else ""
        if not allowed or host != allowed:
            logger.warning("Inbox request rejected for host %r", request.host)
            abort(404)
        return f(*args, **kwargs)

    return decorated
