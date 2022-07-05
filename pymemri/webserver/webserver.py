import threading
import uvicorn
from fastapi import FastAPI


class WebServer:
    def __init__(self):
        self._app = FastAPI(title="Plugin Webserver", redoc_url=None,
                            swagger_ui_oauth2_redirect_url=None)
        self._server_handle = None

    @property
    def app(self) -> FastAPI:
        return self._app

    def run(self):
        """Starts the webserver, only if any route was registered.
        Call returns immediately, server itself is offloaded to
        the daemon thread."""

        # Bare application has two endpoints registered:
        # /openapi.json and /docs
        DEFAULT_ROUTES = 2
        if len(self.app.routes) > DEFAULT_ROUTES:
            def thread_fn():
                uvicorn.run(self.app, host="0.0.0.0", port=8080, workers=1)

            self._server_handle = threading.Thread(target=thread_fn, daemon=True)
            self._server_handle.start()