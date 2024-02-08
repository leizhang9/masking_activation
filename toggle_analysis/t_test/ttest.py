# TODO extend plotting for multiple sets
import numpy as np
import h5py
import multiprocessing as mp
import ctypes as ct
import argparse
from matplotlib import pyplot as plt

# argument parser
parser = argparse.ArgumentParser(
    description='Script to perform horizontal attack on BCH.')
parser.add_argument('-i', '--inputfile', dest='input_file', metavar='filename', type=str, required=True,
                    help='Input file containing the measurements (*.hdf5).')
parser.add_argument('-o', '--outputfile', dest='output_file', metavar='filename', type=str, required=False,
                    help='Output file containing the results (*.hdf5).')
parser.add_argument('-p', '--processes', dest='num_processes', type=int, required=False, default=1,
                    help='Number of processes to be used for the t-test.')
parser.add_argument('--measure-processes', dest='measure_processes', type=int, required=False, default=1,
                    help='Number of processes to be used for each set or sample if second_order is performed.')
parser.add_argument('--seg-size', dest='seg_size', type=int, required=False, default=1,
                    help='Size of the segments.')
parser.add_argument('--dist', dest='dist', type=str, required=False, metavar='distinquisher',
                    help='Distinquiser on which the datasets can be separated.')
parser.add_argument('--dataset', dest='dset', type=str, required=False, default="leakages",
                    help='Dataset that holds the samples.')
parser.add_argument('--second_order', dest='order', type=bool, required=False, default=False,
                    help='Set to true if second-order t-test should performed.')
parser.add_argument('--plot-only', dest='plot_only', type=bool, required=False, default=False,
                    help='Plots the result in a window from an already computed result.')


args = parser.parse_args()

# specify hdf5 file that contains the data
path = args.input_file

# specify number of processes to be used
n_processes = args.measure_processes
# specify number of subprocesses
n_sub = args.num_processes
# specify size of segments (smaller segment size reduces RAM but increases processing time)
# maximal value is file['0000']['samples'].shape[1]
seg_size = args.seg_size
dset = args.dset
output_file = args.output_file
order = args.order
if output_file is None:
    # specify output path is done automatically
    output_file = args.input_file.split(".")[0] + str("_result")


if args.plot_only is False:
    ####################
    # program
    ####################

    # open hdf5 file
    file = h5py.File(path, 'r')

    # determine number of measuring positions
    n_measurement = 1
    if n_measurement == 0:
        print('Found only a single Dataset! Use newest version of attack framework!')
        n_measurement = 1

    # allocate shared memory to store t-values
    if not order:
        t_shared = mp.Array(
            ct.c_double, (file[dset].shape[1] * n_measurement))
        # transform shared memory to numpy array
        t_val = np.frombuffer(t_shared.get_obj())
        t_val = t_val.reshape((n_measurement, file[dset].shape[1]))
    else:
        t_shared = mp.Array(
            ct.c_double, (n_processes * file[dset].shape[1] * n_measurement))
        # transform shared memory to numpy array
        t_val = np.frombuffer(t_shared.get_obj())
        t_val = t_val.reshape((n_processes, n_measurement, file[dset].shape[1]))

    # allocate shared memory for sampling rate and clock cycle
    sampling_rate = mp.Value(ct.c_double)
    clock_cycle = mp.Value(ct.c_double)

    # calculate amount of samples that corresponds to a clock cycle

    # close file
    file.close()

    def perform_eval_segment(set, p_nr, t_val, segment, size, data, segment_size, index0, index1):
        np.seterr(divide='ignore', invalid='ignore')

        q0 = data[index0, p_nr * segment_size: p_nr *
                  segment_size + segment_size]
        q1 = data[index1, p_nr * segment_size: p_nr *
                  segment_size + segment_size]

        bottom = np.sqrt((q0.var(axis=0) / len(index0)) +
                         (q1.var(axis=0) / len(index1)))

        # replace values that are zero otherwise there will be an error during devision
        bottom[bottom == 0] = 0.001

        t_val[set, segment * size + p_nr * segment_size:segment * size + p_nr * segment_size +
              segment_size] = (q0[0:len(index0)].mean(axis=0) - q1[0:len(index1)].mean(axis=0)) / bottom

    # function that performs the t-test
    # parameters:
    #   set = dataset of the hdf5 file
    #   filepath = path and name of the hdf5 file
    #   size = segment size in which the measured traces are split to reduce required memory
    #   align = specify if traces should be aligned or not
    def perform_t_test(set, filepath, t_val, size=5, current_sample=-1):
        # open hdf5 file
        file = h5py.File(filepath, "r")
        samples = file[dset]

        # calculate number of segments
        segments = int(file[dset].shape[1] / size)

        # find indizes of both sets: 0: constant key, 1: variable key
        index0 = []
        index1 = []

        for i in range(0, int(samples.shape[0])):
            if i < int(samples.shape[0] / 2):
                # set of same code word
                index0.append(i)
            else:
                # set of random code words
                index1.append(i)
        index0 = np.array(index0, dtype=np.int64)
        index1 = np.array(index1, dtype=np.int64)

        proc = []

        sub_processed = 0

        while sub_processed < segments:
            if sub_processed + n_sub < segments:
                if current_sample >= 0:
                    data = (samples[:, sub_processed * size: (sub_processed + n_sub) * size] - np.mean(samples[:, sub_processed * size: (sub_processed + n_sub) * size], axis=1).repeat(n_sub*size).reshape(samples.shape[0], n_sub*size)).astype(np.float32) * (samples[:, current_sample].repeat(n_sub * size).reshape(samples.shape[0], n_sub * size) - np.mean(samples[:, sub_processed * size: (sub_processed + n_sub) * size], axis=1).repeat(n_sub*size).reshape(samples.shape[0], n_sub*size)).astype(np.float32)
                else:
                    data = samples[:, sub_processed * size: (sub_processed + n_sub) * size]

                for i in range(0, n_sub):
                    p = mp.Process(target=perform_eval_segment, args=(
                        set, i, t_val, sub_processed, size, data, size, index0, index1))
                    p.start()
                    proc.append(p)

            else:

                n = segments - sub_processed
                if current_sample >= 0:
                    data = (samples[:, sub_processed * size:] - np.mean(samples[:, sub_processed * size:], axis=1).repeat(samples.shape[1] - sub_processed * size).reshape(samples.shape[0], samples.shape[1] - sub_processed * size)).astype(np.float32) * (samples[:, current_sample].repeat(samples.shape[1] - sub_processed * size).reshape(samples.shape[0], samples.shape[1] - sub_processed * size) - np.mean(samples[:, sub_processed * size:], axis=1).repeat(samples.shape[1] - sub_processed * size).reshape(samples.shape[0], samples.shape[1] - sub_processed * size)).astype(np.float32)
                else:
                    data = samples[:, sub_processed * size:]

                # update size
                last_seg_size = int(data.shape[1]/n)
                for i in range(0, n):
                    p = mp.Process(target=perform_eval_segment, args=(
                        set, i, t_val, sub_processed, size, data, last_seg_size, index0, index1))
                    p.start()
                    proc.append(p)

            for p in proc:
                p.join()

            sub_processed += n_sub

            if not order:
                print("########################")
                if sub_processed >= segments:
                    print("Set " + str(set) + ": 100.0%" + " processed")
                else:
                    print("Set " + str(set) + ": " + str(np.around(100 *
                          sub_processed / segments, 2)) + "%" + " processed")

        file.close()
        if not order:
            print("########################")
            print("Set: " + str(set).zfill(4))
            print('Max t-value: ', np.max(np.abs(t_val[set])))

    def start_control_process(t_val, path, seg_size, current_sample):
        # generate several processes to perform t-test
        processed = 0
        while processed < n_measurement:
            procs = []

            if not order:
                print("************************")
                print("Progress: %.2f%%" % (100 * (processed / n_measurement)))
                print("************************")

            if processed + n_processes < n_measurement:
                for i in range(0, n_processes):
                    p = mp.Process(target=perform_t_test, args=(
                        i + processed, path,  t_val, seg_size, current_sample))
                    p.start()
                    procs.append(p)

            else:
                n = n_measurement - processed
                for i in range(0, n):
                    p = mp.Process(target=perform_t_test, args=(
                        i + processed, path, t_val, seg_size, current_sample))
                    p.start()
                    procs.append(p)

            for p in procs:
                p.join()
            processed += n_processes

    f_out = h5py.File(output_file + str(".hdf5"), "w")
    if order:
        current_sample = 0
        dset_out = f_out.create_dataset("t_values", (t_val.shape[2], t_val.shape[1], t_val.shape[2]), dtype=np.float32)
        n_samples = t_val.shape[2]
    else:
        current_sample = -1
        dset_out = f_out.create_dataset("t_values", t_val.shape, dtype=np.float32)
        n_samples = t_val.shape[1]

    while current_sample < n_samples:
        if order:
            print("Second-Order Progress: %.2f%%" % (100 * (current_sample / t_val.shape[2])), end='\r')
        if current_sample >= 0:
            procs = []
            if current_sample + n_processes < t_val.shape[2]:
                for i in range(0, n_processes):
                    p = mp.Process(target=start_control_process, args=(
                        t_val[i], path, seg_size, i + current_sample))
                    p.start()
                    procs.append(p)

            else:
                n = t_val.shape[2] - current_sample
                for i in range(0, n):
                    p = mp.Process(target=start_control_process, args=(
                        t_val[i], path, seg_size, i + current_sample))
                    p.start()
                    procs.append(p)

            for p in procs:
                p.join()
        else:
            start_control_process(t_val, path, seg_size, current_sample)

        if current_sample < 0:
            current_sample = t_val.shape[1]
            dset_out[:, :] = t_val[:, :]
        else:
            if current_sample + n_processes < t_val.shape[2]:
                dset_out[current_sample:current_sample+n_processes, :, :] = t_val[:, :, :]
            else:
                dset_out[current_sample:, :, :] = t_val[:t_val.shape[2] - current_sample, :, :]

            current_sample += n_processes
    f_out.close()

    print("Done with evaluation")

if not order:
    set = 0
    plt.figure()
    plt.plot(np.abs(t_val[set]))
    plt.plot(4.5 * np.ones(len(t_val[set]), dtype=np.uint8))
    plt.title('t-Test')
    plt.xlabel("Samples")
    plt.ylabel("t-Value")
    plt.xlim([0, len(t_val[set])])
    plt.ylim([0, max(np.abs(t_val[set])+3)])
    plt.grid()


    if args.plot_only:
        plt.show()
    else:
        plt.savefig(output_file + ".png")
        print("************************")
        print("Done")
        print("************************")
