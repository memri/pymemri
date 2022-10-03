import abc
from time import sleep

from ..states import RUN_FAILED, RUN_USER_ACTION_COMPLETED, RUN_USER_ACTION_NEEDED


class OAuthAuthenticator(metaclass=abc.ABCMeta):

    SLEEP_INTERVAL = 1.0

    def __init__(self, client, pluginRun):
        self.client = client
        self.pluginRun = pluginRun

    def authenticate(self):
        account = self.pluginRun.account[0] if len(self.pluginRun.account) > 0 else None
        if account.accessToken:
            if self.verify_access_token(account.accessToken):
                return

        tokens = None
        try:
            if not self.pluginRun.account[0].refreshToken:
                raise Exception("Refresh token is empty")
            tokens = self.refresh_tokens(self.pluginRun.account[0].refreshToken)
        except:  # no account exists or expired refresh token
            url = self.get_oauth_url()
            self.present_url_to_user(url)
            code = self.poll_for_code()
            tokens = self.get_tokens_from_code(code)
            # if not tokens: raise an exception or set pluginRun.status=FAILED and pluginRun.message=ERROR_MESSAGE

        self.store_tokens(tokens)

    def poll_for_code(self):
        while True:
            sleep(self.SLEEP_INTERVAL)
            self.pluginRun = self.client.get(self.pluginRun.id)
            if self.pluginRun.status == RUN_USER_ACTION_COMPLETED:
                return self.pluginRun.account[0].code
            if self.pluginRun.status == RUN_FAILED:
                raise Exception(f"Error in plugin.authenticators.oauth {self.pluginRun.message}")

    def present_url_to_user(self, url):
        # request user to visit url
        self.pluginRun.authUrl = url
        self.pluginRun.status = RUN_USER_ACTION_NEEDED
        self.pluginRun.update(self.client)

    def store_tokens(self, tokens):
        account = self.pluginRun.account[0]
        account.accessToken = tokens["access_token"]
        account.refreshToken = tokens["refresh_token"] if "refresh_token" in tokens else None
        account.update(self.client)

    def get_account(self):
        return self.pluginRun.account[0]

    @abc.abstractmethod
    def get_oauth_url(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_tokens_from_code(self, code):
        """Gets access and refresh tokens from 3rd party service
        and returns them in form:
            {
                'access_token': '...',
                'refresh_token': '...'
            }
        """
        raise NotImplementedError

    @abc.abstractmethod
    def refresh_tokens(self):
        """Gets new tokens by using an existing refresh token
        and returns them in form:
            {
                'access_token': '...',
                'refresh_token': '...'
            }

        """
        # use self.pluginRun.account[0].refreshToken
        raise NotImplementedError

    @abc.abstractmethod
    def verify_access_token(self, token):
        """
        Check if existing token is working. If this returns True, then user interaction will not be needed.
        """
        raise NotImplementedError
