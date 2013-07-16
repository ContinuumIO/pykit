"""
Load addresses from shared objects. Works only for runtime compilation.
"""

import ctypes

def resolve_symbols(module, ctypes_lib, names=None):
    """Resolve external symbols from a Module with runtime function addresses"""
    if not names:
        names = [name for name, sym in module.globals.iteritems()
                          if sym.external]
    for name in names:
        sym = module.get_global(name)
        assert sym.external
        cfunc = getattr(ctypes_lib, name)
        sym.address = ctypes.cast(cfunc, ctypes.c_void_p).value