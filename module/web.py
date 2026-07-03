"""web ui for media download"""

import asyncio
import logging
import os
import threading
from typing import Callable, Optional

from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager, UserMixin, login_required, login_user

import utils
from module.app import Application
from module.download_stat import (
    DownloadState,
    get_download_result,
    get_download_state,
    get_total_download_speed,
    set_download_state,
)
from utils.crypto import AesBase64
from utils.format import format_byte

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

_flask_app = Flask(__name__)

_flask_app.secret_key = "tdl"
_login_manager = LoginManager()
_login_manager.login_view = "login"
_login_manager.init_app(_flask_app)
web_login_users: dict = {}
deAesCrypt = AesBase64("1234123412ABCDEF", "ABCDEF1234123412")
_application: Optional[Application] = None
_download_client = None
_start_chat_download_handler: Optional[Callable] = None


class User(UserMixin):
    """Web Login User"""

    def __init__(self):
        self.sid = "root"

    @property
    def id(self):
        """ID"""
        return self.sid


@_login_manager.user_loader
def load_user(_):
    """
    Load a user object from the user ID.

    Returns:
        User: The user object.
    """
    return User()


def get_flask_app() -> Flask:
    """get flask app instance"""
    return _flask_app


def run_web_server(app: Application):
    """
    Runs a web server using the Flask framework.
    """

    get_flask_app().run(
        app.web_host, app.web_port, debug=app.debug_web, use_reloader=False
    )


# pylint: disable = W0603
def init_web(
    app: Application,
    download_client=None,
    start_chat_download_handler: Optional[Callable] = None,
):
    """
    Set the value of the users variable.

    Args:
        users: The list of users to set.

    Returns:
        None.
    """
    global web_login_users
    global _application
    global _download_client
    global _start_chat_download_handler
    _application = app
    _download_client = download_client
    _start_chat_download_handler = start_chat_download_handler
    if app.web_login_secret:
        web_login_users = {"root": app.web_login_secret}
    else:
        _flask_app.config["LOGIN_DISABLED"] = True
    if app.debug_web:
        threading.Thread(target=run_web_server, args=(app,)).start()
    else:
        threading.Thread(
            target=get_flask_app().run, daemon=True, args=(app.web_host, app.web_port)
        ).start()


@_flask_app.route("/login", methods=["GET", "POST"])
def login():
    """
    Function to handle the login route.

    Parameters:
    - No parameters

    Returns:
    - If the request method is "POST" and the username and
      password match the ones in the web_login_users dictionary,
      it returns a JSON response with a code of "1".
    - Otherwise, it returns a JSON response with a code of "0".
    - If the request method is not "POST", it returns the rendered "login.html" template.
    """
    if request.method == "POST":
        username = "root"
        web_login_form = {}
        for key, value in request.form.items():
            if value:
                value = deAesCrypt.decrypt(value)
            web_login_form[key] = value

        if not web_login_form.get("password"):
            return jsonify({"code": "0"})

        password = web_login_form["password"]
        if username in web_login_users and web_login_users[username] == password:
            user = User()
            login_user(user)
            return jsonify({"code": "1"})

        return jsonify({"code": "0"})

    return render_template("login.html")


@_flask_app.route("/")
@login_required
def index():
    """Index html"""
    return render_template(
        "index.html",
        download_state=(
            "pause" if get_download_state() is DownloadState.Downloading else "continue"
        ),
    )


@_flask_app.route("/get_download_status")
@login_required
def get_download_speed():
    """Get download speed"""
    return (
        '{ "download_speed" : "'
        + format_byte(get_total_download_speed())
        + '/s" , "upload_speed" : "0.00 B/s" } '
    )


@_flask_app.route("/set_download_state", methods=["POST"])
@login_required
def web_set_download_state():
    """Set download state"""
    state = request.args.get("state")

    if state == "continue" and get_download_state() is DownloadState.StopDownload:
        set_download_state(DownloadState.Downloading)
        return "pause"

    if state == "pause" and get_download_state() is DownloadState.Downloading:
        set_download_state(DownloadState.StopDownload)
        return "continue"

    return state


def _chat_download_active(chat_config) -> bool:
    """Whether a chat has scheduled or active download work."""
    node = chat_config.node
    if node.is_stop_transmission:
        return False

    if not chat_config.need_check:
        return True

    return node.is_running and node.total_task != node.total_download_task


def _chat_download_status(chat_config) -> str:
    """Return a compact status for the web UI."""
    if _chat_download_active(chat_config):
        return "running"
    if chat_config.node.is_stop_transmission:
        return "stopped"
    if chat_config.total_task and chat_config.finish_task >= chat_config.total_task:
        return "finished"
    return "idle"


def _chat_config_rows():
    """Build rows for the chat config table."""
    if not _application:
        return []

    rows = []
    for chat_id, chat_config in _application.chat_download_config.items():
        progress = 0
        if chat_config.total_task:
            progress = round(chat_config.finish_task / chat_config.total_task * 100, 1)

        rows.append(
            {
                "chat_id": str(chat_id),
                "last_read_message_id": chat_config.last_read_message_id,
                "download_filter": chat_config.download_filter or "",
                "start_date": chat_config.start_date or "",
                "end_date": chat_config.end_date or "",
                "file_size_min": (
                    format_byte(chat_config.file_size_min)
                    if chat_config.file_size_min is not None
                    else ""
                ),
                "file_size_max": (
                    format_byte(chat_config.file_size_max)
                    if chat_config.file_size_max is not None
                    else ""
                ),
                "file_size_min_bytes": chat_config.file_size_min,
                "file_size_max_bytes": chat_config.file_size_max,
                "total_task": chat_config.total_task,
                "finish_task": chat_config.finish_task,
                "ids_to_retry": len(chat_config.ids_to_retry),
                "progress": progress,
                "status": _chat_download_status(chat_config),
            }
        )

    return rows


@_flask_app.route("/get_chat_configs")
@login_required
def get_chat_configs():
    """Get configured chat downloads."""
    data = _chat_config_rows()
    return jsonify({"code": 0, "count": len(data), "data": data})


@_flask_app.route("/save_chat_config", methods=["POST"])
@login_required
def save_chat_config():
    """Create or update one chat config."""
    if not _application:
        return jsonify({"code": 1, "msg": "application is not ready"})

    chat_id = request.form.get("chat_id", "").strip()
    if not chat_id:
        return jsonify({"code": 1, "msg": "chat_id is required"})

    try:
        origin_chat_id = request.form.get("origin_chat_id", "")
        if origin_chat_id:
            resolved_origin_chat_id = _application.resolve_chat_id(origin_chat_id)
            origin_chat_config = _application.chat_download_config.get(
                resolved_origin_chat_id
            )
            if origin_chat_config and _chat_download_active(origin_chat_config):
                return jsonify({"code": 1, "msg": "stop the chat before saving it"})

        last_read_message_id = int(request.form.get("last_read_message_id") or 0)
        _application.upsert_chat_download_config(
            chat_id=chat_id,
            last_read_message_id=last_read_message_id,
            download_filter=request.form.get("download_filter", ""),
            file_size_min=request.form.get("file_size_min", ""),
            file_size_max=request.form.get("file_size_max", ""),
            start_date=request.form.get("start_date", ""),
            end_date=request.form.get("end_date", ""),
            origin_chat_id=origin_chat_id,
        )
        _application.update_config()
    except Exception as e:
        return jsonify({"code": 1, "msg": str(e)})

    return jsonify({"code": 0, "msg": "saved"})


@_flask_app.route("/delete_chat_config", methods=["POST"])
@login_required
def delete_chat_config():
    """Delete one chat config."""
    if not _application:
        return jsonify({"code": 1, "msg": "application is not ready"})

    chat_id = request.form.get("chat_id", "").strip()
    resolved_chat_id = _application.resolve_chat_id(chat_id)
    if resolved_chat_id not in _application.chat_download_config:
        return jsonify({"code": 1, "msg": "chat not found"})

    chat_config = _application.chat_download_config[resolved_chat_id]
    if _chat_download_active(chat_config):
        return jsonify({"code": 1, "msg": "stop the chat before deleting it"})

    _application.delete_chat_download_config(resolved_chat_id)
    _application.update_config()
    return jsonify({"code": 0, "msg": "deleted"})


@_flask_app.route("/start_chat_download", methods=["POST"])
@login_required
def web_start_chat_download():
    """Start one configured chat."""
    if not _application or not _download_client or not _start_chat_download_handler:
        return jsonify({"code": 1, "msg": "download client is not ready"})

    chat_id = request.form.get("chat_id", "").strip()
    resolved_chat_id = _application.resolve_chat_id(chat_id)
    if resolved_chat_id not in _application.chat_download_config:
        return jsonify({"code": 1, "msg": "chat not found"})

    chat_config = _application.chat_download_config[resolved_chat_id]
    if _chat_download_active(chat_config):
        return jsonify({"code": 1, "msg": "chat is already running"})

    chat_config.need_check = False
    try:
        asyncio.run_coroutine_threadsafe(
            _start_chat_download_handler(_download_client, resolved_chat_id),
            _application.loop,
        )
    except Exception as e:
        chat_config.need_check = True
        return jsonify({"code": 1, "msg": str(e)})

    return jsonify({"code": 0, "msg": "started"})


@_flask_app.route("/stop_chat_download", methods=["POST"])
@login_required
def web_stop_chat_download():
    """Stop one configured chat."""
    if not _application:
        return jsonify({"code": 1, "msg": "application is not ready"})

    chat_id = request.form.get("chat_id", "").strip()
    resolved_chat_id = _application.resolve_chat_id(chat_id)
    if resolved_chat_id not in _application.chat_download_config:
        return jsonify({"code": 1, "msg": "chat not found"})

    chat_config = _application.chat_download_config[resolved_chat_id]
    chat_config.node.stop_transmission()
    chat_config.need_check = True
    _application.update_config()
    return jsonify({"code": 0, "msg": "stopped"})


@_flask_app.route("/get_app_version")
def get_app_version():
    """Get telegram_media_downloader version"""
    return utils.__version__


@_flask_app.route("/get_download_list")
@login_required
def get_download_list():
    """get download list"""
    if request.args.get("already_down") is None:
        return "[]"

    already_down = request.args.get("already_down") == "true"

    download_result = get_download_result()
    result = "["
    for chat_id, messages in download_result.items():
        for idx, value in messages.items():
            is_already_down = value["down_byte"] == value["total_size"]

            if already_down and not is_already_down:
                continue

            if result != "[":
                result += ","
            download_speed = format_byte(value["download_speed"]) + "/s"
            result += (
                '{ "chat":"'
                + f"{chat_id}"
                + '", "id":"'
                + f"{idx}"
                + '", "filename":"'
                + os.path.basename(value["file_name"])
                + '", "total_size":"'
                + f'{format_byte(value["total_size"])}'
                + '" ,"download_progress":"'
            )
            result += (
                f'{round(value["down_byte"] / value["total_size"] * 100, 1)}'
                + '" ,"download_speed":"'
                + download_speed
                + '" ,"save_path":"'
                + value["file_name"].replace("\\", "/")
                + '"}'
            )

    result += "]"
    return result
