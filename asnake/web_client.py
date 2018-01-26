from requests import Session
from urllib.parse import urljoin, quote
import json
from .configurator import ASnakeConfig

class ASnakeAuthError(Exception): pass

def http_meth_factory(meth):
    '''Utility method for producing HTTP proxy methods for ASnakeProxyMethods mixin class.

Urls are prefixed with the baseurl defined  All arguments are p
    '''
    def http_method(self, url, *args, **kwargs):
        return getattr(self.session, meth)(urljoin(self.config['baseurl'], url), *args, **kwargs)

    return http_method


class ASnakeProxyMethods(type):
    '''Metaclass to set up proxy methods for all requests-supported HTTP methods'''
    def __init__(cls, name, parents, dct):

        for meth in ('get', 'post', 'head', 'put', 'delete', 'options',):
            fn = http_meth_factory(meth)
            fn.__name__ = meth
            fn.__doc__ = '''Proxied :meth:`requests.Session.{}` method from :class:`requests.Session`'''.format(meth)

            setattr(cls, meth, fn)

class ASnakeClient(metaclass=ASnakeProxyMethods):
    '''ArchivesSnake Web Client'''

    def __init__(self, **config):
        self.config = ASnakeConfig()
        self.config.update(config)

        if not hasattr(self, 'session'): self.session = Session()
        self.session.headers.update({'Accept': 'application/json',
                                     'User-Agent': 'ArchivesSnake/0.1'})


    def authorize(self, username=None, password=None):
        '''Authorizes the client against the configured archivesspace instance.

Parses the JSON response, and stores the returned session token in the session.headers for future requests.
Asks for a "non-expiring" session, which isn't truly immortal, just long-lived.'''
        username = username or self.config['username']
        password = password or self.config['password']

        resp = self.session.post(
            urljoin(self.config['baseurl'], 'users/{username}/login'.format(username=quote(username))),
            params={"password": password, "expiring": False}
        )

        if resp.status_code != 200:
            raise ASnakeAuthError("Failed to authorize ASnake with status: {}".format(resp.status_code))
        else:
            session_token = json.loads(resp.text)['session']
            self.session.headers['X-ArchivesSpace-Session'] = session_token
            return session_token
