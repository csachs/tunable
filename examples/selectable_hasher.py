import hashlib

from tunable import Selectable


class Hasher(Selectable):
    def __init__(self, **kwargs):
        print("got called with", kwargs)

    def hash(self, s):
        raise RuntimeError('Pure virtual function call')


class SHA256(Hasher):
    def hash(self, s):
        return hashlib.sha256(s).hexdigest()


class SHA1(Hasher, Hasher.Default):
    def hash(self, s):
        return hashlib.sha1(s).hexdigest()
