from config.observability import REDACTED, before_send, init_error_tracking


class TestDisabledByDefault:
    def test_no_dsn_means_no_tracking(self):
        assert init_error_tracking(dsn="", environment="test") is False

    def test_none_dsn_means_no_tracking(self):
        assert init_error_tracking(dsn=None, environment="test") is False

    def test_the_project_runs_with_tracking_off(self, settings):
        assert settings.ERROR_TRACKING_ENABLED is False


class TestScrubbing:
    def test_the_authorization_header_is_removed(self):
        event = {"request": {"headers": {"Authorization": "Bearer secret-token"}}}

        scrubbed = before_send(event, None)

        assert scrubbed["request"]["headers"]["Authorization"] == REDACTED
        assert "secret-token" not in str(scrubbed)

    def test_cookies_are_removed_wholesale(self):
        event = {"request": {"cookies": {"pc_refresh": "a-real-refresh-token"}}}

        scrubbed = before_send(event, None)

        assert scrubbed["request"]["cookies"] == REDACTED
        assert "a-real-refresh-token" not in str(scrubbed)

    def test_passwords_in_a_body_are_removed(self):
        event = {
            "request": {"data": {"email": "painter@example.com", "password": "hunter2"}}
        }

        scrubbed = before_send(event, None)

        assert scrubbed["request"]["data"]["password"] == REDACTED
        assert "hunter2" not in str(scrubbed)

    def test_reset_fields_are_removed(self):
        event = {
            "request": {
                "data": {
                    "current_password": "old-one",
                    "new_password": "new-one",
                    "token": "reset-token",
                }
            }
        }

        scrubbed = str(before_send(event, None))

        assert "old-one" not in scrubbed
        assert "new-one" not in scrubbed
        assert "reset-token" not in scrubbed

    def test_the_provider_token_is_removed(self):
        event = {"extra": {"hf_token": "hf_a_real_looking_token_value"}}

        scrubbed = before_send(event, None)

        assert "hf_a_real_looking_token_value" not in str(scrubbed)

    def test_scrubbing_reaches_nested_values(self):
        event = {"extra": {"outer": {"inner": {"password": "hunter2"}}}}

        scrubbed = before_send(event, None)

        assert scrubbed["extra"]["outer"]["inner"]["password"] == REDACTED

    def test_scrubbing_reaches_into_lists(self):
        event = {"extra": {"items": [{"password": "hunter2"}, {"safe": "keep"}]}}

        scrubbed = before_send(event, None)

        assert scrubbed["extra"]["items"][0]["password"] == REDACTED
        assert scrubbed["extra"]["items"][1]["safe"] == "keep"

    def test_breadcrumb_data_is_scrubbed(self):
        event = {"breadcrumbs": {"values": [{"data": {"authorization": "Bearer x"}}]}}

        scrubbed = before_send(event, None)

        assert scrubbed["breadcrumbs"]["values"][0]["data"]["authorization"] == REDACTED

    def test_matching_is_case_insensitive(self):
        event = {"request": {"headers": {"AUTHORIZATION": "Bearer x", "CoOkIe": "y"}}}

        scrubbed = before_send(event, None)

        assert scrubbed["request"]["headers"]["AUTHORIZATION"] == REDACTED
        assert scrubbed["request"]["headers"]["CoOkIe"] == REDACTED

    def test_harmless_fields_survive(self):
        event = {
            "request": {
                "headers": {"User-Agent": "Firefox", "Accept": "application/json"}
            },
            "extra": {"image_id": 42, "duration_ms": 120},
        }

        scrubbed = before_send(event, None)

        assert scrubbed["request"]["headers"]["User-Agent"] == "Firefox"
        assert scrubbed["extra"]["image_id"] == 42

    def test_an_event_with_no_request_passes_through(self):
        event = {"message": "something happened"}
        assert before_send(event, None) == event
