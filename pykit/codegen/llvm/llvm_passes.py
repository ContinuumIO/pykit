from llvmpy.api import llvm

def _initialize_passes():

    passreg = llvm.PassRegistry.getPassRegistry()

    llvm.initializeCore(passreg)
    llvm.initializeScalarOpts(passreg)
    llvm.initializeVectorization(passreg)
    llvm.initializeIPO(passreg)
    llvm.initializeAnalysis(passreg)
    llvm.initializeIPA(passreg)
    llvm.initializeTransformUtils(passreg)
    llvm.initializeInstCombine(passreg)
    llvm.initializeInstrumentation(passreg)
    llvm.initializeTarget(passreg)

    def _dump_all_passes():
        for name, desc in passreg.enumerate():
            yield name, desc
    return dict(_dump_all_passes())

PASSES = _initialize_passes()

def make_fpm_with_passes(lmod, passes):
    passreg = llvm.PassRegistry.getPassRegistry()
    fpm = llvm.FunctionPassManager.new(lmod)
    for name in passes:
        apass = passreg.getPassInfo(name).createPass()
        fpm.add(apass)
    return fpm

def run_function_passses(lfunc, passes):
    fpm = make_fpm_with_passes(lfunc.getParent(), passes)
    fpm.doInitialization()
    fpm.run(lfunc)
    fpm.doFinalization()


def make_pm(opt=2, inline=2000):
    pm = llvm.PassManager.new()
    pmb = llvm.PassManagerBuilder.new()
    pmb.OptLevel = opt
    pmb.Inliner = llvm.createFunctionInliningPass(inline)
    pmb.populateModulePassManager(pm)
    return pm

#from pprint import pprint
#pprint(PASSES)

