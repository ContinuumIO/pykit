from pykit.utils import make_temper
from . import llvm_postpasses
from .llvm_codegen import translate, run
from llvm_utils import module, target_machine, link_module, execution_engine
import llvm_utils

name = "llvm"

def install(env, opt=3, llvm_engine=None, llvm_module=None,
            llvm_target_machine=None, temper=make_temper()):
    """Install llvm code generator in environment"""
    llvm_target_machine = llvm_target_machine or target_machine(opt)
    llvm_module = llvm_module or module(temper("temp_module"))
    llvm_engine = llvm_engine or execution_engine(llvm_module,
                                                  llvm_target_machine)
    env["pipeline.codegen"].append("passes.llvm.postpasses")
    env["passes.codegen"] = run
    env["passes.llvm.postpasses"] = llvm_postpasses
    env["codegen.llvm.opt"] = opt
    env["codegen.llvm.engine"] = llvm_engine
    env["codegen.llvm.module"] = llvm_module
    env["codegen.llvm.machine"] = llvm_target_machine

def verify(func, env):
    """Verify LLVM function and module"""
    llvm_utils.verify(func)
    llvm_utils.verify(env["codegen.llvm.module"])

def optimize(func, env):
    """Optimize llvm module"""
    llvm_utils.optimize(env["codegen.llvm.module"],
                        env["codegen.llvm.machine"],
                        env["codegen.llvm.opt"])

def execute(func, env, *args):
    """Execute llvm function with the given arguments"""
    cfunc = llvm_utils.pointer_to_func(env["codegen.llvm.engine"], func)
    assert len(func.args) == len(args)
    return cfunc(*args)