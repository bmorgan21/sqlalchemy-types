import sqlalchemy.types as stypes
import validation21 as vv


class Integer(stypes.Integer):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Integer(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None)))

        stypes.Integer.__init__(self, *args, **kwargs)


class BigInteger(stypes.BigInteger):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Integer(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None)))

        stypes.BigInteger.__init__(self, *args, **kwargs)


class Decimal(stypes.Numeric):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Decimal(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None),
                                                            rounding=kwargs.pop('rouding', None)))

        kwargs.setdefault('precision', 10)
        kwargs.setdefault('scale', 2)

        stypes.Numeric.__init__(self, *args, **kwargs)


class Currency(Decimal):
    def __init__(self, *args, **kwargs):
        kwargs['precision'] = 15
        Decimal.__init__(self, *args, **kwargs)


class Unicode(stypes.Unicode):
    def __init__(self, length, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Unicode(max_length=length,
                                                            truncate=kwargs.pop('truncate', None)))

        stypes.Unicode.__init__(self, length, *args, **kwargs)


class UnicodeText(stypes.UnicodeText):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Unicode())

        stypes.UnicodeText.__init__(self, *args, **kwargs)


class Enum(Unicode):
    def __init__(self, choices, length, *args, **kwargs):
        self.choices = choices
        kwargs.setdefault('validator', vv.Enum(choices, max_length=length))
        Unicode.__init__(self, length, *args, **kwargs)


class Date(stypes.Date):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Date())

        stypes.Date.__init__(self, *args, **kwargs)


class Time(stypes.Time):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Time())

        stypes.Time.__init__(self, *args, **kwargs)


class DateTime(stypes.DateTime):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.DateTime())

        stypes.DateTime.__init__(self, *args, **kwargs)


class Boolean(stypes.Boolean):
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', vv.Boolean())

        stypes.Boolean.__init__(self, *args, **kwargs)


class Type(Integer):
    def __init__(self, choices, *args, **kwargs):
        self.choices = choices
        kwargs.setdefault('validator', vv.Type(choices))
        Integer.__init__(self, *args, **kwargs)


class PhoneNumber(Unicode):
    def __init__(self, *args, **kwargs):
        kwargs.pop('length', None)
        Unicode.__init__(self, 10, *args, **kwargs)


class PhoneExt(Unicode):
    def __init__(self, *args, **kwargs):
        kwargs.pop('length', None)
        Unicode.__init__(self, 6, *args, **kwargs)


class Email(Unicode):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validator', vv.Email())

        kwargs.pop('length', None)
        Unicode.__init__(self, 255, *args, **kwargs)


# Represents the value another table/objects PrimaryID. Similar to ForeignKey but does not enforce constraint.
class ObjectID(Integer):
    def __init__(self, *args, **kwargs):
        kwargs['min'] = 1
        Integer.__init__(self, *args, **kwargs)


class ZipCode5(Unicode):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validator', vv.ZipCode5())

        kwargs.pop('length', None)
        Unicode.__init__(self, 10, *args, **kwargs)


class ZipCodeExt(Unicode):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validator', vv.ZipCodeExt())

        kwargs.pop('length', None)
        Unicode.__init__(self, 4, *args, **kwargs)
