from __future__ import division

import re
import numpy as np

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

    def __str__(self, infix=True):
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
    def substitute(self, subs):
        raise NotImplementedError

    def _substitute_arg(self, arg, subs):
        if isinstance(arg, Expression):
            return arg.substitute(subs)
        elif isinstance(arg, Variable) and arg.token in subs:
            return Constant(subs[arg.token])
        else:
            return arg

    def eval(self):
        string = re.sub('\.([a-zA-Z]+)', lambda x: 'np' + x.group(0), str(self))
        try:
            return eval(string)
        except Exception:
            return np.nan


class UnaryExpression(Expression):
    def __init__(self, op, arg1):
        self.op = op
        self.arg1 = arg1

    def substitute(self, subs):
        return UnaryExpression(self.op,
                               self._substitute_arg(self.arg1, subs))

    def __str__(self, infix=True):
        if infix:
            return str(self.op) + '(' + self.arg1.__str__(infix) + ')'
        else:
            return self.arg1.__str__(infix) + ' ' + str(self.op)

    __repr__ = __str__


class BinaryExpression(Expression):
    def __init__(self, op, arg1, arg2):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def substitute(self, subs):
        return BinaryExpression(self.op,
                                self._substitute_arg(self.arg1, subs),
                                self._substitute_arg(self.arg2, subs))

    def __str__(self, infix=True):
        if infix:
            return '(' + self.arg1.__str__(infix) + str(self.op) + self.arg2.__str__(infix) + ')'
        else:
            return self.arg1.__str__(infix) + ' ' + self.arg2.__str__(infix) + ' ' + str(self.op)

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

def _pull_unaries(tokens):
    new_tokens = [tokens[-1]]
    for i in range(len(tokens)-2, -1, -1):
        if type(tokens[i]) == Operator and (i == 0 or type(tokens[i-1]) == Operator):
            last = new_tokens.pop(0)
            new_tokens.insert(0, UnaryExpression(tokens[i], last))
        else:
            new_tokens.insert(0, tokens[i])
    return new_tokens

def _pull_binaries(tokens, ops, rtl=False):
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
    tokens = _pull_unaries(tokens)
    tokens = _pull_binaries(tokens, [Operator('^')], rtl=True)
    tokens = _pull_binaries(tokens, [Operator('*'), Operator('/')])
    tokens = _pull_binaries(tokens, [Operator('+'), Operator('-')])

    if len(tokens) > 1:
        raise ParseError('Incomplete syntax tree')

    return tokens[0]

def parse(string):
    tokens = _tokenize(string)
    expr = _syntax(tokens)
    return expr
