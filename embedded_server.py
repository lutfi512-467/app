"""Start the original WebWindow Flask backend inside the Android app."""
import threading
from werkzeug.serving import make_server
from app import app

_server = None
_thread = None


def start_server():
    global _server, _thread
    if _thread is not None and _thread.is_alive():
        return True
    _server = make_server('127.0.0.1', 5000, app, threaded=True)
    _thread = threading.Thread(target=_server.serve_forever, name='WebWindowFlask', daemon=True)
    _thread.start()
    return True
