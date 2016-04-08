# -*- coding: utf-8 -*-
"""
documentation
"""

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

import argparse


def main():

    p = argparse.ArgumentParser()

    Tunable.Manager.register_argparser(p)

    p.parse_args()

    print(Tunable.Manager.get())

    print(Otsu.value)



    Otsu.set(14.0)

    print(Otsu.value)

    Tunable.Manager.load({'__main__.Otsu': 17})

    print(Otsu.value)

    print(QuickOtsu.value)

if __name__ == '__main__':
    main()
