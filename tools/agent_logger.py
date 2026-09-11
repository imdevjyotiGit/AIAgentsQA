"""
tools/agent_logger.py
Shared file logger for the Intelligent Test Planning Agent.

Every tool module logs through here so that a failed run leaves a single,
timestamped trail on disk instead of a one-line message in the browser. The
log file is the first thing to read when generation fails.

Log location: <project_root>/logs/agent.log
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# <project_root>/logs/agent.log  (tools/ -> project root)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent.log")

_configured = False


def get_logger(name="agent"):
    """
    Returns a logger that writes to both the log file and the console.

    Handlers are attached once per process; repeated calls return the same
    configured logger rather than stacking duplicate handlers (which would
    otherwise write every line N times).
    """
    global _configured

    logger = logging.getLogger(name)

    if not _configured:
        os.makedirs(LOG_DIR, exist_ok=True)

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)-16s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Rotate so a long-running server can't fill the disk with log data.
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(fmt)

        root.addHandler(file_handler)
        root.addHandler(console)

        _configured = True
        root.info("=" * 78)
        root.info("Logging initialised -> %s", LOG_FILE)

    return logger


def log_payload(logger, label, text, limit=4000):
    """
    Logs a potentially large payload (prompt or raw model output), truncated.

    Model output is the single most useful artifact when JSON parsing fails,
    so it is recorded even on the success path at DEBUG level.
    """
    if text is None:
        logger.debug("%s: <None>", label)
        return
    text = str(text)
    if len(text) > limit:
        logger.debug(
            "%s (%d chars, showing first %d):\n%s\n...[truncated %d chars]...",
            label, len(text), limit, text[:limit], len(text) - limit
        )
    else:
        logger.debug("%s (%d chars):\n%s", label, len(text), text)
