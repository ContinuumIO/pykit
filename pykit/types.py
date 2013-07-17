from collections import namedtuple
from pykit.utils import invert, hashable

alltypes = set()

class Type(object):
    """Base of types"""

    def __eq__(self, other):
        return isinstance(other, type(self)) and super(Type, self).__eq__(other)

    def __neq__(self, other):
        return isinstance(other, type(self)) and super(Type, self).__neq__(other)

    def __nonzero__(self):
        return True

    __bool__ = __nonzero__

def typetuple(name, elems):
    ty = type(name, (Type, namedtuple(name, elems)), {})
    alltypes.add(ty)
    return ty

VoidT      = typetuple('Void',     [])
Boolean    = typetuple('Boolean',  [])
Integral   = typetuple('Int',      ['bits', 'signed'])
Real       = typetuple('Real',     ['bits'])
Complex    = typetuple('Complex',  ['base'])
Array      = typetuple('Array',    ['base', 'ndim', 'order']) # order in 'C', 'F', 'A'
Struct     = typetuple('Struct',   ['names', 'types'])
Pointer    = typetuple('Pointer',  ['base'])
ObjectT    = typetuple('Object',   [])
BytesT     = typetuple('Bytes',    [])
UnicodeT   = typetuple('Unicode',  [])
CharT      = typetuple('CharT',    [])
UniCharT   = typetuple('UniCharT', [])
Tuple      = typetuple('Tuple',    ['bases'])
List       = typetuple('List',     ['base', 'count'])  # count == -1 if unknown
Dict       = typetuple('Dict',     ['key', 'value', 'count'])
SumType    = typetuple('SumType',  ['types'])
Partial    = typetuple('Partial',  ['fty'])
Function   = typetuple('Function', ['restype', 'argtypes'])
ExceptionT = typetuple('Exception',[])
Typedef    = typetuple('Typedef',  ['name', 'type'])
OpaqueT    = typetuple('Opaque',   []) # Some type we make zero assumptions about

for ty in alltypes:
    for ty2 in alltypes:
        setattr(ty, 'is_' + ty2.__name__.lower(), False)
    setattr(ty, 'is_' + ty.__name__.lower(), True)

# ______________________________________________________________________
# Types

Void    = VoidT()
Bool    = Boolean()
Int8    = Integral(8,  False)
Int16   = Integral(16, False)
Int32   = Integral(32, False)
Int64   = Integral(64, False)
UInt8   = Integral(8,  True)
UInt16  = Integral(16, True)
UInt32  = Integral(32, True)
UInt64  = Integral(64, True)

Float32  = Real(32)
Float64  = Real(64)
# Float128 = Real(128)

Complex64  = Complex(Float32)
Complex128 = Complex(Float64)
# Complex256 = Complex(Float128)

Object    = ObjectT()
Bytes     = BytesT()
Unicode   = UnicodeT()
Exception = ExceptionT()
Opaque    = OpaqueT()

# Typedefs
Int      = Typedef("Int", Int32)
Long     = Typedef("Long", Int32)
LongLong = Typedef("LongLong", Int32)

# ______________________________________________________________________

signed_set   = frozenset([Int8, Int16, Int32, Int64])
unsigned_set = frozenset([UInt8, UInt16, UInt32, UInt64])
int_set      = signed_set | unsigned_set
float_set    = frozenset([Float32, Float64])
complex_set  = frozenset([Complex64, Complex128])
bool_set     = frozenset([Bool])
numeric_set  = int_set | float_set | complex_set
scalar_set   = numeric_set | bool_set

# ______________________________________________________________________
# Internal

VirtualTable  = typetuple('VirtualTable',  ['obj_type'])
VirtualMethod = typetuple('VirtualMethod', ['obj_type'])

# ______________________________________________________________________
# Parsing

def parse_type(s):
    from pykit.parsing import parser
    return parser.build(parser.parse(s, parser.type_parser))

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
    """Python value -> type"""
    return typing_defaults[type(value)]

# ______________________________________________________________________
# Convert

conversion_map = invert(typing_defaults)
conversion_map.update(dict.fromkeys(int_set, int))
conversion_map.update(dict.fromkeys(float_set, float))
conversion_map.update(dict.fromkeys(complex_set, complex))

def convert(value, dst_type):
    """(python value, type) -> converted python value"""
    converter = conversion_map[dst_type]
    return converter(value)

# ______________________________________________________________________

type2name = dict((v, n) for n, v in globals().items() if hashable(v))
typename = type2name.__getitem__

def resolve_typedef(type):
    while type.is_typedef:
        type = type.type
    return type