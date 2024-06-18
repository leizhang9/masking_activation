#!/usr/bin/env python3
import argparse
from attack.helper.utils import HDF5utils as HDF5_utils
import logging

_logger = logging.getLogger(__name__)


def main():
    # Argument parse
    parser = argparse.ArgumentParser(description="Restore documentation from a HDF5.")
    parser.add_argument("-i", "--inputfile", dest="inputfile", metavar="filename", help="HDF5 file with time domain measurements.", type=str, required=True)
    parser.add_argument("-o", "--outputfolder", dest="outputfolder", metavar="folder", help="Folder for documentation files.", type=str, default=".")

    args = parser.parse_args()
    logging.basicConfig(format="[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s", level=logging.INFO)

    _logger.info("Files from %s will be restored to %s" % (args.inputfile, args.outputfolder))

    HDF5_utils.hdf5_recover_documentation(h5file=args.inputfile, folder=args.outputfolder)
    _logger.info("Documentation restored.")


# run program
if __name__ == "__main__":
    main()
