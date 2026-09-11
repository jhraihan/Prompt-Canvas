import json
import logging

import pytest
from django.urls import reverse

from config.logging import (
    HEADER,
    JSONFormatter,
    RequestIDFilter,
    get_request_id,
    logging_config,
)


class TestJSONFormatter:
    @staticmethod
    def _record(**kwargs):
        record = logging.LogRecord(
            name=kwargs.pop("name", "promptcanvas.test"),
            level=kwargs.pop("level", logging.INFO),
            pathname=__file__,
            lineno=1,
            msg=kwargs.pop("msg", "hello %s"),
            args=kwargs.pop("args", ("world",)),
            exc_info=kwargs.pop("exc_info", None),
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def test_emits_one_json_object(self):
        line = JSONFormatter().format(self._record())
        payload = json.loads(line)

        assert payload["level"] == "INFO"
        assert payload["logger"] == "promptcanvas.test"
        assert payload["message"] == "hello world"
        assert payload["timestamp"].endswith("Z")

    def test_output_is_a_single_line(self):
        line = JSONFormatter().format(self._record(msg="first\nsecond", args=()))
        assert "\n" not in line

    def test_carries_the_request_id(self):
        record = self._record(request_id="abc123")
        assert json.loads(JSONFormatter().format(record))["request_id"] == "abc123"

    def test_defaults_the_request_id_outside_a_request(self):
        assert json.loads(JSONFormatter().format(self._record()))["request_id"] == "-"

    def test_extra_fields_ride_along(self):
        record = self._record(duration_ms=42, status=201)
        payload = json.loads(JSONFormatter().format(record))
        assert payload["duration_ms"] == 42
        assert payload["status"] == 201

    def test_unserialisable_extras_do_not_break_the_line(self):
        record = self._record(thing=object())
        payload = json.loads(JSONFormatter().format(record))
        assert isinstance(payload["thing"], str)

    def test_includes_a_traceback_when_there_is_one(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = self._record(exc_info=sys.exc_info())

        payload = json.loads(JSONFormatter().format(record))
        assert "ValueError: boom" in payload["exception"]
        assert "\n" not in JSONFormatter().format(record)


class TestRequestIDFilter:
    def test_always_sets_the_attribute(self):
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "m", (), None)
        assert RequestIDFilter().filter(record) is True
        assert hasattr(record, "request_id")


class TestConfig:
    def test_json_output_selects_the_json_formatter(self):
        config = logging_config(json_output=True)
        assert config["handlers"]["console"]["formatter"] == "json"

    def test_plain_output_selects_the_readable_formatter(self):
        config = logging_config(json_output=False)
        assert config["handlers"]["console"]["formatter"] == "verbose"

    def test_every_handler_carries_the_request_id_filter(self):
        config = logging_config(json_output=True)
        for handler in config["handlers"].values():
            assert "request_id" in handler["filters"]


@pytest.mark.django_db
class TestRequestIDMiddleware:
    def test_returns_an_id_on_every_response(self, client):
        response = client.get(reverse("health"))
        assert response[HEADER]
        assert len(response[HEADER]) >= 16

    def test_each_request_gets_a_different_id(self, client):
        first = client.get(reverse("health"))[HEADER]
        second = client.get(reverse("health"))[HEADER]
        assert first != second

    def test_an_inbound_id_is_reused(self, client):
        response = client.get(reverse("health"), headers={"x-request-id": "trace-abc-1"})
        assert response[HEADER] == "trace-abc-1"

    def test_a_hostile_inbound_id_is_sanitised(self, client):
        response = client.get(
            reverse("health"),
            headers={"x-request-id": "abc\ndef INJECTED"},
        )
        assert "\n" not in response[HEADER]
        assert " " not in response[HEADER]

    def test_an_overlong_inbound_id_is_replaced(self, client):
        response = client.get(reverse("health"), headers={"x-request-id": "x" * 500})
        assert len(response[HEADER]) <= 64

    def test_the_id_is_readable_during_the_request(self, client, settings):
        seen = {}

        from images.views import HealthView

        original = HealthView.get

        def capture(self, request):
            seen["id"] = get_request_id()
            seen["on_request"] = getattr(request, "request_id", None)
            return original(self, request)

        HealthView.get = capture
        try:
            response = client.get(reverse("health"))
        finally:
            HealthView.get = original

        assert seen["id"] == response[HEADER]
        assert seen["on_request"] == response[HEADER]

    def test_the_id_does_not_leak_between_requests(self, client):
        client.get(reverse("health"))
        assert get_request_id() == "-"
