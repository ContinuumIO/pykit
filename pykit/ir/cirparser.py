# -*- coding: utf-8 -*-

"""
Parse pykit IR in the form of C.
"""

from __future__ import print_function, division, absolute_import

from io import StringIO
import os
import tempfile
import json
import tokenize
from itertools import islice
from collections import defaultdict, namedtuple

from pykit import types
from pykit.utils import match
from pykit.ir import defs, Module, Function, Builder, Block, Op, Const, GlobalValue

from pykit.deps.pycparser.pycparser import preprocess_file, c_ast, CParser

root = os.path.dirname(os.path.abspath(__file__))

#===------------------------------------------------------------------===
# Metadata and comment preprocessing
#===------------------------------------------------------------------===

Token = namedtuple('Token', ['toknum', 'tokval', 'beginpos', 'endpos'])

def parse_metadata(metadata):
    """Parse metadata (a JSON dict) as a string"""
    return json.loads(metadata)

def preprocess(source):
    """
    Preprocess source and return metadata. I wish CParser would accept a
    modified CLexer...

    Finds metadata between '/*:' and ':*/' lines

        c = (int) add(a, b); /*: { sideeffects: false } :*/
    """
    metadata = {} # { lineno : dict of metadata }
    tokens = []

    def eat(toknum, tokval, beginpos, endpos, rest):
        tokens.append(Token(toknum, tokval, beginpos, endpos))

    def error(tok, msg):
        raise SyntaxError("%d:%s: %s" % (tok.beginpos + (msg,)))

    tokenize.tokenize(StringIO(unicode(source)).readline, tokeneater=eat)
    tokval = lambda t: t.tokval

    lines = [""] + source.splitlines()
    i = 0
    while i < len(tokens):
        # Locate start of comment
        if "".join(map(tokval, tokens[i:i+3])) == "/*:":
            for j in xrange(i+3, len(tokens)):
                # Locate end of comment
                if "".join(map(tokval, tokens[j:j+3])) == ":*/":
                    lineno = tokens[j].beginpos[0]
                    if lineno != tokens[i].beginpos[0]:
                        raise error(tokens[i], "Metadata must be on a single line")

                    # Cut out string and parse
                    start, end = tokens[i+3].beginpos[1], tokens[j].beginpos[1]
                    metadata[lineno] = parse_metadata(lines[lineno][start:end])

                    i = j + 3
                    break
            else:
                raise error(tokens[i], "Metadata not terminated")

        i = i + 1

    return metadata

#===------------------------------------------------------------------===
# Parsing
#===------------------------------------------------------------------===

type_env = {
    "Type":      types.Type,
    "_list":     list,
    "int":       types.Int,
    "long":      types.Long,
    "long long": types.LongLong,
    "float":     types.Float32,
    "double":    types.Float64,
}

binary_defs = dict(defs.binary_defs, **defs.compare_defs)

def error(node, msg):
    raise SyntaxError("%s:%d: %s" % (node.coord.file, node.coord.line, msg))

class PykitIRVisitor(c_ast.NodeVisitor):
    """
    Map pykit IR in the form of polymorphic C to in-memory pykit IR.

        int function(float x) {
            int i = 0;        /* I am a comment */
            while (i < 10) {  /*: { "unroll": true } :*/
                x = call_external("sqrt", x * x);
            }
            return (int) x;
        }

    Attributes:
    """

    in_function = False

    def __init__(self, type_env=None):
        self.mod = Module()
        self.type_env = type_env or {}

        self.func = None
        self.builder = None
        self.local_vars = None
        self.allocas = None

        self.global_vars = {}
        self.functions = {}

    # ______________________________________________________________________

    @property
    def vars(self):
        if self.in_function:
            return self.local_vars
        else:
            return self.global_vars

    def enter_func(self):
        self.in_function = True
        self.local_vars = {}
        self.allocas = {}

    def leave_func(self):
        self.in_function = False
        self.mod.add_function(self.func)
        self.local_vars = None
        self.allocas = None
        self.func = None

    def visit(self, node, type=None):
        """
        Visit a node.

        :type: Whether we have a type for this opcode, which is an LHS type
               or a cast. E.g.:

              (Int) call(...)    // cast
              result = call(...) // assmnt, assuming 'result' is declared
              result = call(..., call(...)) // second 'call' isn't typed

        """
        self.type = type
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        # if visitor is None:
        #     raise SyntaxError(
        #         "Node %s not supported in %s:%s" % (node, node.coord.file,
        #                                             node.coord.line))
        return visitor(node)

    def visitif(self, node):
        if node:
            return self.visit(node)

    def visits(self, node):
        return list(map(self.visit, node))

    # ______________________________________________________________________

    def alloca(self, varname):
        if varname not in self.allocas:
            # Allocate variable with alloca
            with self.builder.at_front(self.func.blocks[0]):
                type = self.local_vars[varname]
                self.allocas[varname] = self.builder.alloca(type, [], varname)

        return self.allocas[varname]

    def assign(self, varname, rhs):
        if not self.in_function:
            error(rhs, "Assignment only allowed in functions")

        if varname not in self.allocas:
            # Allocate variable with alloca
            with self.builder.at_front(self.func.blocks[0]):
                type = self.local_vars[varname]
                self.allocas[varname] = self.builder.alloca(type, [], varname)

        self.builder.store(self.visit(rhs), self.alloca(varname))

    # ______________________________________________________________________

    def visit_Decl(self, decl):
        if decl.name in self.vars:
            error(decl, "Var '%s' already declared!" % (decl.name,))

        type = self.visit(decl.type)
        self.vars[decl.name] = type
        if decl.init:
            self.assign(decl.name, decl.init)

        return type

    def visit_TypeDecl(self, decl):
        return self.visit(decl.type)

    visit_Typename = visit_TypeDecl

    def visit_PtrDecl(self, decl):
        return types.Pointer(self.visit(decl.type.type))

    def visit_FuncDecl(self, decl):
        return types.Function(self.visit(decl.type),
                              self.visits(decl.args.params))

    def visit_IdentifierType(self, node):
        name, = node.names
        return self.type_env[name]

    def visit_Typedef(self, node):
        if node.name in ("Type", "_list"):
            type = self.type_env[node.name]
        else:
            type = self.visit(node.type)
            if type == types.Type:
                type = getattr(types, node.name)

            self.type_env[node.name] = type

        return type

    def visit_Template(self, node):
        left = self.visit(node.left)
        subtypes = self.visits(node.right)
        if left is list:
            return list(subtypes)
        else:
            assert issubclass(left, types.Type)
            subtypes = self.visits(node.right)
            return left(*subtypes)

    # ______________________________________________________________________

    def visit_FuncDef(self, node):
        assert not node.param_decls
        self.enter_func()

        name = node.decl.name
        type = self.visit(node.decl.type)
        argnames = [p.name for p in node.decl.type.args.params]
        self.func = Function(name, argnames, type)
        self.func.add_block('entry')
        self.builder = Builder(self.func)
        self.builder.position_at_end(self.func.blocks[0])
        self.generic_visit(node.body)

        self.leave_func()

    # ______________________________________________________________________

    def visit_FuncCall(self, node):
        name = node.name.name
        if not self.in_typed_context:
            error(node, "Expected a type for sub-expression "
                        "(add a cast or assignment)")
        if not hasattr(self.builder, name):
            error(node, "No opcode %s" % (name,))
        self.in_typed_context = False

        buildop = getattr(self.builder, name)
        args = self.visits(node.args.exprs)
        return buildop, args

    def visit_ID(self, node):
        if self.in_function:
            if node.name not in self.local_vars:
                error(node, "Not a local: %r" % node.name)

            result = self.alloca(node.name)
            return self.builder.load(result.type, result)

    def visit_Cast(self, node):
        type = self.visit(node.to_type)
        if isinstance(node.expr, c_ast.FuncCall):
            self.in_typed_context = True
            buildop, args = self.visit(node.expr)
            return buildop(type, args, "temp")
        else:
            result = self.visit(node.expr)
            if result.type == type:
                return result
            return self.builder.convert(type, [result], "temp")

    def visit_Assignment(self, node):
        if node.op != '=':
            error(node, "Only assignment with '=' is supported")
        if not isinstance(node.lvalue, c_ast.ID):
            error(node, "Canot only assign to a name")
        self.assign(node.lvalue.name, node.rvalue)

    def visit_Constant(self, node):
        type = self.type_env[node.type]
        const = types.convert(node.value, type)
        return Const(const)

    def visit_UnaryOp(self, node):
        op = defs.unary_defs[node.op]
        buildop = getattr(self.builder, op)
        arg = self.visit(node.expr)
        type = self.type or arg.type
        return buildop(type, [arg])

    def visit_BinaryOp(self, node):
        op = binary_defs[node.op]
        buildop = getattr(self.builder, op)
        left, right = self.visits([node.left, node.right])
        if not self.type:
            assert left.type == right.type, (left, right)
        return buildop(self.type or left.type, [left, right], "temp")

    def _loop(self, init, cond, next, body):
        _, exit_block = self.builder.splitblock("exit")
        _, body_block = self.builder.splitblock("body")
        _, cond_block = self.builder.splitblock("cond")

        self.visitif(init)
        self.builder.jump(cond_block)

        with self.builder.at_front(cond_block):
            cond = self.visit(cond, type=types.Bool)
            self.builder.cbranch(cond, cond_block, exit_block)

        with self.builder.at_front(body_block):
            self.visit(body)
            self.visitif(next)
            self.builder.jump(cond_block)

        self.builder.position_at_end(exit_block)

    def visit_While(self, node):
        self._loop(None, node.cond, None, node.stmt)

    def visit_For(self, node):
        self._loop(node.init, node.cond, node.next, node.stmt)

    def visit_Return(self, node):
        self.builder.ret(self.visit(node.expr))


def parse(source, filename):
    return CParser(lex_optimize=False, yacc_optimize=False, yacc_debug=True).parse(source, filename)

def from_c(source, filename="<string>"):
    metadata = preprocess(source)

    # Preprocess...
    f = tempfile.NamedTemporaryFile()
    try:
        f.write(source)
        f.flush()
        source = preprocess_file(f.name, cpp_args=['-I' + root])
    finally:
        f.close()

    # Parse
    ast = parse(source, filename)
    # ast.show()
    visitor = PykitIRVisitor(dict(type_env))
    visitor.visit(ast)
    return visitor.mod
