from urllib.parse import urlparse
from common.logger import logging


class UrlParse:
    def __init__(self, _url):
        self.scheme = None
        self.netloc = None
        self.path = None
        self.params = None
        self.query = None
        self.fragment = None
        self._resolve(_url)

    def _resolve(self, _url):
        obj = urlparse(_url)
        self.__dict__.update(obj._asdict())
        # Add http protocol by default if haven't scheme
        if self.scheme == '':
            self.scheme = 'http'

        if self.scheme not in ['http', 'https']:
            raise TypeError('{} looks like a regular format'.format(_url))

    def geturl(self, only_domain=False):
        """
        Dynamic return url
        :param only_domain: False by default
        :return: str as <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                 or only domain as <scheme>://<netloc>
        """
        _u = '{}://{}'.format(self.scheme, self.netloc)
        if only_domain:
            return _u

        if self.path:
            _u += self.path
        if self.params:
            _u += ';{}'.format(self.params)
        if self.query:
            _u += '?{}'.format(self.query)
        if self.fragment:
            _u += '#{}'.format(self.fragment)
        return _u

    @classmethod
    def resolve_params(cls, params: str):
        # 以&符号分割
        params_dict = {}
        # error_data = ''
        params_list = params.split('&')
        for part in params_list:
            part = part.split('=')
            if len(part) >= 2:
                name = part[0]
                value = ''.join(part[1:])
                params_dict[name] = value
            else:
                logging.error('resolve params {} error'.format(part))

        return params_dict

