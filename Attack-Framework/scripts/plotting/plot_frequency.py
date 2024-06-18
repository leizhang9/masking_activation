#!/usr/bin/env python3
import numpy as np
import h5py
import argparse
from matplotlib import pyplot as plt
import attack.helper.plot_utils as plot_utils
from attack.helper.utils import FrequencyUtils as freq_utils
from attack.helper.utils import HDF5utils as h5utils
from attack.helper.utils import MISCutils as misc_utils
import logging

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Script for plotting frequencies from the TUEISEC attack framework.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", type=str, required=True, help="Input file name with measurements. (*.hdf5).")
    parser.add_argument("-n", "--noisefile", dest="noisefile", metavar="filename", type=str, default=None, help="File name with noise floor. (*.hdf5).")
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", type=str, default=None, help="Output file name for the plot. (*.pdf). Default: INPUTFILENAME.pdf")
    parser.add_argument("-p", "--position", dest="group", help="Measurement position for evaluation. Default: all", default=None, nargs="*", type=str)
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset for evaluation.", default="samples_spectrum", type=str)
    parser.add_argument("--traces", dest="traces", help="Number of traces for plotting. Default: all", type=int, default=None, nargs="*")
    parser.add_argument("--repetitions", dest="repetitions", help="Number of repetitions for plotting. Default: all", type=int, default=None, nargs="*")
    parser.add_argument("--freq-min", dest="freq_min", help="Minimum frequency that is depicted [Hz].", type=float, default=None)
    parser.add_argument("--freq-max", dest="freq_max", help="Maximum frequency that is depicted [Hz].", type=float, default=None)
    parser.add_argument("--frequency-scale", type=str, help="Time scale of the x-axis ('Hz','kHz','MHz','GHz')", default="MHz")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name for plot configuration(*.json).", type=str, default=None)
    parser.add_argument("--save-plot", dest="save_plot", action="store_true", help="Save the plot as pdf.")
    parser.add_argument("-a", "--annotationfile", dest="annotationfile", metavar="filename", help="File name for plot annotations (*.csv). Lines contains LABEL,start freq.,stop freq.", type=str, required=False, default=None)
    parser.add_argument("--ymin", type=float, default=None, help="Minimum value of y-axis.")
    parser.add_argument("--ymax", type=float, default=None, help="Maximum value of y-axis.")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")

    args = parser.parse_args()
    # configure logger
    misc_utils.configure_logger(verbose=args.verbose)

    # string with parameters that is appended in case no file name is given
    save_string = "_frequency"

    # import plt.rcParam configuration
    plot_utils.load_plotconfig(args.configfile, save=args.save_plot)
    # specify file
    h5filehandle = h5py.File(args.inputfile, "r")
    # get noise file
    if args.noisefile is not None:
        noisefilehandle = h5py.File(args.noisefile, "r")
        save_string = save_string + "_denoised"
    else:
        noisefilehandle = None

    # default: use all positions
    if args.group is None:
        args.group = h5utils.hdf5_get_positions(h5filehandle)

    # generate frequency vector
    freqs, freq_scale, freq_label, bin_min, bin_max = plot_utils.generate_frequency_vector(h5filehandle=h5filehandle, freqscale=args.frequency_scale, freq_min=args.freq_min, freq_max=args.freq_max)
    # update string for saving
    save_string = save_string + "%.0f-%.0f_%s" % (freqs[0], freqs[-1], freq_label)

    for gdx, group in enumerate(args.group):
        # get samples handle
        sample_handle = h5filehandle["/" + group + "/" + args.dataset]
        # get array with selected traces
        samples, traces, repetitions = h5utils.hdf5_apply_selection(sample_handle=sample_handle, traces=args.traces, repetitions=args.repetitions, sample_min=bin_min, sample_max=bin_max)
        if noisefilehandle is not None:
            noise = freq_utils.get_noisefloor_frequency_domain(noisefilehandle=noisefilehandle, group=group, dataset=args.dataset, freq_min=args.freq_min, freq_max=args.freq_max, traces=traces, repetitions=repetitions)
            # subtract noise floor
            samples = samples - noise
            ylabel = "Denoised Spectral Density [dB]"
        else:
            ylabel = "Spectral Density [dB]"

        # plot
        fig, ax = plt.subplots(1, 1)
        # for multiple positions, add position number
        if len(args.group) > 1:
            plt.title(group)
        ax.plot(freqs, samples)
        ax.set_xlabel("Frequency [%s]" % freq_label)
        ax.set_ylabel(ylabel)
        ax.set_xlim([freqs[0], freqs[-1]])
        ax.grid()
        if len(repetitions) == 1 and len(traces) <= 16:
            ax.legend(traces, title="traces")
        elif len(traces) == 1 and len(repetitions) <= 16:
            ax.legend(repetitions, title="repetitions")
        else:
            _logger.warning("Omitting the legend: Too many traces/repetitions...")
        # get some information about the y-dimensions for further use in annotations
        yspan = np.max(samples) - np.min(samples)
        if args.ymax is None:
            ymax = np.max(samples) + yspan * 0.1
        else:
            ymax = args.ymax
        if args.ymin is None:
            ymin = np.min(samples) - yspan * 0.1
        else:
            ymin = args.ymin

        ax.set_ylim([ymin, ymax])

        save_string = plot_utils.annotate(ymax=ymax, yspan=yspan, ypos=0.9, annotationfile=args.annotationfile, save_string=save_string, timescale=freq_scale)
        output_string = save_string + group
        plot_utils.save_figure(outputfile=args.outputfile, inputfile=args.inputfile, save_string=output_string, save=args.save_plot)


# run program
if __name__ == "__main__":
    main()
