# -*- coding: utf-8 -*-
"""
documentation
"""

import argparse
import importlib
import sys
import warnings
from itertools import product


class ModuleHelper(object):

    Exception = Exception
    Warning = Warning
    Ignore = 1

    error_mode = Exception

    prefixes = [""]

    modules = {}

    @classmethod
    def add_prefix(cls, prefix):
        cls.prefixes.append(prefix)

    @classmethod
    def load_module(cls, module_str):
        if module_str in cls.modules:
            return

        sys.path.insert(0, '.')

        module_ = None

        names = [
            "%s%s"
            % (
                prefix,
                name,
            )
            for name, prefix in product(
                [module_str, module_str.lower()], reversed(cls.prefixes)
            )
        ]

        for name in names:
            try:
                module_ = importlib.import_module(name)
                break
            except ImportError:
                pass

        if module_ is None:
            error_msg = (
                "Attempted to load any of %r, but could not load any module." % (names,)
            )
            if cls.error_mode == Exception:
                raise ImportError(error_msg)
            elif cls.error_mode == Warning:
                warnings.warn(error_msg, ImportWarning)
            else:
                raise RuntimeError('Invalid error mode.')

        cls.modules[module_str] = module_

    class ImportAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            ModuleHelper.load_module(values)

    @classmethod
    def register_and_preparse(cls, parser, args=None, short='m', long='module'):

        actions = parser._actions.copy()
        option = parser._option_string_actions.copy()

        parser._actions.clear()
        parser._option_string_actions.clear()

        parser.add_argument(
            parser.prefix_chars[0:1] + short,
            parser.prefix_chars[0:1] * 2 + long,
            type=str,
            action=cls.ImportAction,
        )
        parser.parse_known_args(args=args)

        for action in actions:
            parser._actions.insert(0, action)

        parser._option_string_actions.update(option)
