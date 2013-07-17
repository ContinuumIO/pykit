from .llvm_codegen import translate, run
from llvm_utils import module, target_machine, link_module, execution_engine
import llvm_utils

def init(func, env, opt=3):
    """Initialize environment"""
    opt = env.setdefault("codegen.llvm.opt", 3)
    machine = env.get("codegen.llvm.machine") or target_machine(opt)
    env["codegen.llvm.module"] = mod = module('test_module')
    env["codegen.llvm.engine"] = execution_engine(mod, machine)

def verify(func, env):
    llvm_utils.verify(func)
    llvm_utils.verify(env["codegen.llvm.module"])

def optimize(func, env):
    llvm_utils.optimize(env["codegen.llvm.module"],
                        env["codegen.llvm.machine"],
                        env["codegen.llvm.opt"])

def execute(func, env, *args):
    cfunc = llvm_utils.pointer_to_func(env["codegen.llvm.engine"], func)
    return cfunc(*args)