'''
Collection of f-string related tests specific to Python 3.12 and later.

The main change is allowing any python expression in an f-string, even with the same
quote type.

This is very convenient for string-fixer because it drastically simplifies how we can process
these strings.

See also:
https://docs.python.org/3/whatsnew/3.12.html#whatsnew312-pep701
'''
some_dict = {
    'a': 0,
    'b': 1
}

nested_classic = f'value: {some_dict['a']}'
nested_classic2 = f'value: {some_dict['a']}'

# see: https://stackoverflow.com/q/41215365
x = 42
unreadable = f'-{f'*{f'+{f'.{x}.'}+'}*'}-'
