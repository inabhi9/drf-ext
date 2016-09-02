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
