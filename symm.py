import re

class ParseError(Exception):
    pass


class Symbol(object):
    regex = ''

    def __init__(self, token):
        self.token = token

    @classmethod
    def match(cls, string):
        match = re.match(cls.regex, string)
        if match:
            return cls(string[:match.end()]), string[match.end():]
        else:
            return None, string

    def __str__(self):
        return str(self.token)

    __repr__ = __str__

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.token == other.token
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Variable(Symbol):
    regex = '[a-zA-Z]'

    def __init__(self, token):
        super(Variable, self).__init__(token)


class Constant(Symbol):
    regex = '[0-9]+'

    def __init__(self, token):
        super(Constant, self).__init__(token)


class Operator(Symbol):
    regex = '\+|-|\*|/|\^|(\.[a-z0-9]+)'

    def __init__(self, token):
        if token == '^':
            token = '**'
        super(Operator, self).__init__(token)


class Parenthesis(Symbol):
    regex = '[()[\]{}]'

    def __init__(self, token):
        if token == '[' or token == '{':
            token = '('
        elif token == ']' or token == '}':
            token = ')'
        super(Parenthesis, self).__init__(token)


class Expression(object):
    pass


class UnaryExpression(Expression):
    def __init__(self, op, arg1):
        self.op = op
        self.arg1 = arg1

    def __str__(self):
        return str(self.op) + '(' + str(self.arg1) + ')'

    __repr__ = __str__


class BinaryExpression(Expression):
    def __init__(self, op, arg1, arg2):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self):
        return '(' + str(self.arg1) + str(self.op) + str(self.arg2) + ')'

    __repr__ = __str__


def _tokenize(string):
    cases = Symbol.__subclasses__()
    string = string.lstrip()
    tokens = []
    while len(string) > 0:
        old_string = string
        for case in cases:
            match, rest = case.match(string)
            if match:
                tokens.append(match)
                string = rest.lstrip()
                break
        if string == old_string:  # didn't parse anything
            print 'ERROR: ' + string[0]
            break
    return tokens

def pull_unaries(tokens):
    new_tokens = [tokens[-1]]
    for i in range(len(tokens)-2, -1, -1):
        if type(tokens[i]) == Operator and (i == 0 or type(tokens[i-1]) == Operator):
            last = new_tokens.pop(0)
            new_tokens.insert(0, UnaryExpression(tokens[i], last))
        else:
            new_tokens.insert(0, tokens[i])
    return new_tokens

def pull_binaries(tokens, ops, rtl=False):
    if not rtl:
        new_tokens = [tokens[0]]
        i = 1
        while i < len(tokens):
            if tokens[i] in ops:
                arg1, arg2 = new_tokens.pop(), tokens[i+1]
                new_tokens.append(BinaryExpression(tokens[i], arg1, arg2))
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
    else:  # rtl
        new_tokens = [tokens[-1]]
        i = len(tokens)-2
        while i >= 0:
            if tokens[i] in ops:
                arg1, arg2 = tokens[i-1], new_tokens.pop(0)
                new_tokens.insert(0, BinaryExpression(tokens[i], arg1, arg2))
                i -= 2
            else:
                new_tokens.insert(0, (tokens[i]))
                i -= 1
    return new_tokens

def _syntax(tokens):
    # remove parens
    while Parenthesis(')') in tokens:
        close_idx = tokens.index(Parenthesis(')'))
        open_idx = close_idx-1
        while tokens[open_idx] != Parenthesis('(') and open_idx > 0:
            open_idx -= 1
        if tokens[open_idx] != Parenthesis('('):
            raise ParseError('Mismatched parentheses')
        tokens = tokens[:open_idx] + [_syntax(tokens[open_idx+1:close_idx])] + tokens[close_idx+1:]
    if Parenthesis('(') in tokens:
        raise ParseError('Mismatched parentheses')

    # insert implicit mults
    new_tokens = [tokens[0]]
    for i in range(1, len(tokens)):
        if type(tokens[i-1]) != Operator and type(tokens[i]) != Operator:
            new_tokens.append(Operator('*'))
        new_tokens.append(tokens[i])
    tokens = new_tokens

    # apply order of operations to build expressions
    tokens = pull_unaries(tokens)
    tokens = pull_binaries(tokens, [Operator('^')], rtl=True)
    tokens = pull_binaries(tokens, [Operator('*'), Operator('/')])
    tokens = pull_binaries(tokens, [Operator('+'), Operator('-')])

    if len(tokens) > 1:
        raise ParseError('Incomplete syntax tree')

    return tokens[0]

def eval(expr):
    pass

def parse(string):
    tokens = _tokenize(string)
    expr = _syntax(tokens)
    return expr
