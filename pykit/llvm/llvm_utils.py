from io import BytesIO
from llvmpy.api import llvm

llvm_context = llvm.getGlobalContext()

def verify_module(module):
    action = llvm.VerifierFailureAction.ReturnStatusAction
    errio = BytesIO()
    broken = llvm.verifyModule(module, action, errio)
    if broken:
        raise Exception(errio.getvalue())

def verify_function(func):
    actions = llvm.VerifierFailureAction
    broken = llvm.verifyFunction(func,
                                     actions.ReturnStatusAction)
    if broken:
        # If broken, then re-run to print the message
        llvm.verifyFunction(func, actions.PrintMessageAction)
        raise Exception("Funciton verification failed for %s" % func.getName())


def get_or_insert_func(lmod, name, retty, args, vararg=False):
    "args --- can be values or types"
    if args and not isinstance(args[0], llvm.Type):
        argtys = [arg.getType() for arg in args]
    else:
        argtys = args
    fnty = llvm.FunctionType.get(retty, argtys, vararg)
    fn = lmod.getOrInsertFunction(name, fnty)
    return fn._downcast(llvm.Function)


def make_basic_block(lfunc, name=''):
    return llvm.BasicBlock.Create(llvm_context, name, lfunc, None)
