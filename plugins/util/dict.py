import copy

class CaseInsensitiveDefaultDict(dict):
    @classmethod
    def _k(cls, key):
        return key.casefold() if isinstance(key, str) else key

    def __init__(self, default=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default = default

    def __getitem__(self, toMatch):
        match = None
        for key, value in self.items():
            if (self._k(key) == self._k(toMatch)):
                match = value
        if (match is None and self.default is not None):
            _copy = copy.deepcopy(self.default)
            super().__setitem__(toMatch, _copy)
            return _copy

        if (match is None):
            raise KeyError

        return match

    def __setitem__(self, key, value):
        for k, v in self.items():
            if (self._k(k) == self._k(key)):
                self.__setitem__(k, value)
                return
        super().__setitem__(key, value)

    def __delitem__(self, key):
        for k in super().keys():
            if (self._k(k) == self._k(key)):
                return super().__delitem__(k)

    def __contains__(self, key):
        for k, v in self.items():
            if (self._k(k) == self._k(key)):
                return True
        return False

    def pop(self, key, *args, **kwargs):
        for k, v in self.items():
            if (self._k(k) == self._k(key)):
                return super().pop(k, *args, **kwargs)
        return super().pop(key, *args, **kwargs)

    def get(self, key, *args, **kwargs):
        for k, v in self.items():
            if (self._k() == self._k(key)):
                return super().get(k, *args, **kwargs)
        return super().get(key, *args, **kwargs)
