# -*- coding: utf-8 -*-
"""
documentation
"""


class Selectable(object):

    class SelectableChoice(object):
        overrides = {}

    class Default(object):
        pass

    def __new__(cls):
        if cls in cls.SelectableChoice.overrides:
            result = cls.SelectableChoice.overrides[cls]
        else:
            default = [choice for choice in cls.__subclasses__() if issubclass(choice, cls.Default)]
            if len(default) > 1:
                raise TypeError("Class %r with multiple defaults! %r" % (cls, default,))
            if len(default) == 0:
                raise TypeError("Class %r without implementation!" % (default,))

            result = default[0]
            cls.SelectableChoice.overrides[cls] = result

        return object.__new__(result)


class SelectableManager(object):
    Selectable = Selectable

    @classmethod
    def get(cls):
        return {c: [cc for cc in c.__subclasses__()]
                for c in cls.Selectable.__subclasses__()}

    @classmethod
    def defaults(cls):
        return {c: [cc for cc in c.__subclasses__() if issubclass(cc, Selectable.Default)]
                for c in cls.Selectable.__subclasses__()}

    @classmethod
    def set(cls, selectable, choice):
        if not issubclass(selectable, Selectable):
            raise TypeError("Wrong arguments passed.")

        selectable.SelectableChoice.overrides[selectable] = next(
            possible_choice for possible_choice in cls.get()[selectable]
            if possible_choice == choice or cls.class2name(possible_choice) == choice
        )

    @classmethod
    def class2name(cls, c):
        return c.__name__

    import argparse

    @classmethod
    def register_argparser(cls, parser):

        defaults = cls.defaults()
        for class_, choice in sorted(SelectableManager.get().items(), key=lambda _cc: cls.class2name(_cc[0])):
            name = cls.class2name(class_)
            token = parser.prefix_chars[0:1]*2 + name
            choices = [cls.class2name(c) for c in sorted(choice, key=lambda _c: cls.class2name(_c))]
            default = defaults[class_] if class_ in defaults else choices[0]
            parser.add_argument(token, type=str, choices=choices, default=default, action=cls.ArgparseAction)
            cls.ArgparseAction.mapping[token] = class_

    # noinspection PyClassHasNoInit
    class ArgparseAction(argparse.Action):
        mapping = {}

        def __call__(self, parser, namespace, values, option_string=None):
            if option_string in self.__class__.mapping:
                SelectableManager.set(self.__class__.mapping[option_string], values)

