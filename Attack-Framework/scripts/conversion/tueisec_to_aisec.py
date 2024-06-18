#!/usr/bin/env python3
import argparse
import h5py
import logging
import numpy as np
import os
import sqlite3 as sql
import time
import sys
from attack.helper.utils import HDF5utils as h5utils

from Crypto.Cipher import AES

_logger = logging.getLogger(__name__)


def hdf5_try_access(h5filehandle, h5item="/", attr=None, default=None, load_flag=False):
    """
    Tries to access an item (dataset/group) or attribute from an HDF5 filehandle. A default value is returned if the
    desired item or attribute does not exist
    :param h5filehandle: filehandle of h5file
    :param h5item: dataset or group, relative to root (string)
    :param attr: attribute (optional, string)
    :param default: default value. assigned if item/attribute does not exist (optional, any)
    :return: value / handle
    """

    try:
        if attr is None:
            value = h5filehandle[h5item]
        else:
            value = h5filehandle[h5item].attrs[attr]

        # if dataset is loaded, load it directly to memory
        if load_flag and attr is None:
            value = np.array(value[:], value.dtype)
    except KeyError:
        # if the item/attribute does not exist, assign a default value (e.g. None)
        value = default
        if attr is None:
            _logger.debug("Attribute %s does not exist, return default %s." % (attr, str(default)))
        else:
            _logger.debug("Dataset/group %s does not exist, return default %s." % (attr, str(default)))
    return value


def add_data(h5handle, trace_nr, repetition_nr=None, load_flag=False, start_sample=0, stop_sample=None):
    """
    Extracts the measurement with trace_nr from the HDF5 file specified by h5handle
    :param h5handle: HDF5 file handle
    :param trace_nr: number of the measurement
    :param repetition_nr: select repetition
    :param load_flag: if true, data is loaded as an numpy array
    :param start_sample: first sample that is loaded
    :param stop_sample: last sample that is loaded
    :return: data as numpy array
    """
    if load_flag:
        try:
            if repetition_nr is None:
                data = h5handle[trace_nr, start_sample:stop_sample]
            else:
                data = h5handle[trace_nr, start_sample:stop_sample, repetition_nr]
        except TypeError:
            # e.g. in case, h5handle = None
            data = None
    else:
        try:
            if repetition_nr is None:
                data = np.array(h5handle[trace_nr, start_sample:stop_sample], h5handle.dtype)
            else:
                data = np.array(h5handle[trace_nr, start_sample:stop_sample, repetition_nr], h5handle.dtype)
        except TypeError:
            # e.g. in case, h5handle = None
            data = None

    return data


def convert_keystring_to_array(keystring):
    """
    converts a string with comma separated integer values into a numpy array
    :param keystring:
    :return:
    """
    if keystring is not None:
        # make an array from the string. Comma separation is assumed.
        key_array = np.fromstring(keystring, sep=",", dtype=np.uint8)
    else:
        # pass None
        key_array = None

    return key_array


def convert(  # noqa: C901
    input_db_file,
    out_db_filename,
    nr_traces,
    nr_repetitions=None,
    conversion_to_uint8=True,
    k_label="k",
    ptxt_label="ptxt",
    ctxt_label="ctxt",
    adata_label="adata",
    iv_label="iv",
    samples_label="samples",
    load_flag=False,
    N_commit=None,
    no_group=False,
    key_string=None,
    encrypt_plaintext=False,
    start_sample=0,
    stop_sample=None,
    skip_traces=0,
):
    """
    Converts a HDF5 file with the structure of the TUEISEC attack framework to a sqllite database in the AISEC data
    format. The number of traces for conversion can be set as well as automatic conversion to uint8.
    :param input_db_file: input file path to a valid HDF5 file
    :param out_db_filename: output file path for the sqlite database
    :param nr_traces: number of traces, only the first nr_traces are converted
    :param conversion_to_uint8: Flag whether conversion to uint8 is carried out
    :return:
    """

    # Generate file handle
    h5filehandle = h5py.File(input_db_file, "r")

    if no_group:
        measurement_shape = hdf5_try_access(h5filehandle, "/%s" % samples_label).shape
    else:
        # get the shape of the first groups dataset
        measurement_shape = hdf5_try_access(h5filehandle, "/0000/%s" % samples_label).shape

    # default: convert all traces
    if nr_traces is None:
        nr_traces = measurement_shape[0]
        _logger.info("Number of traces was not specified, all traces will be converted.")
        _logger.info("Number of traces per position to convert: %i" % nr_traces)
    elif nr_traces > measurement_shape[0]:
        _logger.info("Number of traces higher than the maximum available number of traces.")
        _logger.info("Converting available traces: %i" % nr_traces)

    # default: convert all samples
    if stop_sample is None:
        stop_sample = measurement_shape[1]
        _logger.info("Last sample was not specified, all up to the last sample will be converted.")
    elif stop_sample > measurement_shape[1]:
        stop_sample = measurement_shape[1]
        _logger.info("Last sample specified was more than available samples," " all up to the last sample will be converted.")

    if start_sample > stop_sample:
        _logger.error("First sample was specified bigger than last sample.")
        sys.exit(0)

    # default: convert all repetitions
    if nr_repetitions is None:
        if no_group:
            nr_repetitions = 1
        else:
            nr_repetitions = measurement_shape[2]
        _logger.info("Number of repetitions was not specified, all repetitions will be converted.")
        _logger.info("Number of repetitions per position to convert: %i" % nr_repetitions)
    elif nr_repetitions > measurement_shape[2]:
        _logger.info("Number of repetituins higher than the maximum available number of traces.")
        _logger.info("Converting available traces: %i" % nr_repetitions)

    # get the number of different measurement positions
    if no_group:
        nr_positions = 1
    else:
        # check how many groups with a four digit name exist, which are the measurement positions
        # this way __documentation__, etc. are excluded from conversion
        positions = h5utils.hdf5_get_positions(h5filehandle=h5filehandle)
        nr_positions = len(positions)
        if nr_positions > 1:
            # convert the measurement positions into tiles.
            # Tile numbering is following same meander pattern as used for measurement (e.g. starting in the lower left corner of the grid)
            x_pos, y_pos = h5utils.hdf5_get_xy_values(h5filehandle=h5filehandle, positions=positions)
            tile_x, tile_y = h5utils.hdf5_convert_xy_to_tiles(x=x_pos, y=y_pos)
        else:
            # default: only a single measurement position, i.e. tile (0,0)
            tile_x = np.array([0], dtype=int)
            tile_y = np.array([0], dtype=int)

    # Remove output file if it exists
    if os.path.isfile(out_db_filename):
        _logger.warning("File " + out_db_filename + " already exists, overwriting...")
        os.remove(out_db_filename)

    # convert key string into array
    key_array = convert_keystring_to_array(key_string)

    _logger.info("Start conversion...")
    start_time = time.time()

    # create new db
    c = sql.connect(out_db_filename)
    c.execute(
        """CREATE TABLE traces (
        trace_id     INTEGER PRIMARY KEY NOT NULL,
        timestamp  INTEGER (4) DEFAULT (strftime('%s', 'now') ) NOT NULL,
        tile_x          INTEGER,
        tile_y          INTEGER,
        seqnr         INTEGER,
        start           INTEGER,
        end            INTEGER,
        k                BLOB,
        iv               BLOB,
        ptxt            BLOB,
        ctxt            BLOB,
        adata        BLOB,
        samples    BLOB
        );"""
    )
    c.commit()
    _logger.info("Created database.")

    # add traces indo db
    id = 1
    commit_counter = 0
    for i in range(nr_positions):
        if no_group:
            group_string = ""
        else:
            group_string = "%.4i" % i

        _logger.info("Processing position %i of %i." % (i + 1, nr_positions))
        k = hdf5_try_access(h5filehandle, group_string + "/%s" % (k_label), load_flag=load_flag)
        ptxt = hdf5_try_access(h5filehandle, group_string + "/%s" % (ptxt_label), load_flag=load_flag)
        ctxt = hdf5_try_access(h5filehandle, group_string + "/%s" % (ctxt_label), load_flag=load_flag)
        iv = hdf5_try_access(h5filehandle, group_string + "/%s" % (iv_label), load_flag=load_flag)
        adata = hdf5_try_access(h5filehandle, group_string + "/%s" % (adata_label), load_flag=load_flag)
        samples = hdf5_try_access(h5filehandle, group_string + "/%s" % (samples_label), load_flag=load_flag)
        # Generate timestamp
        timestamp = hdf5_try_access(h5filehandle, "%.4i" % i, attr="timestamp", default=0)

        for j in range(skip_traces, nr_traces):
            _logger.info("Processing trace %i of %i." % (j + 1 - skip_traces, nr_traces - skip_traces))
            for ldx in range(nr_repetitions):
                _logger.debug("Processing repetition %i of %i." % (ldx + 1, nr_repetitions))
                # Generate data
                header = {}
                header["trace_id"] = id
                header["timestamp"] = timestamp
                header["tile_x"] = int(tile_x[i])
                header["tile_y"] = int(tile_y[i])
                header["seqnr"] = ldx
                header["start"] = 0
                header["end"] = 0
                if key_array is None:
                    header["k"] = add_data(k, j, load_flag=load_flag)
                else:
                    header["k"] = key_array
                header["iv"] = add_data(iv, j, load_flag=load_flag)
                header["ptxt"] = add_data(ptxt, j, load_flag=load_flag)

                if encrypt_plaintext:
                    cipher = AES.new(key=bytes(header["k"]), mode=AES.MODE_ECB)
                    header["ctxt"] = np.array(list(cipher.encrypt(bytes(header["ptxt"]))), dtype=np.uint8)
                else:
                    header["ctxt"] = add_data(ctxt, j, load_flag=load_flag)
                header["adata"] = add_data(adata, j, load_flag=load_flag)
                if no_group:
                    trace = add_data(samples, trace_nr=j, repetition_nr=None, load_flag=load_flag, start_sample=start_sample, stop_sample=stop_sample)
                else:
                    trace = add_data(samples, trace_nr=j, repetition_nr=ldx, load_flag=load_flag, start_sample=start_sample, stop_sample=stop_sample)
                if conversion_to_uint8 and trace.dtype != np.uint8:
                    trace = h5utils.convert_to_uint8(trace=trace)

                # Add data set
                c.execute(
                    "INSERT INTO traces VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    (header["trace_id"], header["timestamp"], header["tile_x"], header["tile_y"], header["seqnr"], header["start"], header["end"], header["k"], header["iv"], header["ptxt"], header["ctxt"], header["adata"], sql.Binary(bytearray(trace))),
                )

                if commit_counter == N_commit:
                    c.commit()
                    commit_counter = 0
                else:
                    # increase commit counter
                    commit_counter = commit_counter + 1

                # increase ID counter
                id = id + 1

    c.commit()
    c.close()

    end_time = time.time()
    time_elapsed = end_time - start_time
    _logger.info("Conversion finished...")
    _logger.info("Time elapsed: %.1f seconds (about %.2f hours) for %i measurements" % (time_elapsed, time_elapsed / 3600, id))
    _logger.info("Throughput: %.2f measurements/second." % (id / time_elapsed))

    return


def main():
    # Argument parse
    parser = argparse.ArgumentParser(description="Script to convert TUEISEC-HDF5 files to AISEC-db.")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="HDF5 input file (*.hdf5/*.h5)", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="SQLlite output file (default: same as input in current folder with *.db extension)", type=str, default=None)
    parser.add_argument("-N", "--no-of-traces", dest="nr_traces", help="Number of traces for conversion (default: all traces available)", metavar="integer", type=int, default=None)
    parser.add_argument("-R", "--repetitions", dest="nr_repetitions", help="Number of repetitions for conversion (default: all repetitions available)", metavar="integer", type=int, default=None)
    parser.add_argument("--start-sample", dest="start_sample", help="Select the first sample to reduce the size of the " "output database. (default: all samples are used)", metavar="integer", type=int, default=0)
    parser.add_argument("--stop-sample", dest="stop_sample", help="Select the last sample to reduce the size of the " "output database. (default: all samples are used)", metavar="integer", type=int, default=None)
    parser.add_argument("--conversion_to_uint8", dest="conversion_to_uint8", help="Convert traces to uint8 if possible (default: True)", action="store_false", default=True)
    parser.add_argument("-s", "--samples", dest="samples_label", help="Name of the dataset that is stored to 'samples' in the AISEC format (default: 'samples')", metavar="string", type=str, default="samples")
    parser.add_argument("-k", dest="k_label", help="Name of the dataset that is stored to 'k' in the AISEC format (default: 'k')", metavar="string", type=str, default="k")
    parser.add_argument("-p", "--ptxt", dest="ptxt_label", help="Name of the dataset that is stored to 'ptxt' in the AISEC format (default: 'ptxt')", metavar="string", type=str, default="ptxt")
    parser.add_argument("-c", "--ctxt", dest="ctxt_label", help="Name of the dataset that is stored to 'ctxt' in the AISEC format (default: 'ctxt')", metavar="string", type=str, default="ctxt")
    parser.add_argument("-a", "--adata", dest="adata_label", help="Name of the dataset that is stored to 'adata' in the AISEC format (default: 'adata')", metavar="string", type=str, default="adata")
    parser.add_argument("-I", "--iv", dest="iv_label", help="Name of the dataset that is stored to 'iv' in the AISEC format (default: 'iv')", metavar="string", type=str, default="iv")
    parser.add_argument("--load-to-memory", dest="load_flag", help="Load the entire HDF5 datasets to RAM (default: False)", action="store_true", default=False)
    parser.add_argument("--N_commit", dest="N_commit", help="Number of traces after which data is committed to database (default: after all traces)", metavar="integer", type=int, default=None)
    parser.add_argument("--no_group", dest="no_group", help="Assume there are no groups, but all data resides directly under '/'. [For legacy reasons] " "(default: False)", action="store_true", default=False)
    parser.add_argument(
        "--set_key",
        dest="key_string",
        help="Set the key to a fixed value, e.g., if not contained in "
        "the hdf5. A string with comma separated integer values is "
        "expected, which represent one byte each. Example: "
        "70,114,101,101,32,98,101,101,114,32,52,32,97,108,108,33. "
        "[For legacy reasons] (Default: values from HDF5 file are"
        "used.)",
        metavar="string",
        type=str,
        default=None,
    )
    parser.add_argument("--encrypt_plaintext", dest="encrypt_plaintext", help="Encrypt the AES-128 plaintext to get the ciphertext, e.g., if no ciphtext was stored. " "(default: False)", action="store_true", default=False)
    parser.add_argument("--skip-traces", dest="skip_traces", help="Skip the first traces for conversion (default: 0)", metavar="integer", type=int, default=0)
    args = parser.parse_args()

    # configure logger
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(format="[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s", level=loglevel)

    # if not outputfile was specified, use same filename as from input file
    if args.outputfile is None:
        args.outputfile = ".".join(args.inputfile.split(".")[:-1]) + ".db"

    # increase the index of the last sample in order to also include it
    if args.stop_sample is not None:
        args.stop_sample = args.stop_sample + 1

    _logger.info("Input file: %s", args.inputfile)
    _logger.info("Output file: %s", args.outputfile)
    _logger.info("Conversion from int16 to int8: %s", str(args.conversion_to_uint8))

    # start conversion
    convert(
        input_db_file=args.inputfile,
        out_db_filename=args.outputfile,
        nr_traces=args.nr_traces,
        nr_repetitions=args.nr_repetitions,
        conversion_to_uint8=args.conversion_to_uint8,
        k_label=args.k_label,
        ptxt_label=args.ptxt_label,
        ctxt_label=args.ctxt_label,
        adata_label=args.adata_label,
        iv_label=args.iv_label,
        samples_label=args.samples_label,
        load_flag=args.load_flag,
        N_commit=args.N_commit,
        no_group=args.no_group,
        key_string=args.key_string,
        encrypt_plaintext=args.encrypt_plaintext,
        start_sample=args.start_sample,
        stop_sample=args.stop_sample,
        skip_traces=args.skip_traces,
    )


# run program
if __name__ == "__main__":
    main()
