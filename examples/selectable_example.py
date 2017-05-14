# -*- coding: utf-8 -*-
"""
documentation
"""

import argparse
from tunable import SelectableManager, ModuleHelper
from selectable_hasher import *


def main():

    argparser = argparse.ArgumentParser(description="ABC")

    ModuleHelper.add_prefix("selectable_")

    ModuleHelper.register_and_preparse(argparser)

    SelectableManager.register_argparser(argparser)

    argparser.add_argument('--str', type=str, default="Hello World")

    args = argparser.parse_args()

    print("For our Hasher class, there are the following choices:",
          [class_.__name__ for class_ in SelectableManager.get()[Hasher]]
          )

    print("A Hasher() now looks like this:", Hasher())

    print(Hasher().hash(args.str.encode()))


if __name__ == '__main__':
    main()
