# -*- coding: utf-8 -*-
"""
documentation
"""

import sys
sys.path.insert(0, '.')

from tunable import Tunable


class Otsu(Tunable):
    """An important tunable to modify bla bla foo."""
    default = "1.0"
    type_ = float

    #range = range(0, 1)


class QuickOtsu(Tunable(documentation="My little Otsu", default=8, type_=float)):
    pass


class QuickOtsuX(Tunable(documentation="My little Otsu", default=8, type_=float)):
    pass

def main():
    Tunable.Manager.load({'Otsu': 3})
    print(Tunable.Manager.get())

    print(Otsu.value)



    Otsu.set(14.0)

    print(Otsu.value)

    Tunable.Manager.load({"__main__.Otsu": 17})

    print(Otsu.value)

    print(QuickOtsu.value)

if __name__ == '__main__':
    main()
