import sys
from line_profiler import LineProfiler

from contur.run.arg_utils import get_args
from contur.run.run_analysis import main
from contur.factories.test_observable import Observable

lp = LineProfiler()

lp.add_function(Observable.__init__)
lp.add_function(Observable._Observable__getExpected)
lp.add_function(Observable._Observable__getData)
lp.add_function(Observable._Observable__getThy)
lp.add_function(Observable._Observable__getAux)
lp.add_function(Observable.add_signal_component)
lp.add_function(Observable.build_likelihood)

args = get_args(sys.argv[1:], "analysis")

try:
    lp_wrapper = lp(main)
    lp_wrapper(args)
finally:
    lp.print_stats()
