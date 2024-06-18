"""
Collection of plot utilities
"""

from matplotlib import pyplot as plt
import matplotlib as mpl
import csv
import json
import numpy as np
import re
import os
import logging
from attack.helper.utils import FrequencyUtils as freq_utils

_logger = logging.getLogger(__name__)


def annotate(ymax, yspan=None, ypos=0.9, annotationfile=None, save_string="", timescale=1):
    """
    Loads annotation LABEL,starttime,stoptime from *.csv file and puts them into plot
    :param yspan: ymax-ymin, i.e. values spanned on the y-axis
    :param ymax: maximum y-value in plot, where annotations are made
    :param ypos: Relative y-position for annotations
    :param annotationfile: File name for plot annotations (*.csv). Lines contains LABEL,starttime,stoptime
    :param save_string: (optional) string e.g. for output file that is extended by '_annotate' if file can be read.
    :param timescale: factor to adapt the length of the marker if the time is scaled (e.g. us: 1e6, ms:1e3)
    :return:
    """
    if annotationfile is not None:

        annotationlist, type = extract_annotation_data(annotationfile=annotationfile)
        if annotationlist is None:
            return save_string
        else:
            save_string = save_string + "_annotated"
        # Select the type of annotation
        if type == "vertical":
            annotate_vertical(annotationlist=annotationlist, ymax=ymax, timescale=timescale)
        elif type == "colormark":
            annotate_colormark(annotationlist=annotationlist, ymax=ymax, timescale=timescale)
        else:
            annotate_horizontal(annotationlist=annotationlist, ymax=ymax, timescale=timescale, ypos=ypos, yspan=yspan)
    return save_string


def extract_annotation_data(annotationfile):
    """
    Extracts the annotation data and the desired type from the .csv file
    :param annotationfile: file name
    :return result: list with lines of the .csv file
    return type: type of the annotation to select the correct function
    """
    with open(annotationfile) as fh:
        reader = csv.reader(fh)
        result = list(reader)
        if not result:  # result is empty
            _logger.warning("Could not read annotations from csv file.")
            return None, None
        elif re.match(r"^# \[TYPE\] ", result[0][0]):
            # the first line of the csv can contain the type of annotation
            type = re.split(r"^# \[TYPE\] ", result[0][0])[1]
            # delete the entry
            del result[0]
        else:
            type = None
    return result, type


def annotate_vertical(annotationlist, ymax, timescale):
    """
    Annotate vertical dotted lines
    :param annotationlist: list with lines of the .csv file
    :param ymax: maximum y-value in plot, where annotations are made
    :param timescale: factor to adapt the length of the marker if the time is scaled (e.g. us: 1e6, ms:1e3)
    :return:
    """
    for lines in range(0, len(annotationlist)):
        # read from line: label, start time, stop time
        # Note: times are relative to trigger offset!
        ann_label = annotationlist[lines][0]
        # convert to correct time scale
        ann_x = float(annotationlist[lines][1]) * timescale
        # starting point of vertical text
        ann_y_percent = float(annotationlist[lines][2])
        # optional: end point of vertical line (default: from top to bottom)
        try:
            ann_max = float(annotationlist[lines][3])
        except BaseException:
            # default: if entry was not provided.
            ann_max = 1
        plt.vlines(x=ann_x, ymin=0, ymax=ann_max * ymax, colors="k", linestyles="dotted", linewidth=0.25)
        plt.text(ann_x, ann_y_percent * ymax, ann_label, rotation=90, verticalalignment="bottom", fontsize=8)
    return


def annotate_colormark(annotationlist, timescale, ymax):
    """
    Annotate colorbars on top of a plot
    :param annotationlist: list with lines of the .csv file
    :param timescale: factor to adapt the length of the marker if the time is scaled (e.g. us: 1e6, ms:1e3)
    :param ymax: maximum y-value in plot, where annotations are made
    :return:
    """
    for lines in range(0, len(annotationlist)):
        # read from line: color, start time, stop time, (ymin, ymax, alpha)
        # Note: times are relative to trigger offset!
        ann_color = annotationlist[lines][0]
        # convert to correct time scale
        ann_x_min = float(annotationlist[lines][1]) * timescale
        ann_x_max = float(annotationlist[lines][2]) * timescale
        # optional: y values (default: bottom to top) and alpha
        try:
            ann_y_min = float(annotationlist[lines][3])
        except BaseException:
            # default: if entry was not provided.
            ann_y_min = 0
        try:
            ann_y_max = float(annotationlist[lines][4])
        except BaseException:
            # default: if entry was not provided.
            ann_y_max = ymax
        try:
            ann_y_alpha = float(annotationlist[lines][5])
        except BaseException:
            # default: if entry was not provided.
            ann_y_alpha = 0.1
        plt.axvspan(xmin=ann_x_min, xmax=ann_x_max, ymin=ann_y_min, ymax=ann_y_max, alpha=ann_y_alpha, facecolor=ann_color)
    return


def annotate_horizontal(annotationlist, ymax, timescale, ypos=0.9, yspan=None):
    """
    Annotate horizontal markers in a plot
    :param annotationlist: list with lines of the .csv file
    :param ymax: maximum y-value in plot, where annotations are made
    :param timescale: factor to adapt the length of the marker if the time is scaled (e.g. us: 1e6, ms:1e3)
    :param ypos: Relative y-position for annotations
    :param yspan: ymax-ymin, i.e. values spanned on the y-axis
    :return:
    """
    if yspan is None:
        # assume start at 0, i.e. maximum value is
        yspan = ymax
    for lines in range(0, len(annotationlist)):
        # read from line: label, start time, stop time
        # Note: times are relative to trigger offset!
        ann_label = annotationlist[lines][0]
        # convert to correct time scale
        ann_start = float(annotationlist[lines][1]) * timescale
        ann_stop = float(annotationlist[lines][2]) * timescale

        ann_color = "k"
        ann_ypos = (ypos * yspan) - (yspan - ymax)
        # draw horizontal line
        # Option A: use axhline.
        # (+) marker can be used
        # (-) positioning is relative, i.e. if you zoom annotations are kept at the relative position...
        # (-) you need to convert the absolute values to relative values in range (0,1)
        #
        # hline_start = (ann_start - xmin) / (xmax - xmin)
        # hline_stop = (ann_stop - xmin) / (xmax - xmin)
        #
        # plt.axhline(linewidth=1, y=ann_ypos, xmin=hline_start, xmax=hline_stop, color=ann_color, linestyle='--', marker="|")

        # Option B: use hline
        # (+) absolute positioning
        # (-) no markers, i.e. delimiters have to be added manually
        # --> if using zoom size of delimiter changes, but position stays correctly
        ann_del_length = 0.025
        # add horizontal line
        plt.hlines(linewidth=1, y=ann_ypos, xmin=ann_start, xmax=ann_stop, colors=ann_color)
        # add vertical delimiters
        plt.vlines(linewidth=1, x=ann_start, ymin=ann_ypos - ann_del_length * yspan, ymax=ann_ypos + ann_del_length * yspan, colors=ann_color)
        plt.vlines(linewidth=1, x=ann_stop, ymin=ann_ypos - ann_del_length * yspan, ymax=ann_ypos + ann_del_length * yspan, colors=ann_color)

        # add text on top/bottom of line: odd entries on top of line, even entries below
        # Note: works only if the annotations are sorted in the .csv along time axis
        plt.text(ann_start, ann_ypos + 0.03 * yspan, ann_label)
    return


def read_linestyles(lineformatfile, filename, line_count):
    """
    Read the legend entry, line style and line color for different files from a .csv
    Assumed format of the .csv: FILENAME, LEGENDENTRY, LINECOLOR, LINESTYLE
    FILENAME checks only for the base filename, i.e. the folder must not be contained!
    :param lineformatfile: filename of .csv file with legend entries, line styles and line colors for filename
    :param filename: list of inputfiles, for which entries are searched in the .csb
    :param line_count: counter of the current line (used to determine default colors if necessary)
    :return legendentry: string for legend entry (default: base filename)
    :return linecolor: line color (default: from 'prop_cycle' colormap)
    :retunn linestyle: line style (default: solid)
    """

    # default colors (for use if colors are not specified)
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    default_colors = prop_cycle.by_key()["color"]
    diff_colors = len(default_colors)

    # Default: use file base name as entry for legend
    f_name, f_ext = os.path.splitext(os.path.basename(filename))
    legendentry = f_name
    # Default: solid line in default colors
    linestyle = "solid"
    linecolor = default_colors[line_count % diff_colors]

    # get legend entry and line style and color from .csv file
    if lineformatfile is not None:
        try:
            # if a label and linestyle file is provided, check whether there is an entry for the file
            with open(lineformatfile) as fh:
                reader = csv.reader(fh)
                result = list(reader)
                for lines in range(0, len(result)):
                    # check each line of the .csv whether it contains line and legend entries for the filname
                    if result[lines][0] == f_name + f_ext:
                        # if entry is found, use specified label
                        legendentry = result[lines][1]
                        # if no color is given or the colums is not specified at all, use a default color
                        try:
                            linecolor = result[lines][2]
                        except IndexError as e:
                            _logger.warning("No color given/Column for linecolor not defined, make sure your .csv has entries in the third column.")
                            _logger.warning(e)

                        # if the column is not specified at all, use 'solid' as default line style
                        # NOTE: if one entry has a line style, all entries with an empty entry are not displayed
                        try:
                            linestyle = result[lines][3]
                        except IndexError as e:
                            _logger.warning("Column for line style not defined, make sure your .csv has entries in the fourth column.")
                            _logger.warning(e)
        except BaseException as e:
            _logger.warning("There is a problem using the lines and labels .csv %s" % lineformatfile)
            _logger.warning(e)
    return legendentry, linecolor, linestyle


def load_plotconfig(configfile, save=False):
    """
    Read config file (*.json) for customizing matplotlib plots
    Further details on paratemers, c.f.: https://matplotlib.org/3.2.1/tutorials/introductory/customizing.html
    :param configfile: *.json file with rcParams
    :return:
    """

    # load configuration of plot from .json
    if configfile is not None:
        with open(configfile, "r") as cf:
            config = json.load(cf)
            plt.rcParams.update(config)
    else:
        _logger.warning("No config file given, please specify with -c if you want nice plots.")

    # legacy behavior: if the backend is not defined in the config, use pgf and avoid crashed with LaTeX otherwise
    if save and (configfile is None or "backend" not in config):
        # use pgf for output
        mpl.use("pgf")
    elif not save:
        # make sure that tex is not used for view-only
        plt.rcParams["text.usetex"] = False

    return


def convert_timescale(timescale, fclk=1, fs=1):
    """
    Returns the corresponding scaling factor and axis label for a timescale string. The conversion factor is applied to
    a time vector in seconds, e.g. to convert into ms, all values have to be multiplied by 1e3.
    :param timescale: 'ms', 'us', 'ns', 'clockcycles'. default: 's'
    :param fclk: (optional) clock frequency needed to convert the time axis into clock cycles
    :param fs: (optional) sampling frequency needed to convert the time axis into samples
    :return: time_scale: factor to scale into desired time scale
    :return: time_label: sting with label for e.g. axis description or to add to file name
    """
    # sample are given in seconds, calculate conversion factor (time_scale) and axis labeling
    if timescale == "ms":
        time_scale = 1e3
        time_label = "ms"
    elif timescale == "us":
        time_scale = 1e6
        time_label = "us"
    elif timescale == "ns":
        time_scale = 1e9
        time_label = "ns"
    elif timescale == "clockcycles":
        time_scale = fclk
        time_label = "clock cycles"
    elif timescale == "samples":
        time_scale = fs
        time_label = "samples"
    else:
        time_scale = 1
        time_label = "s"
    return time_scale, time_label


def convert_samples_to_timeunit(samples, time_scale, fs):
    """
    Returns the sample index into the the desired equivalent time unit.
    :param samples: sample index
    :param time_scale: factor to scale into desired time scale (as obtained from 'convert_timescale')
    :param fs: sampling frequency
    :return: samples: value in desired time units
    """
    samples = samples * time_scale / fs

    return samples


def get_timevector(t_length, fs=1, time_start=None, time_stop=None, time_scale=1, trigger_offset=0.0):
    """
    Return a vector with entries for the time axis along with the entries (bins) that belong to the desired time_start
    and time_stop. By using trigger_offset the vector can be shifted, e.g. to be aligned with the trigger or the
    beginning of a certain operation
    :param t_length: length of the desired time vector (basically determined as time*fs)
    :param fs: sampling frequency (to convert length to seconds)
    :param time_start: beginning of the time vector (default: first sample)
    :param time_stop: end of the time vector (default: last sample)
    :param time_scale: factor to scale into desired time scale (c.f. function 'convert_timescale')
    :param trigger_offset: offset [seconds], e.g. to align the time vector with trigger
    :return: vector containing time entries, unit is 1/time_scale seconds.
    """

    # time vector
    time_vec = np.arange(0, t_length) / fs * time_scale + trigger_offset * time_scale

    # find desired limits in time vector
    if time_start is not None:
        # find first bin bigger than time_start and take the one before (i.e. time_start is included!)
        # Make sure that only available values can be taken
        time_bin_min = max(np.argmax(time_vec > time_start * time_scale) - 1, 0)
    else:
        time_bin_min = 0

    if time_stop is not None:
        # find last bin smaller than time_stop and the take next one (i.e. time_stop is included!)
        # Make sure that only available values can be taken
        # TODO: make sure that maximum value is taken, if specified range is more than available (currently not caught)
        time_bin_max = min(np.argmin(time_vec < time_stop * time_scale) + 1, len(time_vec) - 1)
    else:
        time_bin_max = len(time_vec) - 1

    return time_vec, time_bin_min, time_bin_max


def convert_freqscale(freqscale):
    """
    Returns the corresponding scaling factor and axis label for a freqscale string. The conversion factor applies to
    a frequency vector in Hertz, e.g. to convert into MHz, all values have to be multiplied by 1e-6.
    :param freqscale: 'kHz', 'MHz', 'GHz'. default: 'Hz'
    :return: freq_scale: factor to scale into desired time scale
    :return: freq_label: sting with label for e.g. axis description or to add to file name
    """
    # sample are given in seconds, calculate conversion factor (freq_scale) and axis labeling
    if "kHz" in freqscale:
        freq_scale = 1e-3
        freq_label = "kHz"
    elif "MHz" in freqscale:
        freq_scale = 1e-6
        freq_label = "MHz"
    elif "GHz" in freqscale:
        freq_scale = 1e-9
        freq_label = "GHz"
    else:
        freq_scale = 1
        freq_label = "Hz"
    return freq_scale, freq_label


def generate_frequency_vector(h5filehandle, freqscale="MHz", freq_min=None, freq_max=None):
    """
    Generate frequency vector with desired scaling and limits for minimum and maximum frequency
    :param h5filehandle: handle of the HDF5 file
    :param freqscale: factor to scale into desired time scale
    :param freq_min: minimum frequency [Hz]
    :param freq_max: maximum frequency [Hz]
    :return freqs: array with frequency values, scaled and limited according to the input parameters
    :return: freq_scale: factor to scale into desired time scale
    :return: freq_label: sting with label for e.g. axis description or to add to file name
    :return: bin_min: index/bin corresponding to the value of freq_min in the original freqs array
    :return: bin_max: index/bin corresponding to the value of freq_max in the original freqs array
    """
    # generate the time vector with desired scaling
    freq_scale, freq_label = convert_freqscale(freqscale=freqscale)
    # load frequencies
    freqs = np.array(h5filehandle["/frequencies"])
    # get corresponding bins
    bin_min, bin_max = freq_utils.get_frequency_bins(freqs, freq_min=freq_min, freq_max=freq_max)
    # limit and rescale frequencies
    freqs = freqs[bin_min : bin_max + 1] * freq_scale
    return freqs, freq_scale, freq_label, bin_min, bin_max


def meander_get_unique_xy_values(x, y):
    """
    Get the unique x and y values of the meander pattern
    :param x: 1D-array with x-values
    :param y: 1D-array with y-values
    :return N_x: unique x-values
    :return N_y: unique y-values
    """
    # get number of entries in each direction
    N_x = len(np.unique(x))
    N_y = len(np.unique(y))
    return N_x, N_y


def invert_meander(samples, x, y):
    """
    Takes measurements that were obtained from a meander pattern and creates a 2D-array of them with the correct order
    in space.
    :param samples: 1D-array with samples from a meander pattern
    :param x: 1D-array with x-values
    :param y: 1D-array with y-values
    :return samples: 2D-array with reshaped samples corresponding to x-y dimensions
    :return N_x: unique x-values
    :return N_y: unique y-values
    """
    N_x, N_y = meander_get_unique_xy_values(x=x, y=y)
    # reshape the result to an array
    samples = np.reshape(samples, (N_y, N_x))
    # apply meander: meander starts in the lower-left corner
    # flip every second dimension
    if N_y % 2 == 0:
        # for even number of x-positions: flip the even lines
        samples[0::2, :] = np.fliplr(samples[0::2, :])
    else:
        # for odd number of x-positions: flip the odd lines
        samples[1::2, :] = np.fliplr(samples[1::2, :])
    return samples, N_x, N_y


def invert_meander_multitrace(samples, x, y):
    """
    Takes mutiple measurements that were obtained from a meander pattern and creates a 3D-array of them with the correct
     order in space.
    :param samples: 2D-array with samples from a meander pattern (positions x traces)
    :param x: 1D-array with x-values
    :param y: 1D-array with y-values
    :return samples: 3D-array with reshaped samples corresponding to x-y dimensions (xpos x ypos x traces)
    :return N_x: unique x-values
    :return N_y: unique y-values
    """
    # preallocate
    num_traces = samples.shape[1]
    N_x, N_y = meander_get_unique_xy_values(x=x, y=y)
    samples_new = np.zeros((N_y, N_x, num_traces))
    # convert for each trace
    for trace_idx in range(num_traces):
        samples_new[:, :, trace_idx], _, _ = invert_meander(samples=samples[:, trace_idx], x=x, y=y)
    return samples_new, N_x, N_y


def save_figure(outputfile=None, inputfile="default", save_string="", save=False):
    """
    Switches between saving a figure or showing the plot. If no output filename is provided in save mode, it is derived
    from the input filename. An additional string, that may contain parameters, etc. can be added.
    :param outputfile: (optional) string with an output filename
    :param inputfile: string with the name of the input file from which figures are generated
    :param save_string: additional string that is inserted into the output filename, e.g. with parameters
    :param save: flag whether to store or display a figure
    """

    if save:
        if outputfile is None:
            # use input file name
            outputfile_name = inputfile
        else:
            outputfile_name = outputfile

        # normalize path, i.e. strip trailing '/'
        outputfile_name = os.path.normpath(outputfile_name)

        file_path, file_extension = os.path.splitext(outputfile_name)

        if outputfile is None:
            # use the same name as the input file, but with the extension defined by the rcParams for plotting
            outputfile_name = file_path + "." + mpl.rcParams["savefig.format"]
        elif file_extension != "":
            # if a file name with an extension is provided, do not add the string (do not overwrite the user input)
            save_string = ""
        else:
            # if a folder is provided, use the input filename and put the plot in the specified folder
            outputfile_name = outputfile_name + "/" + os.path.splitext(os.path.basename(inputfile))[0] + "." + mpl.rcParams["savefig.format"]

        # create folder and subfolders if not existent
        if not os.path.isdir(os.path.split(os.path.realpath(outputfile_name))[0]):
            os.makedirs(os.path.split(os.path.realpath(outputfile_name))[0])

        # add an optional string to the given output file name (e.g. to distinguish parameters)
        outputfile_name = os.path.splitext(outputfile_name)[0] + save_string + os.path.splitext(outputfile_name)[1]

        # use rcParams (https://matplotlib.org/3.1.0/tutorials/introductory/customizing.html#matplotlib-rcparams) to
        # specify the details of plotting
        plt.savefig(outputfile_name)
        plt.close()
    else:
        plt.show()
    return
