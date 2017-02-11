import sqlalchemy.types as stypes
import validation21 as vv


class Integer(stypes.Integer):
    def __init__(self, **kwargs):
        self.validator = kwargs.pop('validator', vv.Integer(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None)))

        stypes.Integer.__init__(self)


class BigInteger(stypes.BigInteger):
    def __init__(self, **kwargs):
        self.validator = kwargs.pop('validator', vv.Integer(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None)))

        stypes.BigInteger.__init__(self)


class Decimal(stypes.Numeric):
    def __init__(self, precision=10, scale=2, decimal_return_scale=None, asdecimal=True, **kwargs):
        self.validator = kwargs.pop('validator', vv.Decimal(min=kwargs.pop('min', None),
                                                            max=kwargs.pop('max', None),
                                                            rounding=kwargs.pop('rouding', None)))

        stypes.Numeric.__init__(self, precision=precision, scale=scale, decimal_return_scale=decimal_return_scale, asdecimal=asdecimal)


class Currency(Decimal):
    def __init__(self, precision=15, scale=None, decimal_return_scale=None, asdecimal=True, **kwargs):
        Decimal.__init__(self, precision=precision, scale=scale, decimal_return_scale=decimal_return_scale, asdecimal=asdecimal, **kwargs)


class Unicode(stypes.Unicode):
    def __init__(self, length=None, **kwargs):
        self.validator = kwargs.pop('validator', vv.Unicode(max_length=length,
                                                            truncate=kwargs.pop('truncate', None)))

        stypes.Unicode.__init__(self, length=length, **kwargs)


class UnicodeText(stypes.UnicodeText):
    def __init__(self, length=None, **kwargs):
        self.validator = kwargs.pop('validator', vv.Unicode())

        stypes.UnicodeText.__init__(self, length=length, **kwargs)


class Enum(Unicode):
    def __init__(self, choices, length, **kwargs):
        self.choices = choices
        kwargs.setdefault('validator', vv.Enum(choices, max_length=length))
        Unicode.__init__(self, length=length, **kwargs)


class Date(stypes.Date):
    def __init__(self, **kwargs):
        self.validator = kwargs.pop('validator', vv.Date())

        stypes.Date.__init__(self)


class Time(stypes.Time):
    def __init__(self, timezone=False, **kwargs):
        self.validator = kwargs.pop('validator', vv.Time())

        stypes.Time.__init__(self, timezone=timezone)


class DateTime(stypes.DateTime):
    def __init__(self, timezone=False, **kwargs):
        self.validator = kwargs.pop('validator', vv.DateTime())

        stypes.DateTime.__init__(self, timezone=timezone)


class Boolean(stypes.Boolean):
    def __init__(self, create_constraint=True, name=None, _create_events=True, **kwargs):
        self.validator = kwargs.pop('validator', vv.Boolean())

        stypes.Boolean.__init__(self, create_constraint=create_constraint, name=name, _create_events=_create_events)


class Type(Integer):
    def __init__(self, choices, **kwargs):
        self.choices = choices
        kwargs.setdefault('validator', vv.Type(choices))
        Integer.__init__(self, **kwargs)


class PhoneNumber(Unicode):
    def __init__(self, **kwargs):
        kwargs.pop('length', None)
        Unicode.__init__(self, length=10, **kwargs)


class PhoneExt(Unicode):
    def __init__(self, **kwargs):
        kwargs.pop('length', None)
        Unicode.__init__(self, length=6, **kwargs)


class Email(Unicode):
    def __init__(self, **kwargs):
        kwargs.setdefault('validator', vv.Email())

        kwargs.pop('length', None)
        Unicode.__init__(self, length=255, **kwargs)


# Represents the value another table/objects PrimaryID. Similar to ForeignKey but does not enforce constraint.
class ObjectID(Integer):
    def __init__(self, **kwargs):
        kwargs['min'] = 1
        Integer.__init__(self, **kwargs)


class ZipCode5(Unicode):
    def __init__(self, **kwargs):
        kwargs.setdefault('validator', vv.ZipCode5())

        kwargs.pop('length', None)
        Unicode.__init__(self, length=10, **kwargs)


class ZipCodeExt(Unicode):
    def __init__(self, **kwargs):
        kwargs.setdefault('validator', vv.ZipCodeExt())

        kwargs.pop('length', None)
        Unicode.__init__(self, length=4, **kwargs)
