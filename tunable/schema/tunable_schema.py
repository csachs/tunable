# Auto-generated by asn1ate on 2017-05-22 14:59:14.572726
from pyasn1.type import char, namedtype, univ

# constraint, namedval, tag, useful


class TunableType(univ.Choice):
    pass


TunableType.componentType = namedtype.NamedTypes(
    namedtype.NamedType('boolValue', univ.Boolean()),
    namedtype.NamedType('intValue', univ.Integer()),
    namedtype.NamedType('floatValue', univ.Real()),
    namedtype.NamedType('stringValue', char.UTF8String()),
    namedtype.NamedType('bytesValue', univ.OctetString()),
)


class Tunable(univ.Sequence):
    pass


Tunable.componentType = namedtype.NamedTypes(
    namedtype.NamedType('name', char.UTF8String()),
    namedtype.NamedType('value', TunableType()),
)


class Version(univ.Integer):
    pass


class TunableSequenceType(univ.SequenceOf):
    pass


TunableSequenceType.componentType = Tunable()


class TunablesList(univ.Sequence):
    pass


TunablesList.componentType = namedtype.NamedTypes(
    namedtype.NamedType('version', Version()),
    namedtype.NamedType('tunables', TunableSequenceType()),
)
