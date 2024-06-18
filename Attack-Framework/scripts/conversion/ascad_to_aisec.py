#!/usr/bin/env python3
import argparse
import h5py
import logging
import numpy as np
import os
import sqlite3 as sql
import time

_logger = logging.getLogger(__name__)


def hdf5_try_access(h5filehandle, h5item="/", attr=None, default=None):
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
    except KeyError:
        # if the item/attribute does not exist, assign a default value (e.g. None)
        value = default
        if attr is None:
            _logger.debug("Attribute %s does not exist, return default %s." % (attr, str(default)))
        else:
            _logger.debug("Dataset/group %s does not exist, return default %s." % (attr, str(default)))
    return value


def add_metadata(h5handle, trace_nr, column):

    try:
        data = np.array(h5handle[trace_nr][column], h5handle[trace_nr][column].dtype)
    except TypeError:
        # e.g. in case, h5handle = None
        data = None
    except NameError:
        data = None

    return data


def add_data(h5handle, trace_nr):

    try:
        data = np.array(h5handle[trace_nr], h5handle.dtype)
    except TypeError:
        # e.g. in case, h5handle = None
        data = None

    return data


def convert_to_uint8(trace):
    """
    converts a dataset from int16 or int8 to uint8. Datatype checks and checks whether convertion by downsamling is
    possible are performed.
    :param trace: dataset with datatype int16/int8
    :return: dataset with datatype uint8
    """
    # check if trace is int16
    if isinstance(trace[0], np.int16):
        # check if downsampling is possible
        if not np.count_nonzero((trace + 2**15) % 2**8):
            # add the offset and downsample
            trace = np.uint8((trace + 2**15) / 2**8)
        else:
            _logger.warning("Conversion from int16 to uint8 not possible!")
    elif isinstance(trace[0], np.int8):
        # add the offset
        trace = np.uint8((trace + 2**7))
    else:
        _logger.debug("Currently supported datatypes for conversion to uint8: int8, int16.")
    return trace


def main(input_db_file, out_db_filename, nr_traces_set):

    # Generate file handle
    h5filehandle = h5py.File(input_db_file, "r")

    # get the number of different measurement positions

    # Remove output file if it exists
    if os.path.isfile(out_db_filename):
        _logger.warning("File " + out_db_filename + " already exists, overwriting...")
        os.remove(out_db_filename)

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
    for i in h5filehandle:
        _logger.info("Processing trace set %s")

        samples = hdf5_try_access(h5filehandle, "/" + i + "/traces")

        timestamp = "0"  # hdf5_try_access(h5filehandle, "%.4i" % i, attr="timestamp", default=0)

        # default: convert all traces
        if nr_traces_set is None:
            nr_traces = hdf5_try_access(h5filehandle, "/" + i + "/traces")
            nr_traces = nr_traces.maxshape[0]
            _logger.info("Number of traces was not specified, all traces of set %s will be converted." % i)
            _logger.info("Number of traces to convert: %i" % nr_traces)
        else:
            nr_traces = nr_traces_set

        for j in range(nr_traces):
            _logger.info("Processing trace %i of %i." % (j + 1, nr_traces))

            # k = hdf5_try_access(, j)
            # ptxt = hdf5_try_access(h5filehandle, "/%.4i/ptxt" % i)
            # ctxt = hdf5_try_access(h5filehandle, "/%.4i/ctxt" % i)
            # iv = hdf5_try_access(h5filehandle, "/%.4i/iv" % i)
            # adata = hdf5_try_access(h5filehandle, "/%.4i/adata" % i)

            # Generate data
            header = {}
            header["trace_id"] = id
            header["timestamp"] = timestamp
            header["tile_x"] = 0
            header["tile_y"] = 0
            header["seqnr"] = id
            header["start"] = 0
            header["end"] = 0
            header["k"] = add_metadata(h5filehandle["/" + i + "/metadata"], j, 2)
            header["iv"] = None
            header["ptxt"] = add_metadata(h5filehandle["/" + i + "/metadata"], j, 0)
            header["ctxt"] = add_metadata(h5filehandle["/" + i + "/metadata"], j, 1)
            header["adata"] = add_metadata(h5filehandle["/" + i + "/metadata"], j, 3)
            # Convert and save
            trace = add_data(samples, j)
            trace = convert_to_uint8(trace)

            # Add data set
            c.execute(
                "INSERT INTO traces VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (header["trace_id"], header["timestamp"], header["tile_x"], header["tile_y"], header["seqnr"], header["start"], header["end"], header["k"], header["iv"], header["ptxt"], header["ctxt"], header["adata"], sql.Binary(bytearray(trace))),
            )

            # c.commit()
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


if __name__ == "__main__":
    # Argument parse
    parser = argparse.ArgumentParser(description="Script to convert ASCAD-HDF5 files to AISEC-db.")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="HDF5 input file (*.hdf5/*.h5)", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="SQLlite output file (default: same as input in current folder)", type=str, default=None)
    parser.add_argument("-N", "--traces", dest="nr_traces", help="Number of traces for conversion (default: None)", metavar="integer", type=int, default=None)

    args = parser.parse_args()

    # configure logger
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(format="[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s", level=loglevel)

    # if not outputfile was specified, use same filename as from input file
    if args.outputfile is None:
        args.outputfile = "./" + args.inputfile.split("/")[-1].split(".")[0] + ".db"

    _logger.info("Input file: %s", args.inputfile)
    _logger.info("Output file: %s", args.outputfile)

    # start main file
    main(args.inputfile, args.outputfile, args.nr_traces)
