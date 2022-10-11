import threading

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server


class WebServer:
    def __init__(self, port: int):
        self._app = self._setup_app()
        self._server_handle = None
        self._uvicorn = None
        self._port = port
        self._daemon = False

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

    def register_health_endpoint(self, endpoint):
        """Sets user defined handler for /v1/health endpoint that is
        used to retrieve the plugin state"""
        self.app.add_api_route("/v1/health", endpoint, methods=["GET"])

    @property
    def app(self) -> FastAPI:
        return self._app

    def run(self) -> bool:
        """Starts the webserver, only if any route was registered.
        Call returns immediately, server itself is offloaded to
        the thread.
        Returns bool if the webserver actually started"""

        # Bare application has two endpoints registered:
        # /openapi.json and /docs
        DEFAULT_ROUTES = 2
        if len(self.app.routes) > DEFAULT_ROUTES:
            config = Config(app=self.app, host="0.0.0.0", port=self._port, workers=1)
            self._uvicorn = Server(config=config)

            self._server_handle = threading.Thread(target=self._uvicorn.run, daemon=False)
            self._server_handle.start()
            return True

        return False

    @property
    def daemon(self) -> bool:
        return self._daemon

    @daemon.setter
    def daemon(self, daemon: bool):
        self._daemon = daemon

    def is_running(self):
        return self._server_handle is not None

    def shutdown(self):
        """Shuts down the uvicorn server, frees the thread"""
        logger.info("Shutting down the webserver..")
        if self._uvicorn:
            self._uvicorn.should_exit = True
            # self._uvicorn.force_exit = True
            logger.info("Joining the thread...")

            if self._server_handle:
                self._server_handle.join()
                self._server_handle = None

        logger.info("Webserver shut down")
