#!/usr/bin/env python3
import numpy as np
import h5py
import argparse
from matplotlib import pyplot as plt
from attack.helper import plot_utils
from attack.helper.utils import HDF5utils as h5utils
import re


def main():  # noqa: C901
    parser = argparse.ArgumentParser(description="Script for plotting measurements from the TUEISEC attack framework.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", type=str, required=True, help="Input file name with measurements. (*.hdf5).")
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", type=str, default=None, help="Output file name for the plot. (*.pdf). Default: INPUTFILENAME.pdf")
    parser.add_argument("-p", "--position", dest="group", help="Measurement position for evaluation", default=None, nargs="*", type=str)
    parser.add_argument("-d", "--dataset", dest="dataset", help="Name of dataset for evaluation. Default: 'samples'", default="samples", type=str)
    parser.add_argument("--traces", dest="traces", help="Indices of traces. Default: 0", type=int, default=[0], nargs="*")
    parser.add_argument("--repetitions", dest="repetitions", help="Indices of repetitions. Default: all", type=int, default=None, nargs="*")
    parser.add_argument("--time-start", dest="time_start", help="First time instance that is depicted [s]. ", type=float, default=None)
    parser.add_argument("--time-stop", dest="time_stop", help="Last time instance that is depicted [s]. ", type=float, default=None)
    parser.add_argument("--timescale", type=str, help="Time scale of the x-axis ('s','ms','us','ns','clockcycles')", default="us")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name for plot configuration(*.json).", type=str, default=None)
    parser.add_argument("--save-plot", dest="save_plot", action="store_true", help="Save the plot as pdf.")
    parser.add_argument("-a", "--annotationfile", dest="annotationfile", metavar="filename", help="File name for plot annotations (*.csv). Lines contains LABEL,starttime,stoptime", type=str, required=False, default=None)

    args = parser.parse_args()

    # string with parameters that is appended in case no file name is given
    save_string = "_samples"

    # import plt.rcParam configuration
    plot_utils.load_plotconfig(args.configfile, save=args.save_plot)

    # specify file
    h5filehandle = h5py.File(args.inputfile, "r")

    # default: use all positions
    if args.group is None:
        args.group = h5utils.hdf5_get_positions(h5filehandle)

    for gdx, group in enumerate(args.group):
        # get samples handle
        sample_handle = h5filehandle["/" + group + "/" + args.dataset]
        # get array with selected traces
        samples, _, _ = h5utils.hdf5_apply_selection(sample_handle=sample_handle, traces=args.traces, repetitions=args.repetitions)

        # try to get values from HDF5
        try:
            fclk = h5filehandle.attrs["fclk [Hz]"]
        except KeyError:
            fclk = 1
            print("Could not find clock frequency.")

        try:
            fs = sample_handle.attrs["sampling rate [S/s]"]
        except KeyError:
            fs = 1
            print("Could not find sampling frequency.")

        try:
            trigger_offset = sample_handle.attrs["trigger: delay [s]"]
        except KeyError:
            trigger_offset = 0

        # access the voltage range and convert sample values to voltage
        try:
            # get all attributes of the handle
            mylist = list(sample_handle.attrs.keys())
            # search for the entry that contains the voltage range (channel differs depending on configuration)
            r = re.compile(r"channel\d: range [V]*")
            range_attribute = list(filter(r.match, mylist))[0]
            voltage_range = sample_handle.attrs[range_attribute]
            if "Keysight" in sample_handle.attrs["scope: type"]:
                voltage_range = voltage_range / 2

            # adapt the samples to milliVolts
            ylabel = "Amplitude [mV]"
            if samples.dtype == np.uint8:
                # shift such that zero line fits
                samples = (samples.astype("int") - 127) / 256 * voltage_range * 1e3
            elif samples.dtype == np.int16:
                samples = (samples.astype("int") / 2**15) * voltage_range * 1e3
            else:
                samples = samples
                ylabel = "Amplitude"
        except BaseException:
            voltage_range = 1
            ylabel = "Amplitude"

        # generate the time vector with desired scaling
        time_scale, time_label = plot_utils.convert_timescale(timescale=args.timescale, fclk=fclk)
        time_vec, time_min, time_max = plot_utils.get_timevector(t_length=samples.shape[0], fs=fs, time_start=args.time_start, time_stop=args.time_stop, time_scale=time_scale, trigger_offset=trigger_offset)

        save_string = save_string + "%.0f-%.0f_%s" % (time_vec[time_min], time_vec[time_max], time_label)

        # plot
        fig, ax = plt.subplots(1, 1)
        if len(args.group) > 1:
            plt.title(group)
        ax.plot(time_vec, samples)
        ax.set_xlabel("Time [%s]" % time_label)
        ax.set_ylabel(ylabel)
        ax.set_xlim([time_vec[time_min], time_vec[time_max]])
        ax.grid()
        # get some information about the y-dimensions for further use in annotations
        yspan = np.max(samples) - np.min(samples)
        ymax = np.max(samples) + yspan * 0.1
        ymin = np.min(samples) - yspan * 0.1
        ax.set_ylim([ymin, ymax])

        save_string = plot_utils.annotate(ymax=ymax, yspan=yspan, ypos=0.9, annotationfile=args.annotationfile, save_string=save_string, timescale=time_scale)

        plot_utils.save_figure(outputfile=args.outputfile, inputfile=args.inputfile, save_string=save_string, save=args.save_plot)


# run program
if __name__ == "__main__":
    main()
