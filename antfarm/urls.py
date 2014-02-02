
'''
Django-style URL dispatcher view.

    App(root_url=url_dispatcher([
        (r'^/$', views.index),
        (re.compile(r'^/(?P<foo>\d+)/'), views.detail, {'bar': True}),
    ])

The view will be called with the request, and any matched _named_ groups.
Extra kwargs can be passed as a 3rd positional argument.

There is a namedtuple class defined called URL provided.  All patterns will be
assembled as a URL instance, and their regex compiled.  If kwargs are not
specified, they will default to {}.
'''

from collections import namedtuple

import re
from . import http

class KeepLooking(Exception):
    '''Used to tell a url_dispatcher to skip this pattern and keep looking.'''
    pass

URL = namedtuple('url', ('regex', 'view', 'kwargs',))

class url_dispatcher(object):
    def __init__(self, patterns):
        self.patterns = map(self._make_url, patterns)

    def _make_url(self, pattern):
        '''Helper to ensure all patterns are url instances.'''
        if not isinstance(pattern, URL):
            if len(pattern) == 2:
                pattern = list(pattern) + [{}]
            pattern[0] = re.compile(pattern[0])
            pattern = URL(*pattern)
        # Ensure the regex is compiled
        pattern.regex = re.compile(pattern.regex)
        return pattern

    def __call__(self, request):
        path = getattr(request, 'remaining_path', request.path)
        for pattern in self.patterns:
            m = pattern.regex.match(path)
            if m:
                path.remaining_path = path[:m.end()]
                kwargs = dict(pattern.kwargs)
                kwargs.update(pattern.kwargs)
                try:
                    return pattern.view(request, **kwargs)
                except KeepLooking:
                    pass

        self.handle_not_found(request)

    def handle_not_found(self, request):
        raise http.NotFound()
