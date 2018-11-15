# -*- coding: utf-8 -*-
"""
documentation
"""

import argparse
from tunable import Tunable, TunableManager


class SomeTunableValue(Tunable):
    """An important tunable to modify bla bla foo."""
    default = "1.0"
    type_ = float

    # range = range(0, 1)


class SomeOtherTunableValue(Tunable(documentation="My little value", default=8, type_=float)):
    pass


class YetAnotherTunableValue(Tunable(documentation="My little other value", default=8, type_=float)):
    pass


def main():

    p = argparse.ArgumentParser()

    TunableManager.register_argparser(p)

    p.parse_args()

    print(TunableManager.get())

    print("Hash: %s" % (TunableManager.get_hash()))

    print(SomeTunableValue.value)

    SomeTunableValue.set(14.0)

    print(SomeTunableValue.value)

    TunableManager.load({'__main__.SomeTunableValue': 17})

    print(SomeTunableValue.value)

    print(SomeOtherTunableValue.value)


if __name__ == '__main__':
    main()
