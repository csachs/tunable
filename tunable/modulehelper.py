# -*- coding: utf-8 -*-
"""
documentation
"""

import argparse
import importlib
import warnings


class ModuleHelper(object):

    Exception = Exception
    Warning = Warning

    error_mode = Exception

    prefix = ""

    modules = {}


    @classmethod
    def load_module(cls, module_str):
        if module_str in cls.modules:
            return

        module = None

        try:
            module = importlib.import_module("%s%s" % (cls.prefix, module_str,))
        except ImportError:
            try:
                module = importlib.import_module(module_str)
            except ImportError:
                if cls.error_mode == Exception:
                    raise
                elif cls.error_mode == Warning:
                    warnings.warn("Attempted to load \"%s%s\" or \"%s\", but could not find either." % (cls.prefix, module_str, module_str,), ImportWarning)
                else:
                    # funny error_mode, huh?
                    raise

        cls.modules[module_str] = module

    class ImportAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            ModuleHelper.load_module(values)

    @classmethod
    def register_and_preparse(cls, parser, args=None, short='m', long='module'):

        actions = parser._actions.copy()
        option = parser._option_string_actions.copy()

        parser._actions.clear()
        parser._option_string_actions.clear()

        parser.add_argument(parser.prefix_chars[0:1] + short, 2*parser.prefix_chars[0:1] + long, type=str, action=cls.ImportAction)
        parser.parse_known_args(args=args)

        for action in actions:
            parser._actions.insert(0, action)

        parser._option_string_actions.update(option)
