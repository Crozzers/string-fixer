'''
Collection of f-string related tests specific to Python 3.11 and earlier (pre pep 701).
'''
some_dict = {
    'a': 0,
    'b': 1
}

nested_classic = f'value: {some_dict["a"]}'
nested_classic2 = f"value: {some_dict['a']}"

# see: https://stackoverflow.com/q/41215365
x = 42
# check quote_order is followed (single first and triple if needed)
unreadable = f"""-{f'''*{f"+{f'.{x}.'}+"}*'''}-"""

# check quote_order is followed with simple strings inside nested f-strings
unreadable_with_simple_strings = f'''-{f"""*{f"+{"abcdef"}+"} {"abcdef"} *""" }-'''
