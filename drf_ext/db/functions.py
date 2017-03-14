from django.db.models import CharField, Value
from django.db.models.aggregates import Aggregate
from django.db.models.expressions import Func


class Cast(Func):
    function = 'CAST'
    template = '%(function)s(%(expressions)s AS %(datatype)s)'

    FLOAT = 'FLOAT'

    def __init__(self, expression, **extra):
        super(Cast, self).__init__(expression, **extra)


class Replace(Func):
    function = 'REPLACE'
    template = "%(function)s(%(expressions)s, '%(pattern)s', '%(replacement)s')"

    def __init__(self, column, pattern, replacement, **extra):
        extra['pattern'] = pattern
        extra['replacement'] = replacement
        super(Replace, self).__init__(column, **extra)


class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(expressions)s)'

    def __init__(self, expression, delimiter, order_by=None, **extra):
        output_field = extra.pop('output_field', CharField())
        delimiter = Value(delimiter)

        super(GroupConcat, self).__init__(
            expression, delimiter, output_field=output_field, **extra)

    def as_postgresql(self, compiler, connection):
        self.function = 'STRING_AGG'
        return super(GroupConcat, self).as_sql(compiler, connection)
