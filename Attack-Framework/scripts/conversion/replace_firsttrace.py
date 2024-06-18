#!/usr/bin/env python3
import sqlite3 as sql
import logging
import argparse

_logger = logging.getLogger(__name__)


def main(input_db_file, out_db_filename):

    # connect to the reference database
    db_ref = sql.connect(input_db_file)
    # create a cursor
    cursor_ref = db_ref.cursor()
    try:
        # retrieve the samples of the first trace and close database
        cursor_ref.execute("""SELECT samples FROM traces WHERE trace_id=1""")
    except sql.OperationalError as except_message:
        _logger.error("Something went wrong.")
        _logger.error(except_message)
        exit()

    trace_ref = cursor_ref.fetchone()
    db_ref.close()

    _logger.info("Reference trace was read.")

    # connect to the output database
    db_out = sql.connect(out_db_filename)

    cursor_out = db_out.cursor()
    cursor_out.execute("""UPDATE traces SET samples = ? WHERE trace_id=1""", (trace_ref))

    _logger.info("Reference trace was written to first trace of output database.")
    db_out.commit()

    db_out.close()

    return


if __name__ == "__main__":
    # Argument parse
    parser = argparse.ArgumentParser(description="Script to replace the first trace in a AISEC-db with the first trace" "of another database. (Useful if alignment of profiling and attack set" "need to done).")
    parser.add_argument("-v", "--verbose", help="Display debug log messages", action="store_true")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="Input file (*.db)", type=str, required=True)
    parser.add_argument("-o", "--outputfile", dest="outputfile", metavar="filename", help="Output file (*.db)", type=str, required=True)

    args = parser.parse_args()

    # configure logger
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(format="[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s", level=loglevel)

    _logger.info("Input file: %s", args.inputfile)
    _logger.info("Output file: %s", args.outputfile)

    # start main file
    main(args.inputfile, args.outputfile)
    _logger.info("Done.")
