# -*- coding: utf-8 -*-
"""
documentation
"""

from .modulehelper import ModuleHelper
from .selectable import Selectable, SelectableManager
from .tunable import Tunable, TunableError

class TunableSelectable(object):

    @classmethod
    def get_common_state(cls):
        return {
            'selectable': 1,
            'tunable': 1
        }

    @classmethod
    def set_common_state(cls, state):
        pass

    @classmethod
    def setup_and_parse(cls, parser, args=None):
        ModuleHelper.register_and_preparse(parser, args)
        SelectableManager.register_argparser(parser)
