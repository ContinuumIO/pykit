# -*- coding: utf-8 -*-

"""
Parse pykit IR.
"""

from __future__ import print_function, division, absolute_import
from pykit import types
from pykit.utils import match
from pykit.ir import Module, Function, Block, Op, Const, GlobalValue
import pgen2.parser, pgen2.pgen

# ______________________________________________________________________

to_type = lambda x: vars(types)[x]

@match
def _build(type, args):
    return args

@_build.case(type='global')
def _build_global(type, args):
    return GlobalValue(args[1], args[3])

@_build.case(type='function')
def _build_function(type, args):
    restype, name, func_args = args[1]
    argtypes, argnames = func_args[::2], func_args[1::2]
    type = types.Function(restype, argtypes)
    f = Function(name, argnames, type)

    blocks = args[2:-2] # omit the footer and newline
    for name, ops in blocks:
        f.add_block(name).extend(ops)

    return f

@_build.case(type='header')
def _build_header(type, args):
    restype, name = args[:2]
    func_args = args[3] if len(args) == 6 else []
    return restype, name, func_args

@_build.case(type='block')
def _build_block(type, args):
    name, ops = args[0], args[2:]
    return name, ops

@_build.case(type='type')
def _build_type(type, args):
    ty, tail = to_type(args[0]), args[1:]
    for i in range(len(tail)):
        ty = types.Pointer(ty)
    return ty

@_build.case(type='op')
def _build_op(type, args):
    if len(args) == 9:
        argnames = []
        _, dest, _, _, type, _, opname, _, _ = args
    else:
        _, dest, _, _, type, _, opname, _, argnames, _ = args

    if not isinstance(argnames, list):
        argnames = [argnames]

    return Op(opname, type, argnames, dest)

@_build.case(type='varname')
def _build_varname(type, args):
    return args[1]

@_build.case(type='id')
def _build_id(type, args):
    return args[0]

# ______________________________________________________________________

def build_ast(parse_result, symmap):
    """Built an AST from a parse tree and a symbol map"""
    (sym, tok, _), args = parse_result

    result = []
    for ((newsym, newtok, n), newargs) in args:
        if newtok not in ('NEWLINE', 'ENDMARKER'):
            if newsym in symmap:
                result.append(build_ast(((newsym, newtok, n), newargs), symmap))
            else:
                result.append(newtok)


    return _build(symmap[sym], result)

# ______________________________________________________________________

ty = "NAME '*'*"

grammar = """
decls    : (function | global)* ENDMARKER
function : 'function' header block* footer NEWLINE
header   : type NAME '(' arg *  ')' '{'

arg      : type varname
id       : ( NAME | NUMBER )
varname  : '%' id
type     : NAME '*'*
oparg    : varname | constant
constant : 'const' '(' type NUMBER ')'


block    : NAME ':' op+
op       : '%' id '=' '(' type ')' NAME '(' varname * ')'
global   : 'global' varname '=' type NEWLINE

footer   : '}'
"""

def make_parser(grammar):
    grammar_st0 = pgen2.parser.parse_string(grammar)
    return pgen2.pgen.buildParser(grammar_st0)

grammar_parser  = make_parser(grammar)
type_parser     = make_parser("p : type\ntype : {type} ENDMARKER\n".format(type=ty))

def parse(source, parser=grammar_parser):
    "Return a list of parsed statements (Function|Block|Stat)"
    result = parser.parseString(source)
    symmap = parser.symbolToStringMap()
    return result, symmap

# ______________________________________________________________________

def build(parse_result):
    """parse tree -> [Function]"""
    parsed, symmap = parse_result
    _, decls = parsed
    return [build_ast(decl, symmap) for decl in decls if decl[0][0] in symmap]

# ______________________________________________________________________

def from_assembly(source, parser=grammar_parser):
    """Parse pykit assembly and return a Module"""
    result = build(parse(source, parser))
    mod = Module()
    for value in result:
        if isinstance(value, GlobalValue):
            mod.add_global(value)
        else:
            mod.add_function(value)

    return mod