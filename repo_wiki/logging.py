from __future__ import annotations

import json
import logging
from typing import Any


LOGGER = logging.getLogger("repo_wiki")


def log_event(event: str, **fields: Any) -> None:
    LOGGER.info(json.dumps({"event": event, **fields}, sort_keys=True, default=str))
