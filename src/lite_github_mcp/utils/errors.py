from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    details: dict[str, Any]
    retry_after: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
        if self.retry_after is not None:
            payload["retry_after"] = self.retry_after
        return payload


# Canonical codes
GH_NOT_INSTALLED = "GH_NOT_INSTALLED"
GH_NOT_AUTHED = "GH_NOT_AUTHED"
RATE_LIMIT = "RATE_LIMIT"
GH_ERROR = "GH_ERROR"
GIT_ERROR = "GIT_ERROR"
INVALID_INPUT = "INVALID_INPUT"
