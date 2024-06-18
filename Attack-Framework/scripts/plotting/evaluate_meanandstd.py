#!/usr/bin/env python3
import h5py
import numpy as np
import argparse
import matplotlib.pyplot as plt


def plot_legacy(file_name, group="0000", dataset="samples", trace_start=0, trace_stop=None, trace_step=1, sample_start=0, sample_stop=None, trace_thres=5, y_min=None, y_max=None):

    # create HDF5 file object
    h5filehandle = h5py.File(file_name, "r")
    # create HDF5 dataset object of samples
    dset = h5filehandle.get(group + "/" + dataset)

    if sample_stop is None:
        sample_stop = dset.shape[1]

    if trace_stop is None:
        trace_stop = dset.shape[0]

    d = dset[trace_start:trace_stop:trace_step, sample_start:sample_stop, 0]
    sample_vec = np.arange(sample_start, sample_stop)

    h5filehandle.close()

    # get the median for each point-in-time of interest
    d_med = np.median(d, axis=0)
    d_std = np.std(d, axis=0)
    d_av = np.mean(d, axis=0)

    if y_min is None:
        y_min = 0.9 * min(d_av - d_std)

    if y_max is None:
        y_max = 1.1 * max(d_av + d_std)

    # plot average and average +/- std

    plt.figure()
    plt.plot(sample_vec, d_av, label="av")
    plt.plot(sample_vec, d_med, "gray", label="median")
    plt.plot(sample_vec, d_av + d_std, "r--", label="av +/- std")
    plt.plot(sample_vec, d_av - d_std, "r--")
    plt.grid()
    plt.legend()
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    plt.xlim((sample_vec[0], sample_vec[-1]))
    plt.ylim((y_min, y_max))
    # plt.legend((h1, h2), ('av.', 'median'))  #%, 'av+std', 'av-std')
    plt.title(file_name)
    plt.savefig(file_name.split(".")[0] + "_" + group + "_amplitudes.png")

    perc_bad = sum(abs(d - d_med) > trace_thres) / len(d)

    print("On average %.3f of the traces diverge more than %i samples from the median for at least one of the samples." % (np.mean(perc_bad), trace_thres))
    for idx in range(0, len(perc_bad)):
        print("Sample %i: %.3f diverge." % (sample_vec[idx], perc_bad[idx]))

    plt.figure()
    plt.plot(np.sort(d, axis=0))
    plt.grid()
    plt.xlabel("Trace")
    plt.title(file_name)
    plt.ylim(0, 255)
    plt.savefig(file_name.split(".")[0] + "_" + group + "_sorted.png")
    plt.show()

    return


def boxplot_of_samples(file_name, group="0000", dataset="samples", trace_start=0, trace_stop=None, trace_step=1, sample_start=0, sample_stop=None, trace_thres=5, y_min=None, y_max=None, whisker_range=1.5):

    # create HDF5 file object
    h5filehandle = h5py.File(file_name, "r")
    # create HDF5 dataset object of samples
    dset = h5filehandle.get(group + "/" + dataset)

    if sample_stop is None:
        sample_stop = dset.shape[1]

    if trace_stop is None:
        trace_stop = dset.shape[0]

    d = dset[trace_start:trace_stop:trace_step, sample_start:sample_stop, 0]
    sample_vec = np.arange(sample_start, sample_stop)

    h5filehandle.close()

    # boxplot
    plt.figure()
    bp_dict = plt.boxplot(d, positions=np.arange(sample_start, sample_stop), whis=whisker_range)
    plt.grid()
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    # plt.xlim((sample_vec[0], sample_vec[-1]))

    plt.title(file_name)

    print("Percent of outliers:")
    outliers = np.zeros(d.shape[1], dtype=np.int)
    for idx in range(0, d.shape[1]):
        outliers[idx] = len(bp_dict["fliers"][idx].get_data()[1])
        print("Sample %i: %.3f" % (sample_vec[idx], 100 * outliers[idx] / d.shape[0]))
    # save the whiskers, i.e., for use in range filter
    whiskers = np.zeros((d.shape[1], 2))
    samples_idx = 0
    print("\nBoundaries of whiskers are:")
    for idx in range(0, 2 * d.shape[1]):

        if idx % 2 == 0:
            whiskers[samples_idx, 0] = int(bp_dict["whiskers"][idx].get_data()[1][1])
        else:
            whiskers[samples_idx, 1] = int(bp_dict["whiskers"][idx].get_data()[1][1])
            print("%i:%i," % (whiskers[samples_idx, 0], whiskers[samples_idx, 1]))
            samples_idx = samples_idx + 1

    if y_min is None:
        y_min = 0.9 * np.min(whiskers[:])

    if y_max is None:
        y_max = 1.1 * np.max(whiskers[:])
    plt.ylim((y_min, y_max))
    plt.savefig(file_name.split(".")[0] + "_" + group + "_boxplot.png")
    plt.show()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script determine the number of different byte values of the plaintext from a dataset.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="HDF5 file (*.hdf5/*.h5)", type=str, required=True)
    parser.add_argument("--sample-start", dest="sample_start", metavar="First sample", help="First sample", type=int, default=624)
    parser.add_argument("--sample-stop", dest="sample_stop", metavar="Last sample", help="Last sample", type=int, default=631)
    parser.add_argument("--trace-start", dest="trace_start", metavar="First trace", help="First trace", type=int, default=0)
    parser.add_argument("--trace-stop", dest="trace_stop", metavar="Last trace", help="Last trace", type=int, default=None)
    parser.add_argument("--trace-step", dest="trace_step", metavar="Step trace", help="Take every i'th trace", type=int, default=1)
    parser.add_argument("--y-min", dest="y_min", help="Minimum y-value for amplitudes", type=int, default=None)
    parser.add_argument("--y-max", dest="y_max", help="Maximum y-value for amplitudes", type=int, default=None)
    parser.add_argument("--whisker-range", dest="whisker_range", help="Multiple of Inter Quartile Range (IQR) at which" "the whiskers are set. Default: 1.5.", type=int, default=1.5)
    parser.add_argument("--trace-threshold", dest="trace_threshold", metavar="Threshold", help="Define deviation from the median in sample points. (For legacy plots only.)", type=int, default=5)
    parser.add_argument("--legacy", dest="legacy", action="store_true", default=False, help="Plot legacy plots with mean and standard deviation. Default: False")

    args = parser.parse_args()

    boxplot_of_samples(args.inputfile, group="0000", dataset="samples", trace_start=args.trace_start, trace_stop=args.trace_stop, trace_step=args.trace_step, y_max=args.y_max, y_min=args.y_min, sample_start=args.sample_start, sample_stop=args.sample_stop, whisker_range=args.whisker_range)

    if args.legacy:
        plot_legacy(args.inputfile, group="0000", dataset="samples", trace_start=args.trace_start, trace_stop=args.trace_stop, trace_step=args.trace_step, y_max=args.y_max, y_min=args.y_min, sample_start=args.sample_start, sample_stop=args.sample_stop, trace_thres=args.trace_threshold)
