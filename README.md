# Python Validation

![Python](https://img.shields.io/badge/python-3.6%2C%203.7-blue.svg)

General purpose validation.

```python
from osnk.validations import Validation, requires


def fn(message):
    if 'Bad' in message:
        return 'Not good!'


good = Validation()
good.validate = fn


def fn(message):
    if len(message) > 8:
        return 'Not fit!'


fit = Validation()
fit.validate = fn


@requires(good & fit)
def echo(message):
    return message


assert echo('Bad') == 'Not good!'
assert echo('A' * 9) == 'Not fit!'
assert echo('Hello!') == 'Hello!'
```

## Installation

```bash
python -m pip install -U -e git+https://github.com/oshinko/pyvalidation.git#egg=validation
```
