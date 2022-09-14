import threading

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server


class WebServer:
    def __init__(self, port: int):
        self._app = self._setup_app()
        self._server_handle = None
        self._uvicorn = None
        self._port = port

    def _setup_app(self) -> FastAPI:
        app = FastAPI(title="Plugin Webserver", redoc_url=None, swagger_ui_oauth2_redirect_url=None)

        # TODO setup allow_origin_regex for *.memri.io and localhost
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app

    @property
    def app(self) -> FastAPI:
        return self._app

    def run(self):
        """Starts the webserver, only if any route was registered.
        Call returns immediately, server itself is offloaded to
        the thread."""

        # Bare application has two endpoints registered:
        # /openapi.json and /docs
        DEFAULT_ROUTES = 2
        if len(self.app.routes) > DEFAULT_ROUTES:
            config = Config(app=self.app, host="0.0.0.0", port=self._port, workers=1)
            self._uvicorn = Server(config=config)

            self._server_handle = threading.Thread(target=self._uvicorn.run, daemon=False)
            self._server_handle.start()

    def is_running(self):
        return self._server_handle is not None

    def shutdown(self):
        """Shuts down the uvicorn server, frees the thread"""
        print("Shutting down the webserver..")
        if self._uvicorn:
            self._uvicorn.should_exit = True
            # self._uvicorn.force_exit = True
            print("Joining the thread...")

            if self._server_handle:
                self._server_handle.join()
                self._server_handle = None

        print("Webserver shut down")
