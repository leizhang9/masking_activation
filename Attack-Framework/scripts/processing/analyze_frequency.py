#!/usr/bin/env python3
import numpy as np
import h5py
import logging
import argparse
from attack.helper.utils import FrequencyUtils as freq_utils
from attack.helper.utils import HDF5utils as h5utils
from attack.helper.utils import MISCutils as misc_utils
import sys
import os

_logger = logging.getLogger(__name__)


def main():  # noqa: C901
    # Argument parse
    parser = argparse.ArgumentParser(description="Convert SCA measurements to frequency domain.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="HDF5 file with time domain measurements.", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="HDF5 file with frequency domain results.", type=str, required=False)
    parser.add_argument("-p", "--position", dest="group", help="Measurement position(s) for evaluation. Default: all", default=None, type=str, nargs="*")
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of the dataset for evaluation. Default: 'samples'", default=["samples"], type=str, nargs="*")
    parser.add_argument("--repetitions", dest="repetitions", help="Number of different repetitions. Default: all", default=None, type=int)
    parser.add_argument("--traces", dest="traces", help="Select traces, [min, max, step]. Default: all", metavar=("min", "max", "step"), type=int, default=[None, None, 1], nargs=3)
    parser.add_argument("--time", dest="time", help="Select time (s) relative to trigger. Default: all", metavar=("start", "stop"), type=float, default=[0, None], nargs=2, required=False)
    parser.add_argument("--frequency-range", dest="freq_range", help="Select the frequency range that is stored.", metavar=("f_min", "f_max"), type=float, default=[0, None], nargs=2, required=False)
    parser.add_argument("-w", "--window", dest="window", help="Windowing method for FFT. Default: 'Hanning'", default="Hanning", type=str)
    parser.add_argument("--smooth-spec", dest="smooth_spec", help="Low pass filter in frequency.", action="store_true")
    parser.add_argument("--average-over-all", dest="av_over_all", help="Average over all traces and repetitions (e.g. for background noise). Overwrites '--average-over-repetitions'.", action="store_true")
    parser.add_argument("--average-over-repetitions", dest="av_over_reps", help="Average over all repetitions (e.g. for SNR enhancement).", action="store_true")
    parser.add_argument("--single-mode", dest="single_mode", action="store_true", help="Convert each trace and repetition separately to save RAM (for big datasets and/or constrained resources)")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")
    parser.add_argument("--fs", dest="fs", help="Sampling frequency [S/s] (if not provided by HDF5).", default=None, type=float)

    args = parser.parse_args()

    # configure logger
    misc_utils.configure_logger(verbose=args.verbose)

    # prefix: file name excluding file extension (.h5/.hdf5)
    filename_prefix = os.path.splitext(os.path.realpath(args.inputfile))[0]

    # Load file
    h5filename_in = h5py.File(args.inputfile, "r")

    # default: convert all positions
    if args.group is None:
        args.group = h5utils.hdf5_get_positions(h5filehandle=h5filename_in)

    # 1. Read data from time domain from the first dataset and make a dummy execution to get the dimension of the
    # resulting data set. Implicit assumption: all datasets have the same dimensions.
    try:
        _logger.info("Try to load samples.")
        # get samples data set
        samples_dset = h5filename_in["/%s/%s" % (args.group[0], args.dataset[0])]

        # read the sampling frequency from the HDF5 (should be default) if no command line option is given (only required for special cases such as TDC)
        if args.fs is not None:
            fs = args.fs
        else:
            # get sampling frequency
            fs = samples_dset.attrs["sampling rate [S/s]"]

        # Trigger delay defaults to zero if not provided by HDF5
        try:
            x_offset = samples_dset.attrs["trigger: delay [s]"]
        except KeyError:
            x_offset = 0

        # convert trace selection into array
        if args.traces[0] is None:
            # default: start with first trace
            args.traces[0] = 0
        if args.traces[1] is None or args.traces[1] > samples_dset.shape[0]:
            # default: stop at last trace (convert all traces) and make sure to limit to maximum available traces
            args.traces[1] = samples_dset.shape[0]
        if args.traces[2] > samples_dset.shape[0]:
            # limit step size to maximum number of traces
            args.traces[2] = samples_dset.shape[0]

        traces_selected = np.arange(args.traces[0], args.traces[1], args.traces[2])

        if args.repetitions is None:
            args.repetitions = samples_dset.shape[2]

        # select time
        if args.time[0] is None:
            # Default: Start at trigger
            samples_start = int(-x_offset * fs)
        else:
            samples_start = int(args.time[0] * fs)
        if args.time[1] is None:
            # Default: last sample
            samples_stop = samples_dset.shape[1]
        else:
            samples_stop = int(args.time[1] * fs)

        # sanitation
        samples_start = max(samples_start, 0)
        samples_stop = min(samples_stop, samples_dset.shape[1])

        args.time[0] = samples_start / fs
        args.time[1] = samples_stop / fs

        # select frequencies
        if args.freq_range[1] is None:
            # default: entire frequency range (maximum according to Nyquist theorem)
            args.freq_range[1] = fs / 2

        _logger.info("Traces %i to %i in steps of %i selected." % (args.traces[0], args.traces[1], args.traces[2]))
        _logger.info("Samples %i to %i selected." % (samples_start, samples_stop))
        _logger.info("%i repetitions selected." % args.repetitions)

        if args.smooth_spec:
            _logger.info("Smoothing in frequency direction activated.")
            smooth_string = "smoothed_"
        else:
            smooth_string = ""
    except KeyError as e:
        _logger.error("Problem using input HDF5.")
        _logger.error(e)
        sys.exit(1)

    if args.av_over_all:
        noise_string = "noise_"
        # overwrites option for averaging over repetitions
        args.av_over_reps = False
    elif args.av_over_reps:
        noise_string = "averaged_"
    else:
        noise_string = ""

    # output filename
    if args.outputfile is None:
        o_file = (
            filename_prefix + "_frequency_domain_" + noise_string + smooth_string + "%.2f-%.2fMHz_%irepetitions_traces_%i-%i-%i_%.3fms.hdf5" % (args.freq_range[0] * 1e-6, args.freq_range[1] * 1e-6, args.repetitions, args.traces[0], args.traces[1], args.traces[2], (args.time[1] - args.time[0]) * 1e3)
        )
    else:
        o_file = args.outputfile

    # Abort if file exists
    if os.path.isfile(o_file):
        _logger.warning("File " + o_file + " already exists, aborting...")
        sys.exit(0)
    else:
        _logger.info("Creating spectral data...")
        # create file for storage
        h5filename_out = h5py.File(o_file, "w")
        # copy metadata from original file
        h5utils.copy_attributes(h5filename_in, h5filename_out)
        # copy the documentation
        try:
            doc_grp = h5filename_in["__documentation__"]
            doc_grp.copy(doc_grp, h5filename_out)
        except KeyError:
            _logger.warning("Source file did not have a '__documentation__' group.")

        # add some additional description
        h5filename_out.attrs["description"] = "Based on the measurement file %s" % args.inputfile
        h5filename_out.attrs["Frequency: start time (relative to trigger)"] = args.time[0]
        h5filename_out.attrs["Frequency: stop time (relative to trigger)"] = args.time[1]
        h5filename_out.attrs["Frequency: repetitions"] = args.repetitions
        h5filename_out.attrs["Frequency: trace start"] = args.traces[0]
        h5filename_out.attrs["Frequency: trace stop"] = args.traces[1]
        h5filename_out.attrs["Frequency: trace step"] = args.traces[2]

    _logger.info("Calculating dummy FFT...")
    # Calculate FFT for first data set to get shape of the resulting spectrum
    samples = np.array(samples_dset[args.traces[0], samples_start:samples_stop, [0]])
    _, freqs, NFFT = freq_utils.single_sided_fft(x=samples, fs=fs, NFFT=None, conv_dec=True, windowing=args.window, FFT_dim=0)
    _logger.info("Finished dummy FFT.")

    # get corresponding indices of the frequency bins
    freq_min_bin, freq_max_bin = freq_utils.get_frequency_bins(freqs=freqs, freq_min=args.freq_range[0], freq_max=args.freq_range[1])

    freqs = freqs[freq_min_bin : freq_max_bin + 1]
    num_freq_bins = freq_max_bin - freq_min_bin + 1

    # save frequencies
    freqs_handle = h5filename_out.create_dataset("frequencies", data=freqs, shape=freqs.shape)
    freqs_handle.attrs["Minimum frequency [Hz]"] = freqs[0]
    freqs_handle.attrs["Maximum frequency [Hz]"] = freqs[-1]
    freqs_handle.attrs["Frequency resolution [Hz]"] = freqs[-1] - freqs[-2]

    for position in args.group:
        _logger.info("Processing postition %s..." % position)
        group_handle = h5filename_out.create_group(position)
        group_handle_in = h5filename_in[position]
        h5utils.copy_attributes(group_handle_in, group_handle)

        # copy the datasets that are not transformed in to frequency domain
        for dsets in group_handle_in.keys():
            if dsets not in args.dataset:
                h5utils.copy_dataset(handle=group_handle_in[dsets], handle_out=group_handle, dset_name=dsets, trace_select=traces_selected, repetititon_select=None)

        # convert the specified datasets to the frequency domain
        for dataset in args.dataset:
            _logger.info("Processing dataset %s..." % dataset)
            # get handle
            dset_handle_in = h5filename_in["/" + position + "/" + dataset]
            # 2. Generate data in frequency domain and write to file

            # create data set for the spectrum
            if args.av_over_all:
                dset_handle_spec = group_handle.create_dataset(dataset + "_spectrum", shape=(1, num_freq_bins), dtype=float)
                spec_tmp = np.zeros((len(traces_selected), num_freq_bins))
            elif args.av_over_reps:
                dset_handle_spec = group_handle.create_dataset(dataset + "_spectrum", shape=(len(traces_selected), num_freq_bins, 1), dtype=float)
            else:
                dset_handle_spec = group_handle.create_dataset(dataset + "_spectrum", shape=(len(traces_selected), num_freq_bins, args.repetitions), dtype=float)

            # copy attributes and add from FFT
            h5utils.copy_attributes(dset_handle_in, dset_handle_spec)
            dset_handle_spec.attrs["NFFT"] = NFFT
            dset_handle_spec.attrs["Windowing"] = args.window

            if args.smooth_spec:
                dset_handle_spec.attrs["Smoothing"] = "2nd order Butterworth (cut 12000)"
            else:
                dset_handle_spec.attrs["Smoothing"] = False

            # iterate over selected traces (for memory reasons)
            for tdx, trace_id in enumerate(traces_selected):
                _logger.info("Calculating FFT of trace %i / %i" % (trace_id + 1, len(traces_selected)))
                # get data
                samples = np.array(dset_handle_in[trace_id, samples_start:samples_stop, 0 : args.repetitions])

                _logger.debug("Calculating FFT...")
                if args.single_mode:
                    # preallocate
                    Y = np.zeros((num_freq_bins, args.repetitions), dtype=float)
                    for rep_id in range(0, args.repetitions):
                        _logger.debug("Calculating FFT of repetition %i / %i" % (rep_id + 1, args.repetitions))
                        Y_tmp, freqs, NFFT = freq_utils.single_sided_fft(x=samples[:, [rep_id]], fs=fs, NFFT=None, conv_dec=True, windowing=args.window, FFT_dim=0)

                        if args.smooth_spec:
                            _logger.debug("Smoothing in frequency direction.")
                            Y_tmp = freq_utils.fft_smooth(data=Y_tmp, order=2, filterdim=0)

                        # limit to selected frequency range
                        Y[:, [rep_id]] = Y_tmp[freq_min_bin : freq_max_bin + 1, :]
                else:
                    Y, freqs, NFFT = freq_utils.single_sided_fft(x=samples, fs=fs, NFFT=None, conv_dec=True, windowing=args.window, FFT_dim=0)
                    if args.smooth_spec:
                        _logger.debug("Smoothing in frequency direction.")
                        Y = freq_utils.fft_smooth(data=Y, order=2, filterdim=0)

                    # limit to selected frequency range
                    Y = Y[freq_min_bin : freq_max_bin + 1, :]

                _logger.debug("Finished FFT.")
                if args.av_over_all or args.av_over_reps:
                    _logger.debug("Averaging spectrum...")
                    # average over repetitions
                    Y = np.mean(Y, axis=1)
                    Y = np.atleast_2d(Y)

                if args.av_over_all:
                    spec_tmp[tdx, :] = Y
                elif args.av_over_reps:
                    dset_handle_spec[tdx, ...] = Y.transpose()
                else:
                    dset_handle_spec[tdx, ...] = Y

            if args.av_over_all:
                dset_handle_spec[:] = np.mean(spec_tmp, axis=0)

    h5filename_out.close()
    h5filename_in.close()

    _logger.info("Done")


# run program
if __name__ == "__main__":
    main()
