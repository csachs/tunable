# -*- coding: utf-8 -*-
"""
documentation
"""

class classproperty(object):
    __slots__ = ('fget', '__doc__', )

    def __init__(self, fget=None, doc=None):
        self.fget = fget

        if doc is None and fget is not None:
            doc = fget.__doc__

        self.__doc__ = doc

    def __get__(self, obj, cls):
        return self.fget(cls)

class TunableError(RuntimeError):
    pass

class Tunable(object):

    class Manager(object):

        @classmethod
        def load(cls, tunables):
            existing = cls.get_multi_dict()

            setted = set()

            for key, value in tunables.items():
                if key not in existing:
                    raise TunableError("Tunable \"%s\" does not exist." % (key,))

                class_ = existing[key]

                class_.set(value)

                setted.add(class_)

            for class_ in (set(existing.values()) - setted):
                class_.reset()

        @classmethod
        def get_classes(cls):
            collection = set()
            def descent(p):
                sub = p.__subclasses__()
                if len(sub) == 0:
                    collection.add(p)
                else:
                    for p in sub:
                        descent(p)

            descent(Tunable)

            return list(sorted(collection, key=lambda p: (p.__module__, p.__name__,)))

        @classmethod
        def get_short_dict(cls):
            return {class_.__name__: class_ for class_ in cls.get_classes()}

        @classmethod
        def get_long_dict(cls):
            return {class_.__module__ + '.' + class_.__name__: class_ for class_ in cls.get_classes()}

        @classmethod
        def get_multi_dict(cls):
            merged = {}
            merged.update(cls.get_long_dict())
            merged.update(cls.get_short_dict())
            return merged

        @classmethod
        def get(cls):
            return list(cls.get_long_dict().keys())

    @classproperty
    def value(cls):
        return cls.reset()

    default = None

    range = None
    type_ = None

    documentation = None

    @classproperty
    def documentation(cls):
        return cls.__doc__

    @classmethod
    def test(cls, value):
        return True

    @classmethod
    def reset(cls):
        print(cls)
        return cls.set(cls.default)

    @classmethod
    def set(cls, value):

        if value is None:
            raise TunableError('Tunable has no value', cls)

        if cls.type_ is not None and type(value) != cls.type_:
            try:
                value = cls.type_(value)
            except ValueError as e:
                raise TunableError(e)

        if cls.range is not None and value not in cls.range \
                and (type(cls.range) == range and value != cls.range.stop):
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

                if hasattr(Tunable, k):
                    setattr(IntermediateTunable, k, v)
                else:
                    raise TunableError('Unsupported attribute \"%s\"' % (k,))

            return IntermediateTunable

