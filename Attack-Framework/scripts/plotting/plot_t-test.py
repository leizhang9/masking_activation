#!/usr/bin/env python3
import numpy as np
from matplotlib import pyplot as plt
import h5py
import argparse
from attack.helper import plot_utils

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for plotting absolute t-test values from the AISEC tool chain.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", type=str, required=True, help="Input file name with t-test results. (*.hdf5).")
    parser.add_argument("--fs", dest="fs", help="Sampling frequency [Hz]", type=float, required=True)
    parser.add_argument("--fclk", dest="fclk", help="Clock frequency [Hz]", type=float, required=True)
    parser.add_argument("--trigger-offset", dest="trigger_offset", type=float, default=0.0, help="Trigger offset [s]. Default: no offset, i.e. trigger ist assumed to be at first sample.")
    parser.add_argument("--time-start", dest="time_start", type=float, default=None, help="Start time [s] relative to trigger, i.e. negative values can be given.")
    parser.add_argument("--time-stop", dest="time_stop", help="Stop time [s] relative to trigger.", type=float, default=None)
    parser.add_argument(
        "--num-order",
        dest="num_order",
        type=int,
        default=1,
        help="Order of the t-test to plot (right now only univariate leakage",
    )
    parser.add_argument("--save-plot", dest="save_plot", action="store_true", help="Save the plot as pdf.")
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", type=str, default=None, help="Output file name for the plot. (*.pdf). Default: INPUTFILENAME_t-test.pdf")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name for plot configuration(*.json).", type=str, required=False, default=None)
    parser.add_argument("--plot-ylog", dest="plot_ylog", action="store_true", help="Logarithmic scaling for t-values.")
    parser.add_argument("--timescale", type=str, help="Time scale of the x-axis ('s','ms','us','ns','clockcycles')", default="us")
    parser.add_argument("-a", "--annotationfile", dest="annotationfile", metavar="filename", help="File name for plot annotations (*.csv). Lines contains LABEL,starttime,stoptime", type=str, required=False, default=None)

    args = parser.parse_args()
    save_string = "_t-test"

    # import plt.rcParam configuration
    plot_utils.load_plotconfig(args.configfile, save=args.save_plot)

    # specify file that contains the results of the t-test
    h5filehandle = h5py.File(args.inputfile, "r")
    # t-values are contained in group "/traces"
    t_values_keys = list(h5filehandle["/traces"].keys())
    # We are plotting the required order of the t-test.
    # Its always the first of three entries and each order adds a set of these three
    t = h5filehandle["/traces/" + t_values_keys[0 + int(((args.num_order - 1) * 3))]]
    if args.num_order > 1:
        save_string = save_string + "_%iorder" % args.num_order

    # generate the time vector with desired scaling
    time_scale, time_label = plot_utils.convert_timescale(timescale=args.timescale, fclk=args.fclk)
    time_vec, time_min, time_max = plot_utils.get_timevector(t_length=t.shape[0], fs=args.fs, time_start=args.time_start, time_stop=args.time_stop, time_scale=time_scale, trigger_offset=args.trigger_offset)

    plt.figure()
    # plot t-value
    plt.plot(time_vec, np.abs(t))
    # plot threshold of 4.5 that marks "significant" leakage
    plt.plot(time_vec, 4.5 * np.ones(len(t), dtype=np.uint8), linewidth=1.0)

    if args.plot_ylog:
        # set y-scale to logarithmic
        plt.yscale("log")
        ymin = 1
        # add to output filename
        save_string = save_string + "_log"
    else:
        # default: linear
        plt.yscale("linear")
        ymin = 0

    plt.xlabel("Time [%s] " % time_label)
    plt.ylabel("|t|")
    xmin = time_vec[time_min]
    xmax = time_vec[time_max]
    plt.xlim([xmin, xmax])
    ymax = max(max(np.abs(t)) * 1.1, 10)
    plt.ylim([ymin, ymax])
    plt.grid()
    # get some information about the y-dimensions for further use in annotations
    yspan = ymax - ymin
    save_string = plot_utils.annotate(ymax=ymax, yspan=yspan, ypos=0.9, annotationfile=args.annotationfile, save_string=save_string, timescale=time_scale)

    plot_utils.save_figure(outputfile=args.outputfile, inputfile=args.inputfile, save_string=save_string, save=args.save_plot)

    h5filehandle.close()
