from datetime import datetime
import re

from sqlalchemy import Column, event
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declared_attr, has_inherited_table
from sqlalchemy.orm.exc import NoResultFound

import types as tt

from validation.exception import ValidationException

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def convert_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

class Base(object):
    __polymorphic__ = None

    @declared_attr
    def __tablename__(cls):
        if has_inherited_table(cls):
            return None
        return convert_to_underscore(cls.__name__)

    @declared_attr
    def row_type(cls):
        if not cls.__polymorphic__:
            return None

        if 'row_type' in cls.__dict__:
            return cls.row_type
        else:
            cls.row_type = d = Column('row_type', tt.Unicode(50))
            return d

    @declared_attr
    def __mapper_args__(cls):
        ret = {'polymorphic_identity': unicode(cls.__name__)}
        if not has_inherited_table(cls) and cls.__polymorphic__:
            ret['polymorphic_on'] = cls.row_type
        elif has_inherited_table(cls) and not cls.__polymorphic__:
            raise Exception('Please specify __polymorphic__=\'single\' on base class')
        return ret

    id = Column(tt.ObjectID(), primary_key=True)

    @staticmethod
    def create_factory(*field_args, **kwargs):
        @classmethod
        def for_value(cls, *value_args):
            try:
                q = cls.query

                for (field, value) in zip(field_args, value_args):
                    if isinstance(value, str):
                        value = unicode(value)
                    q = q.filter(getattr(cls, field) == value)

                if kwargs.get('uselist', False):
                    return q.all()
                return q.one()
            except NoResultFound, e:
                return cls()
        return for_value

    @property
    def exists(self):
        """Returns True when the object has been flushed to the database."""
        return bool(self.id)

    @property
    def type_id(self):
        """Utility method that returns a tuple containing the class name and the id of the object."""
        return (unicode(self.__class__.__name__), self.id)

    def to_json(self, recurse=None):
        result = {'id':self.id,
                  '__class__':self.__class__.__name__,
                  }

        if recurse is not None and self.__class__ in recurse:
            result['recurse'] = True

        return result

class BasePlus(Base):
    @classmethod
    def for_id(cls, id):
        if id is None: return cls()
        if isinstance(id, cls): #allows some shortcuts
            return id

        # for the query below to be cached correctly by sqlalchemy,
        # the id needs to be an int
        try:
            id = int(id)
        except ValueError:
            pass
        try:
            value = cls.query.get(id)
            if value is None: value = cls()
            return value
        except NoResultFound, e:
            return cls()

    @staticmethod
    def for_type_id(type_id):
        """Returns a object constructed for the given type"""
        return getattr(__import__('openmile.model', globals(), locals(), [str(type_id[0])]), type_id[0]).for_id(type_id[1])

    @staticmethod
    def cls(type):
        return getattr(__import__('openmile.model', globals(), locals(), [str(type)]), type)

class SessionBase(object):
    @classproperty
    @classmethod
    def query(cls):
        return cls.db_session().query(cls)

    @classmethod
    def db_session(cls):
        return cls.__db_session__

    def add(self):
        self.db_session().add(self)
        return self

    def delete(self):
        self.db_session().delete(self)
        return self

class Timestamp(object):
    created_at = Column(tt.DateTime(), nullable=False, default=datetime.utcnow)
    last_updated = Column(tt.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Validate(object):
    def __setattr__(self, key, value):
        if isinstance(value, Base):
            if not value in self.db_session():
                raise Exception('assigned object isn\'t added to session [%s]' % key)

        if hasattr(self, '__read_only__'):
            if key.startswith('__') and key.endswith('__'):
                nkey = key[2:-2]
                if nkey in self.__read_only__:
                    key = nkey
            elif key in self.__read_only__:
                raise Exception('%s.%s is readonly' % (self.__class__.__name__, key))

        value_changed = True
        if self.__table__.columns.has_key(key):
            field = self.__table__.columns.get(key)
            try:
                value = field.type.validator.to_python(value)
            except AttributeError as exc:
                # this column does not have a validator, just let it go through
                pass
            current_value = getattr(self, key)
            value_changed = value != current_value
        if value_changed:
            object.__setattr__(self, key, value)

    def is_empty(self, value):
        # None and '' are "empty"
        return value is None or value == '' or (
            isinstance(value, (list, tuple, dict)) and not value)

    def is_changed(self, field_name):
        (added, unchanged, deleted) = getattr(self.__class__, field_name).get_history(self)
        return bool(added or deleted)

    @classmethod
    def handle_event(cls, session, flush_context, instances):
        for obj in session.new | session.dirty:
            if isinstance(obj, cls):
                obj.validate()

    def validate(self):
        errors = {}

        self._default()

        for field in self.__table__.columns:
            value = getattr(self, field.name)
            if not field.nullable and self.is_empty(field.default) and not field.primary_key and self.is_empty(value) and len(field.foreign_keys)==0 :
                errors[field.name] = ValidationException('Please enter a value',
                                                         field=field.name,
                                                         table=self.__class__.__name__)

        if not errors:
            try:
                self._validate()
            except ValidationException, e:
                errors = ValidationException.merge_errors(errors, e)

        if errors:
            raise ValidationException(error_dict=errors)

    def _validate(self):
        pass

    def _default(self):
        pass

event.listen(Session, 'before_flush', Validate.handle_event)
