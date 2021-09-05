import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from base64 import b64encode
from io import BytesIO, StringIO

from .tunable import Tunable, TunableError

try:
    import pyasn1
    from pyasn1.codec.der.decoder import decode as der_decode
    from pyasn1.codec.der.encoder import encode as der_encode
    from pyasn1.codec.native.encoder import encode as native_encode

    from .schema import ASN1_SCHEMA_VERSION
    from .schema import tunable_schema as schema
except ImportError:
    pyasn1 = None

try:
    import yaml
except ImportError:
    yaml = None


class Serializer(object):
    need_binary = False

    _bool = 'boolValue'
    _bytes = 'bytesValue'
    _str = 'stringValue'
    _int = 'intValue'
    _float = 'floatValue'

    type_to_name = {bool: _bool, bytes: _bytes, str: _str, int: _int, float: _float}

    simple_types = {_int, _float, _str}

    def serialize(self, fp, **kwargs):
        pass

    def deserialize(self, fp):
        pass


class XmlSerializer(Serializer):
    need_binary = True

    def serialize(self, fp, tunables=None, **kwargs):
        tl = ET.Element('TunablesList')
        tree = ET.ElementTree(tl)
        version = ET.SubElement(tl, 'version')
        version.text = str(ASN1_SCHEMA_VERSION)

        t = ET.SubElement(tl, 'tunables')

        for k, v in sorted(tunables.items()):
            tunable = ET.SubElement(t, 'Tunable')
            name = ET.SubElement(tunable, 'name')
            name.text = k

            value = ET.SubElement(tunable, 'value')

            the_value = v.value
            tag_name = self.type_to_name[type(the_value)]

            inner = ET.SubElement(value, tag_name)

            if tag_name in self.simple_types:
                inner.text = str(the_value)
            elif tag_name == self._bool:
                if the_value:
                    ET.SubElement(inner, 'true')
                else:
                    ET.SubElement(inner, 'false')
            elif tag_name == self._bytes:
                inner.text = ''.join('%02x' % b for b in the_value)

        tree.write(fp, encoding='utf-8', xml_declaration=True)

    def deserialize(self, fp):
        tree = ET.parse(fp)
        root = tree.getroot()

        assert int(next(root.iter('version')).text) == ASN1_SCHEMA_VERSION

        tl = next(root.iter('tunables'))

        results = {}

        for tunable in tl.iter('Tunable'):
            name = next(tunable.iter('name')).text
            value = next(iter(next(tunable.iter('value'))))

            if value.tag in self.simple_types:
                results[name] = value.text
            elif value.tag == self._bool:
                inner = next(iter(value)).tag
                assert inner in {'true', 'false'}
                results[name] = inner == 'true'
            elif value.tag == self._bytes:
                results[name] = bytes.fromhex(value.text)

        return results


class JsonSerializer(Serializer):
    def serialize(self, fp, representation=None, **kwargs):
        json.dump(representation, fp, sort_keys=True, indent=4, separators=(',', ': '))

    def deserialize(self, fp):
        return json.load(fp)


class YamlSerializer(Serializer):
    def __init__(self):
        if not yaml:
            raise RuntimeError('yaml library missing!')

    def serialize(self, fp, representation=None, **kwargs):
        yaml.dump(representation, fp, default_flow_style=False)

    def deserialize(self, fp):
        return yaml.load(fp)


class ConfigSerializer(Serializer):
    def serialize(self, fp, tunables=None, **kwargs):
        result = ["### Tunables ###", ""]

        for k, v in sorted(tunables.items()):
            # noinspection PyStatementEffect
            v.value
            if v.documentation:
                result.append("# %s" % (v.documentation.replace('\n', '\n# '),))
            result.append("# type: %s" % (v.type_.__name__,))
            result.append(
                "%s=%s"
                % (
                    k,
                    str(v.value),
                )
            )
            result.append("")

        fp.write("\n".join(result))

    def deserialize(self, fp):
        lines = fp.readlines()
        lines = [
            line.strip()
            for line in lines
            if len(line.strip()) > 0 and line.strip()[0] != '#'
        ]

        results = {}

        for line in lines:
            pieces = line.split('=')

            k = pieces[0]
            remainder = '='.join(pieces[1:])

            results[k] = remainder

        return results


class DerSerializer(Serializer):
    need_binary = True

    def __init__(self):
        if not pyasn1:
            raise RuntimeError('pyasn1 library missing!')

    def encode(self, tunables=None, everything=True, **kwargs):
        tl = schema.TunablesList()
        tl['version'] = ASN1_SCHEMA_VERSION
        tl['tunables'] = schema.TunableSequenceType()

        # to make it independent of collation rules,
        # sort it by its UTF-8 binary representation
        for name, tunable in sorted(tunables.items(), key=lambda ab: ab[0].encode()):

            value = tunable.value

            if not (tunable.hash or everything):
                continue

            t = schema.Tunable()

            tv = schema.TunableType()
            tv[self.type_to_name[type(value)]] = value

            t['name'] = name
            t['value'] = tv

            tl['tunables'].append(t)

        return der_encode(tl)

    def serialize(self, fp, tunables=None, **kwargs):
        fp.write(self.encode(tunables=tunables, **kwargs))

    def decode(self, data):
        decode_result, _ = der_decode(data, asn1Spec=schema.TunablesList())

        assert decode_result['version'] == ASN1_SCHEMA_VERSION

        result = {}

        for tunable in decode_result['tunables']:
            result[tunable['name']] = next(
                iter(native_encode(tunable['value']).values())
            )

        return result

    def deserialize(self, fp):
        return self.decode(fp.read())


SERIALIZERS = {
    'json': JsonSerializer,
    'yaml': YamlSerializer,
    'conf': ConfigSerializer,
    'der': DerSerializer,
    'xml': XmlSerializer,
}


class ShowTunablesAction(argparse._StoreTrueAction):
    quit_after_call = True  # False

    def __call__(self, parser, namespace, values, option_string=None):
        cs = ConfigSerializer()

        cs.serialize(sys.stdout, TunableManager.get_semilong_dict())

        if self.__class__.quit_after_call:
            sys.exit(1)


class LoadTunablesAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_name = os.path.abspath(values)

        ext = os.path.splitext(file_name)
        ext = ext[1][1:].lower()

        if ext not in SERIALIZERS:
            raise RuntimeError("Unsupported format %s." % (ext,))

        s = SERIALIZERS[ext]()

        with open(file_name, 'rb' if s.need_binary else 'r') as fp:
            TunableManager.load(s.deserialize(fp))


class SaveTunablesAction(argparse.Action):
    quit_after_call = True  # False
    prompt_overwrite = True  # False

    def finish(self):
        if self.__class__.quit_after_call:
            sys.exit(1)

    def __call__(self, parser, namespace, values, option_string=None):
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

        if ext not in SERIALIZERS:
            raise RuntimeError("Unsupported format %s." % (ext,))

        s = SERIALIZERS[ext]()

        # TODO: call get_serialization()?

        print("Saving tunables to \"%s\" ..." % (file_name,))

        with open(file_name, 'wb+' if s.need_binary else 'w+') as fp:
            s.serialize(
                fp,
                representation=TunableManager.get_representation(),
                tunables=TunableManager.get_semilong_dict(),
            )

        self.finish()


class SetTunableAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pieces = values.split('=')

        k = pieces[0]
        remainder = '='.join(pieces[1:])

        TunableManager.set(k, remainder)


class TunableManager(object):
    @classmethod
    def register_argparser(cls, parser, register=None):
        if register is None:
            register = {
                'show': (None, 'tunables-show'),
                'set': ('t', 'tunable'),
                'load': (None, 'tunables-load'),
                'save': (None, 'tunables-save'),
            }

        p = parser.prefix_chars[0:1]
        prefix = p * 2

        for k, v in list(register.items()):
            if v is None:
                continue

            v = tuple(vv for vv in v if vv)
            if len(v) == 2:
                vshort, vlong = v
                v = (
                    p + vshort,
                    prefix + vlong,
                )
            else:
                v = (prefix + v[0],)

            register[k] = v

        if register['set']:
            parser.add_argument(*register['set'], type=str, action=SetTunableAction)
        if register['show']:
            parser.add_argument(*register['show'], action=ShowTunablesAction)
        if register['load']:
            parser.add_argument(*register['load'], type=str, action=LoadTunablesAction)
        if register['save']:
            parser.add_argument(*register['save'], type=str, action=SaveTunablesAction)

    @classmethod
    def load(cls, tunables, reset=True):
        if reset:
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
        collection -= {Tunable}

        return list(
            sorted(
                collection,
                key=lambda p: (
                    p.__module__,
                    p.__name__,
                ),
            )
        )

    @classmethod
    def get_short_dict(cls):
        return {class_.__name__: class_ for class_ in cls.get_classes()}

    @classmethod
    def get_long_dict(cls):
        return {
            class_.__module__ + '.' + class_.__name__: class_
            for class_ in cls.get_classes()
        }

    @staticmethod
    def _strip_main(kv):
        return {
            (k[len('__main__.') :] if '__main__.' in k else k): v for k, v in kv.items()
        }

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
    def get_serialization(cls, extension='conf'):
        assert extension in SERIALIZERS

        serializer = SERIALIZERS[extension]()

        if serializer.need_binary:
            buf = BytesIO()
        else:
            buf = StringIO()

        serializer.serialize(
            buf,
            tunables=cls.get_semilong_dict(),
            representation=cls.get_representation(),
        )

        return buf.getvalue()

    @classmethod
    def get_hash(cls):
        serializer = DerSerializer()
        data = serializer.encode(tunables=cls.get_semilong_dict(), everything=False)

        hasher = hashlib.sha256()
        hasher.update(data)
        hash_value = b64encode(hasher.digest()).decode()

        return "VERSION:%d:SHA256:%s" % (ASN1_SCHEMA_VERSION, hash_value)
