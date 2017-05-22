# -*- coding: utf-8 -*-
"""
documentation
"""

import sys
import os
import argparse
import json
import hashlib

try:
    import pyasn1
    from .tunable_schema import (Tunable as SchemaTunable, TunableSequenceType as SchemaTunableSequenceType,
                                 TunablesList as SchemaTunablesList, TunableType as SchemaTunableType)
    from pyasn1.codec.der.encoder import encode as der_encode
except ImportError:
    pyasn1 = None

try:
    import yaml
except ImportError:
    pass


ASN1_SCHEMA_VERSION = 1


class Asn1Serializer(object):
    def __init__(self):
        self.tl = SchemaTunablesList()
        self.tl['version'] = ASN1_SCHEMA_VERSION
        self.tl['tunables'] = SchemaTunableSequenceType()

    def add_tunables(self, kv):
        # to make it independent of collation rules, sort it by its UTF-8 binary representation
        for k, v in sorted(kv.items(), key=lambda ab: ab[0].encode()):
            self.add_tunable(k, v)

    def add_tunable(self, name, value):
        sub_key = {
            bool: 'boolValue',
            int: 'intValue',
            bytes: 'bytesValue',
            float: 'floatValue',
            str: 'stringValue'
        }

        t = SchemaTunable()

        tv = SchemaTunableType()
        tv[sub_key[type(value)]] = value

        t['name'] = name
        t['value'] = tv

        self.tl['tunables'].append(t)

    def get_der(self):
        return der_encode(self.tl)

    def get_sha512(self):
        hasher = hashlib.sha512()
        hasher.update(self.get_der())
        return hasher.hexdigest()


# noinspection PyPep8Naming
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


class TunableManager(object):
    @classmethod
    def register_argparser(cls, parser, register=None):
        if register is None:
            register = {
                'show': (None, 'tunables-show'),
                'set': ('t', 'tunable'),
                'load': (None, 'tunables-load'),
                'save': (None, 'tunables-save')
            }

        p = parser.prefix_chars[0:1]
        prefix = p * 2

        for k, v in list(register.items()):
            if v is None:
                continue

            v = tuple(vv for vv in v if vv)
            if len(v) == 2:
                vshort, vlong = v
                v = (p + vshort, prefix + vlong,)
            else:
                v = (prefix + v[0],)

            register[k] = v

        if register['show']:
            parser.add_argument(*register['show'], action=cls.ShowTunablesAction)
        if register['set']:
            parser.add_argument(*register['set'], type=str, action=cls.SetTunableAction)
        if register['load']:
            parser.add_argument(*register['load'], type=str, action=cls.LoadTunablesAction)
        if register['save']:
            parser.add_argument(*register['save'], type=str, action=cls.SaveTunablesAction)

    class ShowTunablesAction(argparse._StoreTrueAction):
        quit_after_call = True  # False

        def __call__(self, parser, namespace, values, option_string=None):
            cls = TunableManager

            print(cls.get_config_representation())

            if self.__class__.quit_after_call:
                sys.exit(1)

    class LoadTunablesAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            cls = TunableManager
            file_name = os.path.abspath(values)

            ext = os.path.splitext(file_name)
            ext = ext[1][1:].lower()

            if ext == 'conf':
                with open(file_name) as f:
                    lines = [line.strip() for line in f.readlines() if len(line.strip()) > 0 and line.strip()[0] != '#']
                    for line in lines:
                        pieces = line.split('=')

                        k = pieces[0]
                        remainder = '='.join(pieces[1:])

                        TunableManager.set(k, remainder)

            elif ext == 'json':
                with open(file_name) as f:
                    cls.load(json.load(f))

            elif ext == 'yaml':
                if not yaml:
                    raise RuntimeError('yaml library missing!')

                with open(file_name) as f:
                    cls.load(yaml.load(f))

            elif ext == 'xml':
                raise RuntimeError('XML input currently not supported.')

            elif ext == 'der':
                if not pyasn1:
                    raise RuntimeError('pyasn1 library missing!')
                raise RuntimeError('DER input currently not supported.')

    class SaveTunablesAction(argparse.Action):
        quit_after_call = True  # False
        prompt_overwrite = True  # False

        def finish(self):
            if self.__class__.quit_after_call:
                sys.exit(1)

        def __call__(self, parser, namespace, values, option_string=None):
            cls = TunableManager

            file_name = os.path.abspath(values)

            ext = os.path.splitext(file_name)
            ext = ext[1][1:].lower()

            if os.path.exists(file_name):
                if self.__class__.prompt_overwrite:
                    while True:
                        print("File \"%s\" already exists. Overwrite? [y/n]" % (file_name,))
                        result = input().lower()
                        if result in ['y', 'n']:
                            break

                    if result != 'y':
                        return self.finish()
                else:
                    return self.finish()

            print("Saving tunables to \"%s\" ..." % (file_name,))

            if ext == 'conf':
                with open(file_name, 'w+') as f:
                    f.write(cls.get_config_representation())

            elif ext == 'json':
                with open(file_name, 'w+') as f:
                    json.dump(
                        cls.get_representation(),
                        f,
                        sort_keys=True, indent=4, separators=(',', ': '))

            elif ext == 'yaml':
                if not yaml:
                    raise RuntimeError('yaml library missing!')

                with open(file_name, 'w+') as f:
                    yaml.dump(
                        cls.get_representation(),
                        f,
                        default_flow_style=False)

            elif ext == 'xml':
                raise RuntimeError('XML output currently not supported.')

            elif ext == 'der':
                if not pyasn1:
                    raise RuntimeError('pyasn1 library missing!')
                with open(file_name, 'wb+') as f:
                    f.write(cls.get_serializer().get_der())

            self.finish()

    class SetTunableAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            pieces = values.split('=')

            k = pieces[0]
            remainder = '='.join(pieces[1:])

            TunableManager.set(k, remainder)

    @classmethod
    def load(cls, tunables):
        cls.init()

        for key, value in tunables.items():
            cls.set(key, value)

    @classmethod
    def set(cls, key, value):
        existing = cls.get_multi_dict()

        if key not in existing:
            raise TunableError("Tunable \"%s\" does not exist." % (key,))

        class_ = existing[key]

        class_.set(value)

    @classmethod
    def init(cls):
        for class_ in cls.get_multi_dict().values():
            class_.reset()

    @classmethod
    def get_representation(cls):
        return {k: v.value for k, v in cls.get_semilong_dict().items()}

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

    @staticmethod
    def _strip_main(kv):
        return {(k[len('__main__.'):] if '__main__.' in k else k): v for k, v in kv.items()}

    @classmethod
    def get_semilong_dict(cls):
        return cls._strip_main(cls.get_long_dict())

    @classmethod
    def get_multi_dict(cls):
        merged = {}
        long = cls.get_long_dict()
        merged.update(long)
        merged.update(cls._strip_main(long))
        merged.update(cls.get_short_dict())

        return merged

    @classmethod
    def get(cls):
        return list(cls.get_long_dict().keys())

    @classmethod
    def get_config_representation(cls):
        result = [
            "### Tunables ###",
            ""
        ]

        for k, v in sorted(cls.get_semilong_dict().items()):
            result.append("# %s" % (v.documentation,))
            result.append("# type: %s" % (v.type_.__name__,))
            result.append("%s=%s" % (k, str(v.value),))
            result.append("")

        return "\n".join(result)

    @classmethod
    def get_serializer(cls, everything=False):
        serializer = Asn1Serializer()
        the_dict = {}

        for name, value in cls.get_long_dict().items():
            if value.hash or everything:
                the_dict[name] = value.value

        serializer.add_tunables(the_dict)

        return serializer

    @classmethod
    def get_hash(cls):
        return cls.get_serializer().get_sha512()

    @classmethod
    def get_hash_version(cls):
        return ASN1_SCHEMA_VERSION


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
                elif hasattr(Tunable, k):
                    setattr(IntermediateTunable, k, v)
                else:
                    raise TunableError('Unsupported attribute \"%s\"' % (k,))

            return IntermediateTunable
