from datetime import datetime
import re

from sqlalchemy import Column, ForeignKey, event, exists
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declared_attr, has_inherited_table
from sqlalchemy.orm.exc import NoResultFound

import types as tt

from validation21.exception import ValidationException


def _get_parent_table_class(cls):
    if not has_inherited_table(cls):
        #  Safety against recursion
        return None

    base_classes = [b for b in cls.__bases__ if b.__tablename__]
    if len(base_classes) > 1:
        #  For simplicity at present, only allow join configurations IFF there's only one parent table class
        raise Exception('Can only inherit from one base class with defined table')

    return base_classes[0]


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


OrigColumn = Column


class Column(OrigColumn):
    def __init__(self, *args, **kwargs):
        if 'default' in kwargs:
            if 'server_default' not in kwargs:
                default = kwargs['default']
                if isinstance(default, bool):
                    default = "'1'" if default else "'0'"
                elif isinstance(default, (int, float)):
                    scale = getattr(args[0], 'scale', None)
                    if scale:
                        default = "'{{:.{}f}}'".format(scale).format(default)
                    else:
                        default = "'{}'".format(default)
                elif isinstance(default, (str, unicode)):
                    default = default
                elif default is None:
                    default = text('NULL')
                elif default == datetime.utcnow:
                    default = text('CURRENT_TIMESTAMP')
                else:
                    raise Exception('Unable to infer a valid server_default from default: {}'.format(default))
                kwargs['server_default'] = default
        OrigColumn.__init__(self, *args, **kwargs)


class Base(object):
    __polymorphic__ = None
    __immutable__ = False

    @declared_attr
    def __tablename__(cls):

        table_name = None

        if has_inherited_table(cls):
            if cls.__polymorphic__ == 'single':
                #  Single implies we are extending an existing table
                #  in which case SQLAlchemy should not be provided a new one
                return None
            elif cls.__polymorphic__ == 'join':
                parent = _get_parent_table_class(cls)
                table_name = "{}{}".format(parent.__name__, cls.__name__)
                # hack to make sure we can redefine id in a subclass
                cls.id = Column(tt.ObjectID(), ForeignKey("{}.id".format(parent.__tablename__)), primary_key=True)
        else:
            table_name = cls.__name__

        return convert_to_underscore(table_name)

    @declared_attr
    def row_type(cls):
        if not cls.__polymorphic__:
            return None

        if 'row_type' in cls.__dict__:
            return cls.row_type
        else:
            cls.row_type = d = Column('row_type', tt.Unicode(50), index=True)
            return d

    @declared_attr
    def __mapper_args__(cls):
        ret = {'polymorphic_identity': unicode(cls.__name__)}
        if not has_inherited_table(cls) and cls.__polymorphic__:
            ret['polymorphic_on'] = cls.row_type
        elif has_inherited_table(cls) and not cls.__polymorphic__:
            raise Exception('Please specify __polymorphic__=\'single\' or __polymorphic__=\'join\' on base class')
        return ret

    @declared_attr
    def id(cls):
        return Column(tt.ObjectID(), primary_key=True)

    @property
    def exists(self):
        """Returns True when the object has been flushed to the database."""
        return bool(self.id)

    @classmethod
    def exists_by_id(cls, session, id):
        """Returns True if the object exists in the database."""
        return session.query(exists().where(cls.id == id)).scalar()

    @property
    def type_id(self):
        """Utility method that returns a tuple containing the class name and the id of the object."""
        return (unicode(self.__class__.__name__), self.id)

    def to_json(self, recurse=None):
        result = {'id': self.id,
                  '__class__': self.__class__.__name__,
                  }

        if recurse is not None and self.__class__ in recurse:
            result['recurse'] = True

        return result

    @classmethod
    def before_flush(cls, session, flush_context, instances):
        for obj in session.dirty | session.deleted:
            if isinstance(obj, cls) and cls.__immutable__:
                raise Exception('Object is immutable: {}'.format(cls.__name__))

event.listen(Session, 'before_flush', Base.before_flush)


class BaseWithQuery(Base):
    @classmethod
    def for_id(cls, id, options=None):
        if id is None:
            return cls()
        if isinstance(id, cls):  # allows some shortcuts
            return id

        # for the query below to be cached correctly by sqlalchemy,
        # the id needs to be an int
        try:
            id = int(id)
        except ValueError:
            pass
        try:
            query = cls.query
            if options:
                query = query.options(*options)

            value = query.get(id)
            if value is None:
                value = cls()
            return value
        except NoResultFound:
            return cls()

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

                options = kwargs.get('options')
                if options:
                    q = q.options(*options)

                if kwargs.get('uselist', False):
                    return q.all()
                return q.one()
            except NoResultFound:
                return cls()
        return for_value


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
    modified_at = Column(tt.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Validate(object):
    def __setattr__(self, key, value):
        # if isinstance(value, Base):
        #     if value not in self.db_session():
        #         raise Exception('assigned object isn\'t added to session [%s]' % key)

        if hasattr(self, '__read_only__'):
            if key.startswith('__') and key.endswith('__'):
                nkey = key[2:-2]
                if nkey in self.__read_only__:
                    key = nkey
            elif key in self.__read_only__:
                raise Exception('%s.%s is readonly' % (self.__class__.__name__, key))

        value_changed = True
        current_value = None
        attribute = self.__mapper__.class_manager.get(key)
        if attribute is not None and hasattr(attribute, 'type'):
            try:
                value = attribute.type.validator.to_python(value)
            except AttributeError:
                # this column does not have a validator, just let it go through
                pass
            except ValidationException, e:
                e.field = key
                raise
            current_value = getattr(self, key)
            value_changed = value != current_value

        if value_changed:
            is_set = False
            if hasattr(self.__class__, key):
                attr = getattr(self.__class__, key)
                if isinstance(attr, property):
                    for v in self.__class__.__dict__.values():
                        if isinstance(v, property) and \
                           v.fget == attr.fget and \
                           v.fset is not None:
                            v.fset(self, value)
                            is_set = True
                            break

            if not is_set:
                object.__setattr__(self, key, value)

            if hasattr(self, 'changed'):
                self.changed(key, current_value, value)

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

        for key, attribute in self.__mapper__.class_manager.items():
            if hasattr(attribute, 'type'):
                if not attribute.nullable and self.is_empty(attribute.default) and not attribute.primary_key and len(attribute.foreign_keys) == 0:
                    value = getattr(self, key)
                    if self.is_empty(value):
                        errors[key] = ValidationException('Please enter a value',
                                                          field=key,
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
