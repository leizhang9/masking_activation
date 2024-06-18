#!/usr/bin/env python3
import numpy as np
import h5py
import argparse
import scipy.signal


def copy_attributes(handle, handle_out):
    for name, value in handle.attrs.items():
        handle_out.attrs[name] = value


def copy_dataset(handle, handle_out, dset_name, trace_select, dtype=None):
    if dtype is None:
        handle_out.create_dataset(dset_name, shape=(len(trace_select), handle.shape[1], handle.shape[2]), dtype=handle.dtype)
        handle_out[dset_name][:] = handle[trace_select, :, :]
    else:
        handle_out.create_dataset(dset_name, shape=(len(trace_select), handle.shape[1], handle.shape[2]), dtype=dtype)


def create_filecopy(handle, handle_out, trace_select):
    for keys in handle.keys():
        # create group
        handle_out.create_group(keys)
        # copy attributes of group
        copy_attributes(handle[keys], handle_out[keys])
        # loop over datasets
        for dsets in handle[keys].keys():

            if dsets == "samples":
                # create dataset of float type
                copy_dataset(handle[keys][dsets], handle_out[keys], dset_name=dsets, trace_select=trace_select, dtype=np.float)
            else:
                # copy data set and attributes
                copy_dataset(handle[keys][dsets], handle_out[keys], dset_name=dsets, trace_select=trace_select)
            # copy attributes
            copy_attributes(handle[keys][dsets], handle_out[keys][dsets])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for bandpass filtering a file.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="Input file name with t-test results. (*.hdf5).", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="Output file (default: add '_filtered_<f_min>_<f_max>' to file name)", type=str, default=None)
    parser.add_argument("-f", "--freqrange", dest="freqrange", help="Frequency range for filterung [Hz] <f_min f_max>.", type=float, required=True, nargs=2)
    parser.add_argument("--order", dest="order", help="Order of the filtering (default: 2).", type=int, required=False, default=2)
    parser.add_argument("-p", "--position", dest="group", help="Measurement position for evaluation", default="0000", type=str)
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of the dataset for evaluation. Default: 'samples'", default="samples", type=str)
    parser.add_argument("--traces", dest="traces", help="Select traces, [min, max, step]. Default: all", metavar=int, type=int, default=[None, None, 1], nargs=3)

    args = parser.parse_args()

    # specify file that contains the raw data
    h5filehandle = h5py.File(args.inputfile, "r")
    # create data set handle
    samples_dset = h5filehandle["/" + args.group + "/" + args.dataset]

    # convert trace selection into array and sanitize
    if args.traces[0] is None:
        # Default: from first trace on
        args.traces[0] = 0
    if args.traces[1] is None or args.traces[1] > samples_dset.shape[0]:
        # Default (or if more traces than available are selected): till the last trace
        args.traces[1] = samples_dset.shape[0]
    elif args.traces[2] > args.traces[1] - args.traces[0]:
        # if steps are bigger than selected trace range, just take a single trace.
        args.traces[2] = args.traces[1] - args.traces[0]
    # create array with trace indices
    traces_selected = np.arange(args.traces[0], args.traces[1], args.traces[2])

    ### Filter Design (c.f AISEC attacktool bandpassfilter)  # noqa: E266

    # retrieve sampling rate
    sample_rate = samples_dset.attrs["sampling rate [S/s]"]
    # Nyquist frequency
    nyq = 0.5 * sample_rate
    # lower freq
    lowf = args.freqrange[0] / nyq
    # higher freq
    highf = args.freqrange[1] / nyq
    #  numerator_coefficient_vector and denominator_coefficient_vector
    ncv, dcv = scipy.signal.butter(args.order, [lowf, highf], btype="band")

    ### Create copy of the file  # noqa: E266

    # same file name but adding frequency ranges
    if args.outputfile is None:
        args.outputfile = ".".join(args.inputfile.split(".")[:-1]) + "_filtered_%.2fMHz_%.2fMHz.hdf5" % (args.freqrange[0] * 1e-6, args.freqrange[1] * 1e-6)

    # open copy
    h5filehandle_out = h5py.File(args.outputfile, "w")
    h5filehandle_out.attrs["Original file before filtering"] = args.inputfile
    create_filecopy(handle=h5filehandle, handle_out=h5filehandle_out, trace_select=traces_selected)
    # dataset handle
    samples_dset_out = h5filehandle_out["/" + args.group + "/" + args.dataset]

    # add attributes for filterung
    samples_dset_out.attrs["Filtering"] = "order %i butterworth bandpass" % args.order
    samples_dset_out.attrs["Lower frequency [Hz]"] = args.freqrange[0]
    samples_dset_out.attrs["Upper frequency [Hz]"] = args.freqrange[1]
    samples_dset_out.attrs["Selected Traces"] = args.traces

    ### Actual filtering  # noqa: E266

    # get dataset
    trace = np.array(samples_dset[traces_selected, :, :])

    # filter each trace
    # TODO: could be improved by filtering batches of traces (the current method makes sure not to run into RAM problems)
    for idx in range(0, trace.shape[0]):
        print("Trace %i / %i" % (idx, trace.shape[0]))
        samples_dset_out[idx, :, :] = scipy.signal.lfilter(ncv, dcv, trace[idx, :, :], axis=0)

    # close HDF5 files
    h5filehandle.close()
    h5filehandle_out.close()
