# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.authenticators.oauth.ipynb (unless otherwise specified).

__all__ = ['OAuthAuthenticator', 'ExampleOAuthAuthenticator']

# Cell
# hide
import abc
from time import sleep
from ..states import RUN_USER_ACTION_NEEDED, RUN_USER_ACTION_COMPLETED

# Cell
# hide

class OAuthAuthenticator(metaclass=abc.ABCMeta):

    SLEEP_INTERVAL = 1.0

    def __init__(self, client, pluginRun):
        self.client = client
        self.pluginRun = pluginRun
        self.isTest = False

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
        except: # no account exists or expired refresh token
            url = self.get_oauth_url()
            code = self.present_url_to_user(url)
            tokens = self.get_tokens_from_code(code)
            # if not tokens: raise an exception or set pluginRun.status=FAILED and pluginRun.message=ERROR_MESSAGE

        self.store_tokens(tokens)

    def present_url_to_user(self, url):
        if self.isTest:
            return 'dummy_code'
        # request user to visit url
        self.pluginRun.oAuthUrl = url
        self.pluginRun.status = RUN_USER_ACTION_NEEDED
        self.pluginRun.update(self.client)
       # WAIT HERE = BLOCK
        while True:
            sleep(self.SLEEP_INTERVAL)
            self.pluginRun = self.client.get(self.pluginRun.id)
            if self.pluginRun.status == RUN_USER_ACTION_COMPLETED:
                return self.pluginRun.account[0].code

    def store_tokens(self, tokens):
        account = self.pluginRun.account[0]
        account.accessToken = tokens['access_token']
        account.refreshToken = tokens['refresh_token'] if 'refresh_token' in tokens else None
        account.update(self.client)

    @abc.abstractmethod
    def get_oauth_url(self):
        raise NotImplemented()

    @abc.abstractmethod
    def get_tokens_from_code(self, code):
        """ Gets access and refresh tokens from 3rd party service
            and returns them in form:
                {
                    'access_token': '...',
                    'refresh_token': '...'
                }
        """
        raise NotImplemented()

    @abc.abstractmethod
    def refresh_tokens(self):
        """ Gets new tokens by using an existing refresh token
            and returns them in form:
                {
                    'access_token': '...',
                    'refresh_token': '...'
                }

        """
        # use self.pluginRun.account[0].refreshToken
        raise NotImplemented()

    @abc.abstractmethod
    def verify_access_token(self, token):
        """
        Check if existing token is working. If this returns True, then user interaction will not be needed.
        """
        raise NotImplemented()




# Cell
# hide

class ExampleOAuthAuthenticator(OAuthAuthenticator):

    def get_oauth_url(self):
        return "https://example.com/oauth"

    def get_tokens_from_code(self, code):
        return {
            'access_token': 'dummy_access_token',
            'refresh_token': 'dummy_refresh_token'
        }

    def refresh_tokens(self, refreshToken):
        return {
            'access_token': 'refreshed_dummy_access_token',
            'refresh_token': 'refreshed_dummy_refresh_token'
        }

    def verify_access_token(self, token):
        if token:
            return True