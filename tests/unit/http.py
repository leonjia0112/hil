from haas import http

from abc import ABCMeta, abstractmethod
from urllib import urlencode
from StringIO import StringIO
import unittest
import json
import sys

from werkzeug.routing import Map
from werkzeug.wrappers import Request


def wsgi_mkenv(method, path, data=None):
    """Helper routine to build a wsgi environment.

    We need this to generate mock requests.
    """
    env = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'SERVER_NAME': 'haas.test-env',
        'SERVER_PORT': '5000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithreaded': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    if data is None:
        env['wsgi.input'] = StringIO()
    else:
        env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        env['wsgi.input'] = StringIO(urlencode(data))
    return env


class HttpTest(unittest.TestCase):
    """A test which excercises the http server.

    HttpTests run with no api functions registered to the http server yet;
    this lets us test the http-related code in an environment that is not
    constrained by our actual api.
    """

    def setUp(self):
        # We back up the old _url_map, and restore it in tearDown; this makes
        # it easy to be sure that we're not interfering with other tests:
        self.old_url_map = http._url_map
        # We make ourselves an empty one for our test:
        http._url_map = Map()

    def tearDown(self):
        http._url_map = self.old_url_map


class HttpEquivalenceTest(object):
    """A test that ensures a particlar call to the api behaves the same over
    http and when called as a function. Subclasses must override `api_call`
    and `request`, and may also be interested in `api_setup` and
    `api_teardown`.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def api_call(self):
        """Invoke the api call directly."""

    @abstractmethod
    def request(self):
        """Return a request which will invoke the api call.

        The request should take the form of a WSGI v1.0 environment.
        The function `wsgi_mkenv` can be used to build a suitable
        environment.
        """

    def api_setup(self):
        """Setup routine to be run before each call to the api.

        This is conceptually similar to python's unittest setUp()
        method, but with each call to `api_call`, rather than the
        whole test.

        By default this is a noop; subclasses should override this if
        they need specific environments.
        """

    def api_teardown(self):
        """like `api_setup`, but tears things down after the call."""

    def test_equivalence(self):
        """Calling `api_call` directly should be the same as via http."""

        # First invoke the call over http. This should never raise exceptions.
        self.api_setup()
        req = Request(self.request())
        resp = http.request_handler(req)
        body = resp.get_data()
        self.api_teardown()

        # Now call it directly.
        try:
            self.api_setup()
            ret = self.api_call()
            assert resp.status_code == 200
            if ret == '':
                assert body == ''
            else:
                assert json.loads(body) == json.loads(ret)
        except http.APIError, e:
            assert resp.status_code == e.status_code
            assert json.loads(body) == {'type': e.__class__.__name__,
                                        'msg': e.message,
                                        }
        finally:
            self.api_teardown()


class TestUrlArgs(HttpEquivalenceTest, HttpTest):
    """Test that arguments supplied in the url are passed correctly."""
    # The use of HTTPEquivalenceTest here is a bit weird; We're not actually
    # calling the api function from `api_call`. This is actually probably a
    # fairly common way to want to use the superclass; we should think about
    # whether the documented usage is necessarily the right idea.

    def setUp(self):
        HttpTest.setUp(self)

        @http.rest_call('GET', '/func/<foo>/<bar>')
        def func(foo, bar):
            return json.dumps([foo, bar])

    def api_call(self):
        return json.dumps(['alice', 'bob'])

    def request(self):
        return wsgi_mkenv('GET', '/func/alice/bob')


class TestEquiv_basic_APIError(HttpEquivalenceTest, HttpTest):
    """Basic test to make sure the APIError handling code is excercised."""

    def setUp(self):
        HttpTest.setUp(self)

        @http.rest_call('GET', '/some_error')
        def some_error():
            self.api_call()

    def api_call(self):
        raise http.APIError("Basic test of the APIError code.")

    def request(self):
        return wsgi_mkenv('GET', '/some_error')