from unittest.mock import Mock, patch

from creator_moderation import InfraiImageClient, ModerationRequest, ModerationResult, moderate_submission


class FakeClient:
    def __init__(self):
        self.calls = []

    def upload(self, content, filename):
        self.calls.append((content, filename))
        return {"id": "img_123"}


def test_high_risk_upload_is_rejected_after_upload():
    client = FakeClient()
    result = moderate_submission(ModerationRequest("sub_7", "launch.png", b"pixels", 0.91), client)
    assert result == ModerationResult("sub_7", "img_123", "rejected", "risk score is above the publishing threshold")
    assert client.calls == [(b"pixels", "launch.png")]


@patch("creator_moderation.time.sleep")
def test_upload_sends_json_and_retries_rate_limit(sleep):
    rate_limited = Mock(
        status_code=429,
        headers={"Retry-After": "0.5"},
        json=Mock(return_value={"ok": False, "error": {"code": "RATE_LIMITED"}}),
    )
    uploaded = Mock(status_code=200, headers={}, json=Mock(return_value={"ok": True, "data": {"id": "img_123"}}))
    session = Mock()
    session.request.side_effect = [rate_limited, uploaded]

    result = InfraiImageClient("test-key", session).upload(b"pixels", "launch.png")

    assert result == {"id": "img_123"}
    assert session.request.call_count == 2
    assert session.request.call_args.kwargs["json"] == {"file": "cGl4ZWxz", "filename": "launch.png"}
    assert "files" not in session.request.call_args.kwargs
    assert "data" not in session.request.call_args.kwargs
    sleep.assert_called_once_with(0.5)
