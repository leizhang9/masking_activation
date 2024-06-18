#!/usr/bin/env python3
import numpy as np
import h5py
import argparse
from matplotlib import pyplot as plt
import attack.helper.plot_utils as plot_utils
from attack.helper.utils import HDF5utils as h5utils
from attack.helper.utils import MISCutils as misc_utils
from attack.helper.utils import FrequencyUtils as freq_utils
import logging
import sys

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Script for plotting frequencies from the TUEISEC attack framework.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", type=str, required=True, help="Input file name with measurements. (*.hdf5).")
    parser.add_argument("-n", "--noisefile", dest="noisefile", metavar="filename", type=str, default=None, help="File name with noise floor. (*.hdf5).")
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", type=str, default=None, help="Output file name for the plot. (*.pdf). Default: INPUTFILENAME.pdf")
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset for evaluation. Default: 'samples_spectrum'", default="samples_spectrum", type=str)
    parser.add_argument("--traces", dest="traces", help="Number of traces for plotting. Default: first", type=int, default=[0], nargs="*")
    parser.add_argument("--repetitions", dest="repetitions", help="Number of repetitions for plotting. Default: first", type=int, default=[0], nargs="*")
    parser.add_argument("--freq-min", dest="freq_min", help="Minimum frequency that is evaluated [Hz]. ", type=float, default=None)
    parser.add_argument("--freq-max", dest="freq_max", help="Maximum frequency that is evaluated [Hz]. ", type=float, default=None)
    parser.add_argument("--evaluation-function", type=str, default="amp_max", help="Evaluation that is applied, e.g. 'maximum'.")
    parser.add_argument("--frequency-scale", type=str, help="Time scale of the x-axis ('Hz','kHz','MHz','GHz')", default="MHz")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name for plot configuration(*.json).", type=str, default=None)
    parser.add_argument("--save-plot", dest="save_plot", action="store_true", help="Save the plot as pdf.")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")
    parser.add_argument("--vmin", type=float, default=None, help="Minimum value of colormap.")
    parser.add_argument("--vmax", type=float, default=None, help="Maximum value of colormap.")

    args = parser.parse_args()
    # configure logger
    misc_utils.configure_logger(verbose=args.verbose)

    # import plt.rcParam configuration
    plot_utils.load_plotconfig(args.configfile, save=args.save_plot)
    # specify file
    h5filehandle = h5py.File(args.inputfile, "r")
    # get noise file
    if args.noisefile is not None:
        noisefilehandle = h5py.File(args.noisefile, "r")
        save_string = "_frequency_denoised"
    else:
        noisefilehandle = None
        save_string = "_frequency"

    # get all positions
    positions = h5utils.hdf5_get_positions(h5filehandle)
    # generate frequency vector
    freqs, freq_scale, freq_label, bin_min, bin_max = plot_utils.generate_frequency_vector(h5filehandle=h5filehandle, freqscale=args.frequency_scale, freq_min=args.freq_min, freq_max=args.freq_max)
    # string with parameters that is appended in case no file name is given
    save_string = save_string + "_%.0f-%.0f_%s_%s" % (freqs[0], freqs[-1], freq_label, args.evaluation_function)

    num_observations = max(len(args.repetitions), len(args.traces))
    samples_eval = np.ones((len(positions), num_observations)) * -1

    for gdx, group in enumerate(positions):
        position_handle = h5filehandle["/" + group]
        # get samples handle
        sample_handle = position_handle[args.dataset]
        # get array with selected traces
        samples, traces, repetitions = h5utils.hdf5_apply_selection(sample_handle=sample_handle, traces=args.traces, repetitions=args.repetitions, sample_min=bin_min, sample_max=bin_max)
        if noisefilehandle is not None:
            noise = freq_utils.get_noisefloor_frequency_domain(noisefilehandle=noisefilehandle, group=group, dataset=args.dataset, freq_min=freqs[0] / freq_scale, freq_max=freqs[-1] / freq_scale, traces=traces, repetitions=repetitions)
            # subtract noise floor
            samples = samples - noise
            colorbar_addition = "denoise"
        else:
            colorbar_addition = ""
        # apply processing
        if args.evaluation_function == "amp_max":
            # get the maximum amplitude value
            samples_eval[gdx, :] = np.max(samples, axis=0)
            colorbarlabel = "|$f_{%s}$| [dB]" % colorbar_addition
        elif args.evaluation_function == "freq_max":
            # get the frequency with the maximum PSD
            samples_eval[gdx, :] = freqs[np.argmax(samples, axis=0)]
            colorbarlabel = "$f$ [%s]" % args.frequency_scale
        else:
            _logger.error("Processing '%s' not supported yet." % args.evaluation_function)
            sys.exit(1)

    x, y = h5utils.hdf5_get_xy_values(h5filehandle, positions)

    samples_eval, N_x, N_y = plot_utils.invert_meander_multitrace(samples=samples_eval, x=x, y=y)

    for plt_idx in range(num_observations):
        plt.figure()
        # make sure, the origin is in the lower corner
        plt.imshow(samples_eval[:, :, plt_idx], origin="lower", vmin=args.vmin, vmax=args.vmax)

        # adapt the xTicks and yTicks
        plt.gca().set_xticks(range(N_x))
        plt.gca().set_yticks(range(N_y))
        xlabels = ["%.2f" % elem for elem in np.unique(x).tolist()]
        ylabels = ["%.2f" % elem for elem in np.unique(y).tolist()]
        plt.gca().set_xticklabels(xlabels, rotation=90)
        plt.gca().set_yticklabels(ylabels)
        plt.xlabel("x [mm]")
        plt.ylabel("y [mm]")
        # add colorbar
        clb = plt.colorbar()
        clb.ax.set_title(colorbarlabel)

        save_string_tmp = save_string + "_%i" % plt_idx
        plot_utils.save_figure(outputfile=args.outputfile, inputfile=args.inputfile, save_string=save_string_tmp, save=args.save_plot)


if __name__ == "__main__":
    main()
