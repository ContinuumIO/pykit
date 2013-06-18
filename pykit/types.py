from collections import namedtuple, defaultdict, deque, Set, Mapping
from pykit.ir import parser

alltypes = set()

def typetuple(name, elems):
    ty = namedtuple(name, elems)
    alltypes.add(ty)
    return ty

Boolean    = typetuple('Boolean',  [])
Int        = typetuple('Int',      ['bits', 'signed'])
Real       = typetuple('Real',     ['bits'])
Complex    = typetuple('Complex',  ['base'])
Array      = typetuple('Array',    ['base', 'ndim', 'order']) # order in 'C', 'F', 'A'
Struct     = typetuple('Struct',   ['types'])
Pointer    = typetuple('Pointer',  ['base'])
ObjectT    = typetuple('Object',   [])
BytesT     = typetuple('Bytes',    [])
UnicodeT   = typetuple('Unicode',  [])
Tuple      = typetuple('Tuple',    ['base', 'count']) # count == -1 if unknown
List       = typetuple('List',     ['base', 'count'])
Dict       = typetuple('Dict',     ['key', 'value', 'count'])
SumType    = typetuple('SumType',  ['types'])
Partial    = typetuple('Partial',  ['fty', 'bound']) # bound = { 'myparam' }
Function   = typetuple('Function', ['res', 'argtypes', 'argnames'])
Typedef    = typetuple('Typedef',  ['type', 'name'])

for ty in alltypes:
    for ty2 in alltypes:
        setattr(ty, 'is_' + ty.__name__.lower(), False)
    setattr(ty, 'is_' + ty.__name__.lower(), True)

# ______________________________________________________________________
# Types

Bool    = Boolean()
Int8    = Int(8, False)
Int16   = Int(8, False)
Int32   = Int(8, False)
Int64   = Int(8, False)
UInt8   = Int(8, True)
UInt16  = Int(8, True)
UInt32  = Int(8, True)
UInt64  = Int(8, True)

Float32  = Real(32)
Float64  = Real(64)
Float128 = Real(128)

Complex64  = Complex(Float32)
Complex128 = Complex(Float64)
Complex256 = Complex(Float128)

Object  = ObjectT()
Bytes   = BytesT()
Unicode = UnicodeT()

# ______________________________________________________________________

signed_set   = frozenset([Int8, Int16, Int32, Int64])
unsigned_set = frozenset([UInt8, UInt16, UInt32, UInt64])
int_set      = signed_set | unsigned_set
float_set    = frozenset([Float32, Float64, Float128])
complex_set  = frozenset([Complex64, Complex128, Complex256])
bool_set     = frozenset([Bool])
numeric_set  = int_set | float_set | complex_set
scalar_set   = numeric_set | bool_set

# ______________________________________________________________________
# Internal

VirtualTable  = typetuple('VirtualTable',  ['obj_type'])
VirtualMethod = typetuple('VirtualMethod', ['obj_type'])

# ______________________________________________________________________
# Parsing

def _from_ast(ty):
    """Convert a pykit.ir.parser Type AST to a Type"""
    if isinstance(ty, parser.Struct):
        return Struct(*map(_from_ast, ty.types))
    elif isinstance(ty, parser.Pointer):
        return Pointer(_from_ast(ty.base))
    else:
        return globals()[ty.name]

def parse_type(s):
    ty_ast, = parser.from_assembly(s, parser.type_parser)
    return _from_ast(ty_ast)

# ______________________________________________________________________
# Typeof

typing_defaults = {
    bool:       Bool,
    int:        Int32,
    float:      Float64,
    complex:    Complex128,
    str:        Bytes,
    unicode:    Unicode,
    tuple:      Tuple,
    list:       List,
    dict:       Dict,
}

def typeof(value):
    return typing_defaults[type(value)]