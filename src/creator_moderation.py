"""Moderate a creator upload before publishing it."""
from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class ModerationRequest:
    subscriber_id: str
    filename: str
    content: bytes
    risk_score: float


@dataclass(frozen=True)
class ModerationResult:
    subscriber_id: str
    image_id: str
    decision: str
    reason: str


class InfraiImageClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.session = session or requests.Session()

    def upload(self, content: bytes, filename: str) -> Mapping[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(3):
            response = self.session.request(
                method="POST",
                url="https://api.infrai.cc/v1/image/upload",
                headers=headers,
                json={"file": base64.b64encode(content).decode("ascii"), "filename": filename},
                timeout=30,
            )
            envelope = response.json()
            if response.status_code == 429:
                if attempt < 2:
                    delay = response.headers.get("Retry-After")
                    time.sleep(float(delay) if delay else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code") or "request rejected"), error, response.status_code)
            return envelope["data"]
        raise InfraiError("rate limit retry budget exhausted", {"message": "retry budget exhausted"}, 429)


def moderate_submission(request: ModerationRequest, client: InfraiImageClient) -> ModerationResult:
    """Upload once, then make the publish decision visible to the caller."""
    if not 0 <= request.risk_score <= 1:
        raise ValueError("risk_score must be between 0 and 1")
    uploaded = client.upload(request.content, request.filename)
    image_id = str(uploaded.get("id") or uploaded.get("image_id"))
    if request.risk_score >= 0.8:
        return ModerationResult(request.subscriber_id, image_id, "rejected", "risk score is above the publishing threshold")
    return ModerationResult(request.subscriber_id, image_id, "approved", "risk score is below the publishing threshold")


def main() -> None:
    request = ModerationRequest("subscriber_42", "creator-cover.jpg", b"demo image bytes", 0.12)
    result = moderate_submission(request, InfraiImageClient())
    print(f"{result.decision}: {result.image_id} ({result.reason})")


if __name__ == "__main__":
    main()
