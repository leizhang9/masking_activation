import numpy as np
import h5py
from matplotlib import pyplot as plt
import argparse

# argument parser
parser = argparse.ArgumentParser(description='Script to plot the t-test result from a *.npy or *.hdf5 file.')
parser.add_argument('-i', '--inputfile', dest='input_file', metavar='filename', type=str, required=True,
                    help='Input file containing the result (*.npy or *.hdf5).')
parser.add_argument('--index', '--index', dest='sample_index', type=int, required=False, default=0,
                    help='Sample index which should be plotted (only possible for second order t-test!).')
parser.add_argument('-o', '--outputfile', dest='output_file', metavar='filename', type=str, required=False,
                    default='/tmp/result',
                    help='Output File where the plot jpg should be saved. If not specified, no image is saved.')

# TODO: Abtast und target frequenz angeben

# specify file that contains the results of the t-test

args = parser.parse_args()

if args.input_file.split(".")[1] == "npy":
    t = np.load(args.input_file)
else:
    f = h5py.File(args.input_file, "r")
    t = f["t_values"]

if len(t.shape) > 2:
    plt.figure()
    plt.plot(np.max(np.abs(t), axis=2)[:, 0])
    plt.plot(4.5 * np.ones(t.shape[2], dtype=np.uint8))
    plt.title("Max. t-value for combined Samples")
    plt.xlabel("Sample used to combine")
    plt.ylabel("Max. t-Value in Trace")
    plt.xlim([0, t.shape[2]])
    plt.ylim([0, np.max(np.max(np.abs(t), axis=2))+1])
    plt.grid()
    plt.savefig(args.output_file + "_second_order.png")
    t = t[args.sample_index, :, :]

for set in range(0, t.shape[0]):
    plt.figure()
    plt.plot(np.abs(t[set]))
    plt.plot(4.5 * np.ones(len(t[set]), dtype=np.uint8))
    if t.shape[0] > 1:
        plt.title('t-Test on Position: ' + str(set))
    else:
        plt.title('t-Test')
    plt.xlabel("Samples")
    plt.ylabel("t-Value")
    plt.xlim([0, len(t[set])])
    plt.ylim([0, max(np.abs(t[set])+3)])
    plt.grid()
    plt.savefig(args.output_file + str(set) + ".png")

if args.input_file.split(".")[1] == "hdf5":
    f.close()

plt.show()
