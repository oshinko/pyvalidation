import inspect
import functools


class MixedValidation:
    def __init__(self, left, right, any=False):
        self.any = any
        self.left = left
        self.right = right

    def __and__(self, other):
        if isinstance(other, (MixedValidation, Validation)):
            return MixedValidation(self, other)
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, (MixedValidation, Validation)):
            return MixedValidation(self, other, any=True)
        return NotImplemented

    def validate(self, *args, **kwargs):
        left = self.left.validate(*args, **kwargs)
        if self.any:
            if left:
                right = self.right.validate(*args, **kwargs)
                return left if right else None
        else:
            return left if left else self.right.validate(*args, **kwargs)


class Validation:
    def __and__(self, other):
        if isinstance(other, (MixedValidation, Validation)):
            return MixedValidation(self, other)
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, (MixedValidation, Validation)):
            return MixedValidation(self, other, any=True)
        return NotImplemented

    def validate(self, *args, **kwargs):
        raise NotImplementedError()


class PassableValidationResult:
    def __init__(self, validations, error=None):
        if isinstance(validations, (tuple, list)):
            self.validations = validations
        else:
            self.validations = (validations,)
        self.error = error


class PassableMixedValidation:
    def __init__(self, left, right, any=False):
        self.any = any
        self.left = left
        self.right = right

    def validate(self, *args, **kwargs):
        left, left_error = self.left.validate(*args, **kwargs)
        if self.any:
            if left_error:
                right, right_error = self.right.validate(*args, **kwargs)
                return left + right, left_error if right_error else None
            return left, left_error
        if left_error:
            return left, left_error
        right, right_error = self.right.validate(*args, **kwargs)
        return left + right, right_error


class PassableValidation:
    def __init__(self, validation):
        self.validation = validation

    def validate(self, *args, **kwargs):
        e = self.validation.validate(*args, **kwargs)
        return ((self.validation, bool(e)),), e


def passable(validation):
    if isinstance(validation, MixedValidation):
        left = passable(validation.left)
        right = passable(validation.right)
        return PassableMixedValidation(left, right, any=validation.any)
    return PassableValidation(validation)


def requires(validation, passedkey='passed'):
    """Validator.

    >>> def fn(s):
    ...     if 'ab' not in s:
    ...         return 'Invalid'
    >>> ab = Validation()
    >>> ab.validate = fn
    >>> def fn(s):
    ...     if 'cd' not in s:
    ...         return 'Invalid'
    >>> cd = Validation()
    >>> cd.validate = fn
    >>> def fn(s):
    ...     if 'ef' not in s:
    ...         return 'Invalid'
    >>> ef = Validation()
    >>> ef.validate = fn
    >>> def fn(s):
    ...     if 'gh' not in s:
    ...         return 'Invalid'
    >>> gh = Validation()
    >>> gh.validate = fn
    >>> @requires(ab | cd & (ef | gh))
    ... def test(s, passed):
    ...     return (s, *passed)
    >>> assert ('abcdefgh', ab) == test('abcdefgh')
    >>> assert ('cdefgh', cd, ef) == test('cdefgh')
    >>> assert ('cdgh', cd, gh) == test('cdgh')
    """
    def w(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            argspec = inspect.getfullargspec(fn)
            if passedkey in argspec.args + argspec.kwonlyargs:
                results, error = passable(validation).validate(*args, **kwargs)
                if error:
                    return error
                kwargs[passedkey] = tuple(v for v, e in results if not e)
                return fn(*args, **kwargs)
            else:
                r = validation.validate(*args, **kwargs)
                return r if r else fn(*args, **kwargs)
        return wrapper
    return w
