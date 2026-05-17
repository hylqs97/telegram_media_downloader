"""test app"""

import os
import sys
import unittest
from unittest import mock

import module.app
from module.app import Application, ChatDownloadConfig, DownloadStatus, parse_file_size
from utils.meta_data import MetaData

sys.path.append("..")  # Adds higher directory to python modules path.


class AppTestCase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        config_test = os.path.join(os.path.abspath("."), "config_test.yaml")
        data_test = os.path.join(os.path.abspath("."), "data_test.yaml")
        if os.path.exists(config_test):
            os.remove(config_test)
        if os.path.exists(data_test):
            os.remove(data_test)

    def test_app(self):
        app = Application("", "")
        self.assertEqual(app.save_path, os.path.join(os.path.abspath("."), "downloads"))
        self.assertEqual(app.proxy, {})
        self.assertEqual(app.restart_program, False)
        self.assertEqual(app.web_auto_start, False)

        app.chat_download_config[123] = ChatDownloadConfig()
        app.chat_download_config[123].last_read_message_id = 13
        app.chat_download_config[123].node.download_status[
            6
        ] = DownloadStatus.Downloading
        app.chat_download_config[123].ids_to_retry.append(7)
        # download success
        app.chat_download_config[123].node.download_status[
            8
        ] = DownloadStatus.SuccessDownload
        app.chat_download_config[123].finish_task += 1
        # download success
        app.chat_download_config[123].node.download_status[
            10
        ] = DownloadStatus.SuccessDownload
        app.chat_download_config[123].finish_task += 1
        # not exist message
        app.chat_download_config[123].node.download_status[
            13
        ] = DownloadStatus.SuccessDownload
        app.config["chat"] = [{"chat_id": 123, "last_read_message_id": 5}]

        app.update_config(False)

        self.assertEqual(
            app.chat_download_config[123].last_read_message_id + 1,
            app.config["chat"][0]["last_read_message_id"],
        )
        self.assertEqual(
            [6, 7],
            app.app_data["chat"][0]["ids_to_retry"],
        )


    def test_assign_config_sort_options(self):
        app = Application("", "")
        config = {
            "api_id": 123,
            "api_hash": "abc",
            "chat": [
                {
                    "chat_id": "test_chat",
                    "sort_by": "views_count",
                    "sort_order": "ASC",
                    "limit": 100,
                }
            ],
            "media_types": ["video"],
            "file_formats": {"audio": ["all"], "video": ["all"], "document": ["all"]},
        }

        app.assign_config(config)

        self.assertEqual(app.chat_download_config["test_chat"].sort_by, "views_count")
        self.assertEqual(app.chat_download_config["test_chat"].sort_order, "asc")
        self.assertEqual(app.chat_download_config["test_chat"].limit, 100)

    def test_get_file_save_path_chat_id_prefix(self):
        app = Application("", "")
        app.save_path = "/root/project"

        self.assertEqual(
            app.get_file_save_path("video", -100123, "2026_05", "Renamed Chat"),
            os.path.join("/root/project", "-100123", "2026_05"),
        )

        app.file_path_prefix = ["chat_title", "media_datetime"]
        self.assertEqual(
            app.get_file_save_path("video", -100123, "2026_05", "Renamed Chat"),
            os.path.join("/root/project", "Renamed Chat", "2026_05"),
        )

    def test_chat_file_size_filter(self):
        app = Application("", "")
        chat_config = ChatDownloadConfig()
        chat_config.file_size_min = parse_file_size("10MB")
        chat_config.file_size_max = parse_file_size("20 MB")

        self.assertEqual(
            app.exec_filter(chat_config, MetaData(media_file_size=9)), False
        )
        self.assertEqual(
            app.exec_filter(chat_config, MetaData(media_file_size=15 * 1024 * 1024)),
            True,
        )
        self.assertEqual(
            app.exec_filter(chat_config, MetaData(media_file_size=21 * 1024 * 1024)),
            False,
        )

    def test_upsert_chat_config(self):
        app = Application("", "")
        app.config["chat"] = []

        app.upsert_chat_download_config(
            chat_id="-100123",
            last_read_message_id=42,
            download_filter="media_file_size > 1MB",
            file_size_min="10MB",
            file_size_max="20MB",
        )
        app.update_config(False)

        chat_config = app.config["chat"][0]
        self.assertEqual(chat_config["chat_id"], -100123)
        self.assertEqual(chat_config["last_read_message_id"], 42)
        self.assertEqual(chat_config["file_size_min"], 10 * 1024 * 1024)
        self.assertEqual(chat_config["file_size_max"], 20 * 1024 * 1024)

    @mock.patch("__main__.__builtins__.open", new_callable=mock.mock_open)
    @mock.patch("module.app.yaml", autospec=True)
    def test_update_config(self, mock_yaml, mock_open):
        app = Application("", "")
        app.config_file = "config_test.yaml"
        app.app_data_file = "data_test.yaml"
        app.config["chat"] = [{"chat_id": 123, "last_read_message_id": 0}]
        app.update_config()
        mock_open.assert_called_with("data_test.yaml", "w", encoding="utf-8")
