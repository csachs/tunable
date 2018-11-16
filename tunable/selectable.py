# -*- coding: utf-8 -*-
"""
documentation
"""

from .modulehelper import ModuleHelper


class Selectable(object):
    autoload = True

    class SelectableChoice(object):
        overrides = {}
        parameters = {}

    class Default(object):
        pass

    class Virtual(object):
        pass

    class Multiple(object):
        pass

    @classmethod
    def SelectableGetMultiple(cls, *args, **kwargs):
        return SelectableManager.create_selectable(cls, args, kwargs, multiple=True)

    def __new__(cls, *args, **kwargs):
        return SelectableManager.create_selectable(cls, args, kwargs)


def get_all_subclasses(what):
    collector = set()

    def _recurse(w):
        for cc in w.__subclasses__():
            collector.add(cc)
            _recurse(cc)

    _recurse(what)
    return collector


def opportunistic_cast(value):
    if value.lower() == 'true':
        return True

    if value.lower() == 'false':
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return str(value)


def parse_class_name_with_kwargs(value):
    the_kwargs = dict()
    if '(' in value and value[-1] == ')':
        value, kv = value.split('(')
        kv = kv[:-1]

        for kv_pair in kv.split(','):
            k, v = kv_pair.split('=')
            k, v = k.strip(), v.strip()

            v = opportunistic_cast(v)

            the_kwargs[k] = v

    return value, the_kwargs


class SelectableManager(object):
    Selectable = Selectable

    @classmethod
    def resolve_selectable(cls, selectable_cls):
        if selectable_cls in selectable_cls.SelectableChoice.overrides:
            result = selectable_cls.SelectableChoice.overrides[selectable_cls]
        else:
            # check if it is directly inherited, or deeper inherited
            # if it is not-direct, it must still remain valid to instantiate classes
            if Selectable not in selectable_cls.__bases__:
                result = selectable_cls
            else:
                default = [choice for choice in selectable_cls.__subclasses__() if issubclass(choice, selectable_cls.Default)]
                if len(default) > 1:
                    raise TypeError("Class %r with multiple defaults! %r" % (selectable_cls, default,))
                if len(default) == 0:
                    raise TypeError("Class %r without implementation!" % (default,))

                result = default[0]
                selectable_cls.SelectableChoice.overrides[selectable_cls] = result

        return result

    @classmethod
    def proxify_init(cls, selectable):
        if hasattr(selectable, '__real_init__'):
            return

        selectable.__real_init__ = selectable.__init__

        def _init_proxy(self, *args, **kwargs):
            if hasattr(self, '__real_init_called'):
                return
            else:
                setattr(self, '__real_init_called', True)
                selectable.__real_init__(self, *args, **kwargs)

        selectable.__init__ = _init_proxy

    @classmethod
    def instantiate_selectable(cls, selectable, args, kwargs):

        cls.proxify_init(selectable)

        result = object.__new__(selectable)

        compound_kwargs = {}
        if selectable in selectable.SelectableChoice.parameters:
            compound_kwargs.update(selectable.SelectableChoice.parameters[selectable])
        compound_kwargs.update(kwargs)

        result.__init__(*args, **compound_kwargs)

        return result

    @classmethod
    def create_selectable(cls, selectable_cls, args, kwargs, multiple=False):
        result = cls.resolve_selectable(selectable_cls)

        if cls.is_multiple(selectable_cls):
            if not multiple:
                if isinstance(result, list):
                    result = result[0]
            else:
                if not isinstance(result, list):
                    result = [result]
                return [
                    cls.instantiate_selectable(one_selectable, args, kwargs)
                    for one_selectable in result
                ]
        return cls.instantiate_selectable(result, args, kwargs)

    @classmethod
    def get(cls):
        return {
            c: [cc for cc in get_all_subclasses(c) if Selectable.Virtual not in cc.__subclasses__()]
            for c in cls.Selectable.__subclasses__()
        }

    @classmethod
    def get_choice_for_string(cls, selectable, choice):
        if isinstance(choice, type):
            choice = cls.class2name(choice)
        for class_ in cls.get()[selectable]:
            if cls.class2name(class_) == choice:
                return class_
        raise RuntimeError("Invalid choice passed.")

    @classmethod
    def defaults(cls):
        return {c: [cc for cc in l if issubclass(cc, Selectable.Default)] for c, l in cls.get().items()}

    @classmethod
    def _pick(cls, selectable, choice):
        if not issubclass(selectable, Selectable):
            raise TypeError("Wrong arguments passed.")

        return next(
            possible_choice for possible_choice in cls.get()[selectable]
            if possible_choice == choice or cls.class2name(possible_choice) == choice
        )

    @classmethod
    def set(cls, selectable, choice):
        selectable.SelectableChoice.overrides[selectable] = cls._pick(selectable, choice)

    @classmethod
    def add(cls, selectable, choice):
        pick = cls._pick(selectable, choice)
        overrides = selectable.SelectableChoice.overrides

        if selectable not in overrides:
            overrides[selectable] = []

        if selectable in overrides and not isinstance(overrides[selectable], list):
            overrides[selectable] = [overrides[selectable]]

        overrides[selectable].append(pick)

    @classmethod
    def set_default_parameters(cls, selectable, parameters):
        if selectable not in selectable.SelectableChoice.parameters:
            selectable.SelectableChoice.parameters[selectable] = {}
        selectable.SelectableChoice.parameters[selectable].update(parameters)

    @classmethod
    def class2name(cls, c):
        return c.__name__

    @classmethod
    def is_multiple(cls, selectable):
        return issubclass(selectable, Selectable.Multiple)

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
            cls.ArgparseAction.mapping[name] = class_

        parser._real_check_value = parser._check_value

        self = parser

        def _monkey_patch_check_value(action, value):
            if action.dest in cls.ArgparseAction.mapping:
                value, the_kwargs = parse_class_name_with_kwargs(value)

                class_ = cls.ArgparseAction.mapping[action.dest]
                if action.choices and value not in action.choices:
                    if class_.autoload:
                        try:
                            ModuleHelper.load_module(value)
                        except ImportError:
                            pass  # this time we're silent
                    choice = SelectableManager.get()[class_]
                    action.choices = [cls.class2name(c) for c in sorted(choice, key=lambda _c: cls.class2name(_c))]

            self._real_check_value(action, value)

        parser._check_value = _monkey_patch_check_value

    # noinspection PyClassHasNoInit
    class ArgparseAction(argparse.Action):
        mapping = {}

        def __call__(self, parser, namespace, values, option_string=None):
            if option_string in self.__class__.mapping:
                mapped_selectable = self.__class__.mapping[option_string]

                class_name = SelectableManager.class2name(mapped_selectable)

                if SelectableManager.is_multiple(mapped_selectable):
                    setattr(namespace, class_name,
                            getattr(namespace, class_name, []) + [values]
                            )
                else:
                    setattr(namespace, class_name, values)

                values, the_kwargs = parse_class_name_with_kwargs(values)

                if SelectableManager.is_multiple(mapped_selectable):
                    SelectableManager.add(mapped_selectable, values)
                else:
                    SelectableManager.set(mapped_selectable, values)

                if the_kwargs:
                    SelectableManager.set_default_parameters(
                        SelectableManager.get_choice_for_string(mapped_selectable, values),
                        the_kwargs
                    )
