import hashlib

from selectable_hasher import Hasher


class MD5(Hasher):
    def hash(self, s):
        return hashlib.md5(s).hexdigest()
