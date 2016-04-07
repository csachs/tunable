from selectable import Hasher
import hashlib

class MD5(Hasher):
    def hash(self, s):
        return hashlib.md5(s).hexdigest()
