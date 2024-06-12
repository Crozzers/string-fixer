"This string will not be converted because 'escaping the substring' will cause more escapes"

"This string will be converted and the substring will be \"unescaped\""

"This string will not be converted, but the substring will be \'unescaped\'"

"""Unescaped \\"quotations\\" shouldn't be affected"""

'''Unescaped \\'quotations\\' shouldn't be affected'''

"""'''Nested triple quote won't be converted'''"""

"""\'\'\'Escaped nested triple quote should be unescaped\'\'\'"""

"This string has 'two escapes' but by keeping \"the original\" quote style we can actually reduce the number of \'escapes\' to 1"
