from symm import _tokenize, parse

test_strs = ['-2/5x + 3yz - .sqrt 7',
             '(-b+.sqrt(b^2-4ac))/(2a)',
             'n(n+1)(2n+1)/6',
             'a^b^c',
             'ab + bc + ac',
             '(x+y)(x-y) - x^2 + y^2']

for test_str in test_strs:
    print test_str
    print _tokenize(test_str)
    print parse(test_str)
    print ''
