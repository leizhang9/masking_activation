#!/usr/bin/env python3
import numpy as np
from matplotlib import pyplot as plt
import h5py
import argparse
import os
from attack.helper import plot_utils
import re
import logging

_logger = logging.getLogger(__name__)


def load_cpoi_values(filename):
    """
    Loads CPOI values from the AISEC attacktool
    :param filename: filename of the HDF5
    :return cpoi: numpy array of CPOI values
    """
    try:
        # specify file that contains the results of the cpoi-test
        h5filehandle = h5py.File(filename, "r")
    except BaseException as e:
        _logger.warning("Could not load file %s" % filename)
        _logger.warning(e)
        return None
    # cpoi-values are contained in group "/traces"
    cpoi_values_key = list(h5filehandle["/traces"].keys())
    # We are plotting the required order of the cpoi-test.
    # Its always the first of three entries and each order adds a set of these three
    cpoi = np.array(h5filehandle["/traces/" + cpoi_values_key[0]])
    h5filehandle.close()
    return cpoi


def load_cpoi_with_linestyles_and_legends(filenames, lineformats):
    """
    Load CPOI data and corresponding entries for legend entries, line color and line styles
    :param filenames: list of CPOI inputfilesnames (HDF5)
    :param lineformats: filename of .csv file with legend entries, line styles and line colors for filename
    :return cpoi_values: numpy array of CPOIs
    :return legend_entry_list: list of legendentries
    :retunn linestyle_list: list of line styles
    :return linecolor_list: list of line colors

    """
    entry_list = list()  # empty list for legend entries
    style_list = list()  # empty list for line styles
    color_list = list()  # empty list for line color
    cpois = list()  # empty list for CPOI data

    # sort files by filename (for nicer legends)
    filenames.sort()
    file_count = 0

    for (
        fidx,
        file,
    ) in enumerate(filenames):

        # load CPOIs
        cpoi = load_cpoi_values(filename=file)
        if cpoi is not None:
            # if valid data is returned, append
            cpois.append(cpoi)
            # get the line styles and legend entries (either user defined or defaults)
            entry, line_color, line_style = plot_utils.read_linestyles(lineformatfile=lineformats, filename=file, line_count=file_count)
            entry_list.append(entry)
            style_list.append(line_style)
            color_list.append(line_color)
            # increase file count if valid data was provided
            file_count = file_count + 1

    # make numpy array from list
    cpois = np.array(cpois)

    return cpois, entry_list, color_list, style_list


def main():
    parser = argparse.ArgumentParser(description="Script for plotting CPOI values from the AISEC tool chain.")
    parser.add_argument("-i", "--inputfiles", dest="inputfile", metavar="filenames", type=str, required=True, nargs="*", help="Input file names with CPOI results. (*.hdf5/.*h5) or folder.")
    parser.add_argument("--fs", dest="fs", help="Sampling frequency [Hz]", metavar="frequency", type=float, required=True)
    parser.add_argument("--fclk", dest="fclk", help="Clock frequency [Hz]", metavar="frequency", type=float, required=True)
    parser.add_argument("--trigger-offset", dest="trigger_offset", metavar="time", type=float, default=0.0, help="Trigger offset [s]. Default: no offset, i.e. trigger ist assumed to be at first sample.")
    parser.add_argument("--time-start", dest="time_start", metavar="time", type=float, default=None, help="Start time [s] relative to trigger, i.e. negative values can be given.")
    parser.add_argument("--time-stop", dest="time_stop", metavar="time", help="Stop time [s] relative to trigger.", type=float, default=None)
    parser.add_argument("--save-plot", dest="save_plot", action="store_true", help="Save the plot as pdf.")
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", type=str, default=None, help="Output file name for the plot. (*.pdf). Default: INPUTFILENAME_cpoi.pdf")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name for plot configuration(*.json).", type=str, required=False, default=None)
    parser.add_argument("--timescale", type=str, help="Time scale of the x-axis ('s','ms','us','ns','clockcycles', 'samples')", default="us")
    parser.add_argument(
        "-a",
        "--annotationfiles",
        dest="annotationfiles",
        metavar="filename",
        type=str,
        required=False,
        default=None,
        nargs="*",
        help="File name(s) for plot annotations (*.csv).  First line may contain annotation type after '# [TYPE] ': Horizontal (default): Lines contains LABEL,starttime,stoptime Vertical: Lines contains LABEL,xposition,rel.yheight",
    )
    parser.add_argument("-l", "--lineformats", dest="lineformats", metavar="filename", type=str, required=False, default=None, help="File name with config for line styles and (*.csv). Lines contains FILENAME,legendlabel,linecolor,linestyle")
    parser.add_argument("--snr", dest="snr", action="store_true", help="Plot logarithmic SNR instead of CPOI.")
    parser.add_argument("--snr-lin", dest="snr_lin", action="store_true", help="Plot SNR on a linear scale instead of logarithmically.")
    parser.add_argument("--ymin", type=float, default=-60, help="Minimum value of y-axis for SNR.")
    parser.add_argument("--ymax", type=float, default=-20, help="Maximum value of y-axis for SNR.")
    parser.add_argument("--no-legend", dest="no_legend", action="store_true", help="Omit legend.")

    logging.basicConfig()

    args = parser.parse_args()
    if args.snr:
        # overwrite linear option (to have a clear behavior if both options are set)
        args.snr_lin = False
        save_string = "_snr"
        ylabel_string = "SNR [dB]"
    elif args.snr_lin:
        save_string = "_snrlin"
        ylabel_string = "SNR"
    else:
        save_string = "_cpoi"
        ylabel_string = "CPOI"

    # import plt.rcParam configuration
    plot_utils.load_plotconfig(args.configfile, save=args.save_plot)

    if os.path.isdir(args.inputfile[0]):
        # if folder is given: list all files in the folder
        inputfiles = [args.inputfile[0] + f for f in os.listdir(args.inputfile[0]) if os.path.isfile(args.inputfile[0] + f)]
    else:
        # if files are given, use file names
        inputfiles = args.inputfile

    # read the linestyles and legend entries
    cpoi_values, legend_entry, linecolor_list, linestyle_list = load_cpoi_with_linestyles_and_legends(filenames=inputfiles, lineformats=args.lineformats)

    # generate the time vector with desired scaling
    time_scale, time_label = plot_utils.convert_timescale(timescale=args.timescale, fclk=args.fclk, fs=args.fs)
    time_vec, time_min, time_max = plot_utils.get_timevector(t_length=cpoi_values[0].shape[0], fs=args.fs, time_start=args.time_start, time_stop=args.time_stop, time_scale=time_scale, trigger_offset=args.trigger_offset)

    if args.snr and not args.snr_lin:
        # Use decibel scale for SNR
        # convert to decibel (convert 0 input to Floating-point relative accuracy)
        cpoi_values = 20 * np.log10(np.clip(cpoi_values, a_min=np.spacing(1), a_max=None))

    # plot cpoi-value
    plt.figure()
    for ldx in range(0, cpoi_values.shape[0]):
        plt.plot(time_vec, cpoi_values[ldx, :].transpose(), label=legend_entry[ldx], linestyle=linestyle_list[ldx], color=linecolor_list[ldx])
    # set the legend above the plot in the middle and make sure at most four entries are used per column
    Ncol = 4
    if not args.no_legend:
        plt.legend(ncol=Ncol)
    plt.yscale("linear")

    plt.xlabel("Time [%s] " % time_label)
    plt.ylabel(ylabel_string)
    plt.xlim([time_vec[time_min], time_vec[time_max]])
    if args.snr or args.snr_lin:
        plt.ylim([args.ymin, args.ymax])
    else:
        plt.ylim([0, 1.1])
    plt.grid()

    if args.annotationfiles is not None:
        # Apply all different annotations
        for adx in range(0, len(args.annotationfiles)):
            save_string_tmp = plot_utils.annotate(ymax=1.1, yspan=1.1, ypos=0.9, annotationfile=args.annotationfiles[adx], save_string=save_string, timescale=time_scale)
            if adx == 0:
                # add the string only for the first annotation file to avoid lengthy file names
                save_string = save_string_tmp

    if args.save_plot and not (len(args.inputfile) == 1 and os.path.isfile(args.inputfile[0])):
        # if folder is provided, use last folder name as label for saving
        save_string = save_string + "_" + re.split("/", os.path.normpath(args.inputfile[0]))[-1]

    plot_utils.save_figure(outputfile=args.outputfile, inputfile=args.inputfile[0], save_string=save_string, save=args.save_plot)


# run program
if __name__ == "__main__":
    main()
