#!/usr/bin/env python3
import numpy as np
import h5py
import argparse
from attack.helper.utils import HDF5utils as HDF5_utils
import logging

_logger = logging.getLogger(__name__)


def cummulative_moving_average(x, cma, n):
    """
    Cummulative moving average (CMA), c.f. https://en.wikipedia.org/wiki/Moving_average
    :param x: current data
    :param cma: current CMA
    :param n: number of included data points
    :return: updated CMA
    """

    cma = cma + (x - cma) / n
    return cma


def main():  # noqa: C901
    parser = argparse.ArgumentParser(description="Script for averaging several traces with a certain fixed input file. A moving average is calculated.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="Input file name with t-test results. (*.hdf5).", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="Output file (default: add '_averaged_N<number of traces>' to file name)", type=str, default=None)
    parser.add_argument("-p", "--position", dest="group", help="Measurement position for evaluation", default="0000", type=str)
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of the dataset for evaluation. Default: 'samples'", default="samples", type=str)
    parser.add_argument("--traces", dest="traces", help="Number of traces for averaging. Default: all", metavar=int, type=int, default=None)
    parser.add_argument("--reference_dataset", dest="reference_dataset", type=str, help="Reference dataset according to which the traces are selected", default=None)
    parser.add_argument("--reference_value", dest="reference_value", nargs="*", help="Reference value from which the traces are selected.", type=int, default=None)
    parser.add_argument("--average-repetitions-only", dest="reps_only", action="store_true", help="Only average across repetitions, independent of data.")
    parser.add_argument("--repetitions", dest="num_repetitions", help="Number of repetitions for averaging. Default: all", metavar=int, type=int, default=None)
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")

    args = parser.parse_args()

    # configure logger
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(format="[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s", level=loglevel)

    # specify file that contains the raw data
    h5filehandle = h5py.File(args.inputfile, "r")

    # create data set handle
    samples_dset = h5filehandle["/" + args.group + "/" + args.dataset]
    if args.reference_dataset is not None:
        reference_dset = h5filehandle["/" + args.group + "/" + args.reference_dataset]
    else:
        reference_dset = h5filehandle["/" + args.group + "/" + args.dataset]

    # loop over all traces that have the correct value (e.g. key, input, etc.) and perform moving average
    if args.reps_only:
        N_traces = 0
        if args.traces is None:
            num_traces = samples_dset.shape[0]
        else:
            num_traces = args.traces

        cma = np.zeros((num_traces, samples_dset.shape[1]))
        trace_select = np.arange(0, num_traces)
        for repetition_idx in range(0, samples_dset.shape[2]):
            N_traces = N_traces + 1
            _logger.info("Repetition %i" % (N_traces))
            cma = cummulative_moving_average(np.array(samples_dset[0:num_traces, :, repetition_idx]), cma, N_traces)
            if args.num_repetitions is not None:
                # stop after desired number of traces
                if N_traces == args.num_repetitions:
                    break
    else:
        N_traces = 0
        first_reference_idx = None
        cma = np.zeros(samples_dset.shape[1])
        for trace_idx in range(0, reference_dset.shape[0]):
            # check whether reference dataset has the correct reference value for the trace (if no reference is given, average over all traces)
            if np.all(np.array(reference_dset[trace_idx, :, 0]) == args.reference_value) or args.reference_value is None:
                N_traces = N_traces + 1

                _logger.info("Averaging trace %i" % (N_traces))
                cma = cummulative_moving_average(np.array(samples_dset[trace_idx, :, 0]), cma, N_traces)

                if first_reference_idx is None:
                    # store the index of the first matching trace
                    first_reference_idx = trace_idx

            # if desired number of traces is reached, abort
            if args.traces is not None:
                # stop after desired number of traces
                if N_traces == args.traces:
                    break

    # same file name but adding number of traces
    if args.outputfile is None:
        args.outputfile = ".".join(args.inputfile.split(".")[:-1]) + "_averaged_N%i.hdf5" % (N_traces)

    # open copy
    h5filehandle_out = h5py.File(args.outputfile, "w")
    h5filehandle_out.attrs["Original file before averaging"] = args.inputfile
    if args.reps_only:
        # copy the file, generating a float dataset
        HDF5_utils.create_filecopy(handle=h5filehandle, handle_out=h5filehandle_out, trace_select=trace_select, repetition_select=np.arange(0, 1), conversion=[["samples", np.float]])
    else:
        # copy the file, generating a float dataset
        HDF5_utils.create_filecopy(handle=h5filehandle, handle_out=h5filehandle_out, trace_select=[first_reference_idx], conversion=[["samples", np.float]])
    # dataset handle
    samples_dset_out = h5filehandle_out["/" + args.group + "/" + args.dataset]

    # add attributes with the number of traces used for averaging
    samples_dset_out.attrs["Number of averaged traces"] = N_traces

    # write cummulative average
    samples_dset_out[:, :, 0] = cma

    # close HDF5 files
    h5filehandle.close()
    h5filehandle_out.close()


# run program
if __name__ == "__main__":
    main()
