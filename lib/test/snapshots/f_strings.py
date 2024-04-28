'''
Collection of python version agnostic f-string related tests.

These tests should result in the same output regardless of the python version being used.
'''

abc = '123'

normal = f'some string {abc}'

normal_with_other_stuff = f'some \'quotes\' and such: \'{abc}\' and \'\'\'other\'\'\''
