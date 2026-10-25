"""Web directory controls without Telegram or desktop side effects."""

import os
import unittest
from types import SimpleNamespace
from unittest import mock

from module import web
from module.app import Application, ChatDownloadConfig


class WebDirectoryTestCase(unittest.TestCase):
    def setUp(self):
        self.application = Application("", "")
        self.application.file_path_prefix = ["chat_title", "media_datetime"]
        self.chat = ChatDownloadConfig()
        self.chat.chat_title = "Example Chat"
        self.application.chat_download_config[-100123] = self.chat
        self.directory = os.path.join(self.application.save_path, "Example Chat")
        self.flask_app = web.get_flask_app()
        self.old_config = dict(self.flask_app.config)
        self.flask_app.config.update(TESTING=True, LOGIN_DISABLED=True)
        self.addCleanup(self.flask_app.config.update, self.old_config)
        self.addCleanup(self.flask_app.config.clear)
        self.client = self.flask_app.test_client()
        for patcher in [
            mock.patch.object(web, "_application", self.application),
            mock.patch.object(web, "_download_client", None),
            mock.patch.object(web, "_chat_title_checks", {}),
            mock.patch("module.web.os.path.isdir", return_value=True),
            mock.patch("module.web.os.name", "nt"),
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)
        opener = mock.patch("module.web.os.startfile", create=True)
        self.open_directory = opener.start()
        self.addCleanup(opener.stop)
        self.addCleanup(self.application.loop.close)
        self.addCleanup(self.application.executor.shutdown)

    def post(self, **kwargs):
        kwargs.setdefault("json", {"chat_id": "-100123"})
        return self.client.post("/open_chat_directory", **kwargs)

    def test_chat_rows_include_title_and_actual_directory(self):
        response = self.client.get("/get_chat_configs")
        row = response.get_json()["data"][0]
        self.assertEqual(row["chat_title"], "Example Chat")
        self.assertEqual(row["chat_id"], "-100123")
        self.assertEqual(row["save_directory"], self.directory)
        self.assertTrue(row["can_open_directory"])
        self.open_directory.assert_not_called()

    def test_open_configured_directory(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 0)
        self.open_directory.assert_called_once_with(
            os.path.realpath(self.directory), "explore"
        )

    def test_browser_supplied_path_is_never_used(self):
        response = self.post(
            json={"chat_id": "-100123", "path": os.path.dirname(self.directory)}
        )
        self.assertEqual(response.status_code, 200)
        self.open_directory.assert_called_once_with(
            os.path.realpath(self.directory), "explore"
        )
        self.open_directory.reset_mock()
        self.assertEqual(self.post(json={"path": self.directory}).status_code, 400)
        self.open_directory.assert_not_called()

    def test_authentication_required(self):
        self.flask_app.config["LOGIN_DISABLED"] = False
        self.assertEqual(self.post().status_code, 302)
        self.open_directory.assert_not_called()

    def test_open_requires_json_post(self):
        self.assertEqual(self.client.get("/open_chat_directory").status_code, 405)
        response = self.client.post("/open_chat_directory", data={"chat_id": "-100123"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "json_required")
        for value in [[], None, {"chat_id": 123}]:
            with self.subTest(value=value):
                self.assertEqual(self.post(json=value).status_code, 400)
        self.open_directory.assert_not_called()

    def test_reject_unknown_chat_and_unready_application(self):
        self.assertEqual(self.post(json={"chat_id": "-100999"}).status_code, 404)
        with mock.patch.object(web, "_application", None):
            self.assertEqual(self.post().status_code, 503)
        self.open_directory.assert_not_called()

    def test_reject_remote_and_cross_origin_opening(self):
        for options in [
            {"environ_overrides": {"REMOTE_ADDR": "192.168.1.20"}},
            {"base_url": "http://attacker.example"},
            {"headers": {"Origin": "https://attacker.example"}},
            {"headers": {"Origin": "http://localhost:9999"}},
            {"headers": {"Sec-Fetch-Site": "cross-site"}},
            {"headers": {"Sec-Fetch-Site": "same-site"}},
        ]:
            with self.subTest(options=options):
                self.assertEqual(self.post(**options).status_code, 403)
        self.open_directory.assert_not_called()

    def test_allow_matching_loopback_origin_and_ipv6(self):
        self.assertEqual(
            self.post(headers={"Origin": "http://localhost"}).status_code, 200
        )
        self.assertEqual(
            self.post(
                base_url="http://[::1]:5000", environ_overrides={"REMOTE_ADDR": "::1"}
            ).status_code,
            200,
        )

    def test_remote_rows_disable_directory_control(self):
        response = self.client.get(
            "/get_chat_configs", environ_overrides={"REMOTE_ADDR": "192.168.1.20"}
        )
        row = response.get_json()["data"][0]
        self.assertFalse(row["can_open_directory"])
        self.assertEqual(row["directory_error"], "local_access_required")

    def test_missing_directory_is_not_created_or_opened(self):
        with mock.patch("module.web.os.path.isdir", return_value=False):
            response = self.post()
        self.assertEqual(response.get_json()["error"], "directory_missing")
        self.open_directory.assert_not_called()

    def test_unknown_title_does_not_guess_id_directory(self):
        self.chat.chat_title = ""
        response = self.client.get("/get_chat_configs")
        row = response.get_json()["data"][0]
        self.assertEqual(row["save_directory"], self.application.save_path)
        self.assertFalse(row["can_open_directory"])
        self.assertEqual(self.post().get_json()["error"], "title_unavailable")
        self.open_directory.assert_not_called()

    def test_reject_directory_and_junction_targets_outside_root(self):
        outside = os.path.abspath("outside_download_root")
        with mock.patch.object(
            self.application, "get_chat_save_path", return_value=outside
        ):
            self.assertEqual(self.post().get_json()["error"], "outside_download_root")
        realpath = os.path.realpath
        with mock.patch(
            "module.web.os.path.realpath",
            side_effect=lambda path: outside
            if path == self.directory
            else realpath(path),
        ):
            self.assertEqual(self.post().get_json()["error"], "outside_download_root")
        self.open_directory.assert_not_called()

    def test_unsupported_platform(self):
        with mock.patch("module.web.os.name", "posix"):
            self.assertEqual(self.post().get_json()["error"], "unsupported_platform")
        self.open_directory.assert_not_called()

    def test_explorer_error_is_reported(self):
        self.open_directory.side_effect = OSError("permission denied")
        response = self.post()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["error"], "open_directory_failed")

    def test_title_lookup_is_throttled_and_not_a_download(self):
        client = SimpleNamespace(is_connected=True)
        with mock.patch.object(web, "_download_client", client), mock.patch.object(
            self.application.loop, "is_running", return_value=True
        ), mock.patch("module.web.asyncio.run_coroutine_threadsafe") as submit:
            submit.side_effect = lambda coroutine, loop: coroutine.close()
            self.client.get("/get_chat_configs")
            self.client.get("/get_chat_configs")
            submit.assert_called_once()
        self.assertEqual(self.chat.total_task, 0)

    def test_title_lookup_handles_success_and_failure(self):
        async def get_chat(chat_id):
            self.assertEqual(chat_id, -100123)
            return SimpleNamespace(title="New Title")

        self.application.loop.run_until_complete(
            web._refresh_chat_title(
                SimpleNamespace(get_chat=get_chat), -100123, self.chat
            )
        )
        self.assertEqual(self.chat.chat_title, "New Title")

        async def failed_chat(_):
            raise OSError("offline")

        self.application.loop.run_until_complete(
            web._refresh_chat_title(
                SimpleNamespace(get_chat=failed_chat), -100123, self.chat
            )
        )
        self.assertEqual(self.chat.chat_title, "New Title")
