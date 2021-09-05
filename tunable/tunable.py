# -*- coding: utf-8 -*-
"""
documentation
"""


def fancybool(value):
    if isinstance(value, type('')):
        value = value.lower()
        if (
            value == 'true'
            or value == 'yes'
            or value == 't'
            or value == 'y'
            or value == '1'
        ):
            return True
        elif (
            value == 'false'
            or value == 'no'
            or value == 'f'
            or value == 'n'
            or value == '0'
        ):
            return False
        raise ValueError('Unsupported value %r passed, expected a bool.' % (value,))
    else:
        return bool(value)


CONVERTERS = {bool: fancybool}


class TunableError(RuntimeError):
    pass


# noinspection PyPep8Naming
class classproperty(object):
    __slots__ = (
        'fget',
        '__doc__',
    )

    def __init__(self, fget=None, doc=None):
        self.fget = fget

        if doc is None and fget is not None:
            doc = fget.__doc__

        self.__doc__ = doc

    def __get__(self, obj, cls):
        return self.fget(cls)


class Tunable(object):
    @classproperty
    def value(cls):
        return cls.reset()

    default = None

    convert_type = True
    range = None
    type_ = None

    hash = True

    documentation = None

    @classproperty
    def documentation(cls):
        if cls.__doc__:
            return cls.__doc__.strip()
        else:
            return ''

    # noinspection PyUnusedLocal
    @classmethod
    def test(cls, value):
        return True

    @classmethod
    def reset(cls):
        return cls.set(cls.default)

    @classmethod
    def set(cls, value):

        if value is None:
            raise TunableError('Tunable has no value', cls)

        if cls.type_ is None and cls.convert_type:
            cls.type_ = type(cls.default)

        if cls.type_ is not None and type(value) != cls.type_:
            try:
                if cls.type_ in CONVERTERS:
                    value = CONVERTERS[cls.type_](value)
                else:
                    value = cls.type_(value)
            except ValueError as e:
                raise TunableError(e)

        if (
            cls.range is not None
            and value not in cls.range
            and (type(cls.range) == range and value != cls.range.stop)
        ):
            raise TunableError('Tunable not in range', cls)

        if cls.test is not None and not cls.test(value):
            raise TunableError('test() failed!')

        cls.value = value
        return value

    def __new__(cls, *args, **kwargs):
        if len(kwargs) == 0:
            return cls.value
        else:

            class IntermediateTunable(Tunable):
                pass

            for k, v in kwargs.items():
                if k == 'documentation':
                    IntermediateTunable.__doc__ = v
                elif hasattr(Tunable, k):
                    setattr(IntermediateTunable, k, v)
                else:
                    raise TunableError('Unsupported attribute \"%s\"' % (k,))

            return IntermediateTunable
