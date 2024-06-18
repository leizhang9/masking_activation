import datetime
import h5py
import logging
import numpy as np
from scipy import signal
import os
import sys
import time
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
import subprocess
import shlex
import re

_logger = logging.getLogger(__name__)


class JSONutils:
    """
    Utilities for handling JSON files (configuration files for the TUEISEC-Attack-Framework)
    """

    @staticmethod
    def json_try_access(jsonobject, jsonitem=[], default=None):
        """
        Tries to access an item a JSON object. A default value is returned if the desired value does not exist. This is
        particularly useful if new attributes are introduced in the config file. In such cases, a legacy default can be
        assigned.
        :param jsonobject:
        :param jsonitem: a list that specifies the hierarchy to the desired value, e.g. ['HDF5', 'datasets', 'samples']
        :param default: default value. assigned if item/attribute does not exist (optional)
        :return: value
        """

        try:
            value = jsonobject
            for i in jsonitem:
                value = value[i]
        except KeyError:
            # if the item does not exist, assign a default value (e.g. None)
            value = default
            _logger.warning("Item %s does not exist, return default %s." % (jsonitem, default))
        return value


class DATAutils:
    """
    Utilities for handling data, e.g. conversion of traces, etc.
    """

    @staticmethod
    def convert_int16toint8(trace):
        """
        converts a dataset from int16 to int8. Datatype is checked as well as whether downsampling the resolution is
        possible without loosing information.
        :param trace: an array with a trace
        :return: the converted trace
        """
        # check if trace is int16
        if trace.dtype == np.int16:
            # check if downsampling is possible
            if not np.count_nonzero(trace % 2**8):
                trace = np.int8(trace // 2**8)
            else:
                _logger.warning("Conversion from int16 to int8 not possible!")
        else:
            _logger.debug("Trace is not of datatype int16...")

        return trace

    @staticmethod
    def convert_to_uint8(trace):
        """
        converts a dataset from int16 or int8 to uint8. Datatype checks and checks whether conversion by downsampling is
        possible are performed.
        :param trace: dataset with datatype int16/int8
        :return: dataset with datatype uint8
        """
        # check if trace is int16
        if trace.dtype == np.int16:
            # check if downsampling is possible
            if not np.count_nonzero((trace + 2**15) % 2**8):
                # downsample and add the offset (all calculations done as int16)
                trace = np.uint8((trace // 2**8) + 2**7)
            else:
                _logger.warning("Conversion from int16 to uint8 not possible!")
        elif trace.dtype == np.int8:
            # add the offset
            trace = np.uint8((trace + 2**7))
        else:
            _logger.debug("Currently supported datatypes for conversion to uint8: int8, int16.")
        return trace


class HDF5utils:
    """
    Utilities for handling HDF5 files. The functions essentially create a HDF5 file and allow to add attributes and
    groups
    """

    @staticmethod  # noqa: C901
    def hdf5_file_init(configfile, target_info="", target_module_path="", trace_measurement_version="", configfile_path=""):
        """
        Initializes HDF5 file
        :param configfile: dictionary created from the configuration file (c.f. config_template for entries)
        :param target_info: A string with information about the target chip (e.g. Artix-7)
        :param target_module_path: path to the target module that is used in order to store the file
        :param configfile_path: path to the config file that is used in order to store file
        :param trace_measurement_version: version of the trace_measurement script
        :return: file handle of the HDF5 containing attributes and documentation
        """

        o_file = configfile["HDF5"]["output_file"]

        # generate a time stamp to append it to the file name
        datestring = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        o_file = HDF5utils.hdf5_create_output_filename(o_file=o_file, add_datestring=JSONutils.json_try_access(configfile, ["HDF5", "output_file_addtimestring"], default=False), datestring=datestring)

        # Abort if file already exists (to avoid unintentional data loss)
        if os.path.isfile(o_file):
            _logger.warning("File " + o_file + " already exists, aborting...")
            sys.exit(0)

        # Generate file
        h5filehandle = h5py.File(o_file, "x")
        _logger.info("File %s is created." % o_file)

        HDF5utils.hdf5_add_attributes(h5filehandle=h5filehandle, configfile=configfile, entry="target", add_entry_name=False)
        # get chip name from the device
        h5filehandle.attrs["chip"] = target_info
        h5filehandle.attrs["time stamp"] = datestring

        # store documentation (picture of setup, binary file, etc.)
        HDF5utils.hdf5_create_documentation(h5filehandle=h5filehandle, configfile=configfile, target_module_path=target_module_path, configfile_path=configfile_path, trace_measurement_version=trace_measurement_version)

        # Add attributes
        HDF5utils.hdf5_add_attributes(h5filehandle=h5filehandle, configfile=configfile, entry="msmt", add_entry_name=False)
        HDF5utils.hdf5_add_attributes(h5filehandle=h5filehandle, configfile=configfile, entry="table", add_entry_name=True)
        HDF5utils.hdf5_add_attributes(h5filehandle=h5filehandle, configfile=configfile, entry="experiment", add_entry_name=True)
        return h5filehandle

    @staticmethod
    def hdf5_create_output_filename(o_file, datestring=None, add_datestring=False):
        """
        Checks whether provided file name is valid and adds a datestring optionally.
        :param o_file: filename supposed to be used for the HDF5
        :param datestring: a string with date, hour, etc.
        :param add_datestring: a flag, upon which the datestring is appended to the filename
        :return o_file: output file name (possible modified to the input version)
        """

        # extract the file name, the extension and the path
        file_name, file_extension = os.path.splitext(os.path.basename(o_file))
        file_path, _ = os.path.split(os.path.realpath(o_file))

        if file_extension == "" or file_name == "":
            _logger.error("Please provide a valid filename with an extension!")
            sys.exit(0)

        if file_path == "/":
            # in case the root folder is the desired location, empty the string as a '/' is added later
            file_path = ""
            _logger.warning("You try to save your measurements under '/' - are you sure you want this?!")

        # delete datestring if not required
        if not add_datestring or datestring is None:
            datestring = ""
        else:
            datestring = "_" + datestring

        # Compose the final file name
        o_file = file_path + "/" + file_name + datestring + file_extension

        return o_file

    @staticmethod
    def hdf5_create_documentation(h5filehandle, configfile, target_module_path, configfile_path, trace_measurement_version):
        """
        Creates the documentation
        :param h5filehandle: hdf5 filehandle
        :param configfile: dictionary created from the configuration file (c.f. config_template for entries)
        :param target_module_path: path to the target module that is used in order to store the file
        :param configfile_path: path to the config file that is used in order to store file
        :param trace_measurement_version: version of the trace_measurement script
        :param attack_version: version of the attack tool that is used
        :return:
        """
        # store documentation (picture of setup, binary file, etc.)
        docgroup = h5filehandle.create_group("__documentation__")
        docgroup.attrs["trace_measurement version"] = trace_measurement_version
        HDF5utils.hdf5_store_attackversion(docgroup)
        HDF5utils.hdf5_store_git(h5handle=docgroup)

        # add target module
        if os.path.isfile(target_module_path):
            HDF5utils.hdf5_store_binary(h5filehandle=docgroup, dataset_name=os.path.split(target_module_path)[1], binaryfile=target_module_path)

        # add config file
        if os.path.isfile(configfile_path):
            HDF5utils.hdf5_store_binary(h5filehandle=docgroup, dataset_name=os.path.split(configfile_path)[1], binaryfile=configfile_path)

        # storing binary as dataset
        binaryfile = JSONutils.json_try_access(configfile, ["target", "binary"], default=None)
        if not (binaryfile is None):
            # if binary was specified, store into HDF5. Use filename w/o path as name for dataset
            HDF5utils.hdf5_store_binary(h5filehandle=docgroup, dataset_name=os.path.split(binaryfile)[1], binaryfile=binaryfile)

        # store information on python environment
        docgroup = HDF5utils.hdf5_store_pythonenvironment(h5handle=docgroup, dataset_name="requirements.txt")

        # if documentation entry exist, store files
        if JSONutils.json_try_access(configfile, ["HDF5", "documentation"], default=None) is not None:
            # store further files
            for attributes in configfile["HDF5"]["documentation"]:
                # check for all entries whether a file is given that exists
                if os.path.isfile(configfile["HDF5"]["documentation"][attributes]):
                    # store the file as a void data set (binary data)
                    HDF5utils.hdf5_store_binary(h5filehandle=docgroup, dataset_name=attributes, binaryfile=configfile["HDF5"]["documentation"][attributes])
        else:
            _logger.warning("No key 'HDF5: documentation' exists!")

        return

    @staticmethod
    def hdf5_add_attributes(h5filehandle, configfile, entry, add_entry_name=True):
        """
        Adds attributes from a dictionary to a hdf5 handle.
        :param h5filehandle: hdf5 filehandle
        :param configfile: dictionary created from the configuration file (c.f. config_template for entries)
        :param entry: name of the group from the configfile dictionary whose subentries are added as attributes
        :param add_entry_name: flag to add the entry name to the attribute
        :return:
        """

        try:
            for attributes in configfile[entry]:
                if add_entry_name:
                    h5filehandle.attrs["%s - " % entry + attributes] = configfile[entry][attributes]
                else:
                    h5filehandle.attrs[attributes] = configfile[entry][attributes]
            _logger.info("Adding keys '%s'..." % entry)
        except KeyError:
            _logger.warning("No key '%s' exists!" % entry)
        return

    @staticmethod
    def hdf5_add_group(h5filehandle, configfile, N_traces, noSamples, group=0, N_repetitions=1, x=None, y=None, z=None):
        """
        Adds a measurement group (i.e. per measurement position) with respective datasets
        :param h5filehandle
        :param configfile:
        :param N_traces:
        :param group:
        :param N_repetitions:
        :param x: x coordinate in mm (default: None if no table is used)
        :param y: y coordinate in mm (default: None if no table is used)
        :param z: z coordinate in mm (default: None if no table is used)
        :return: h5group
        :return: num_datasets: list with channel and dataset string
        """
        # add group for first measurement position (default: only one position)
        h5group = h5filehandle.create_group("%.4i" % group)

        # add coordinates
        if (x is not None) and (y is not None):
            h5group.attrs["x position [mm]"] = x
            h5group.attrs["y position [mm]"] = y

        if z is not None:
            h5group.attrs["z position [mm]"] = z

        # number of datasets to store
        diff_datasets = list()

        # generate datasets for each of the specified datasets from the configfile
        for datasets in configfile["HDF5"]["datasets"]:

            if configfile["HDF5"]["datasets"][datasets]["create"]:
                dataset_dim = configfile["HDF5"]["datasets"][datasets]["dim"]
                add_attributes = False
                if dataset_dim is None:
                    # only for samples, the dimension is not specified: in this case, use the number of samples as dimension
                    dataset_dim = noSamples
                    # third dimension: number of repetitions
                    repetition_dim = N_repetitions
                    # add attributes of channel, trigger, etc.
                    add_attributes = True
                else:
                    # get the dimension of the desired data set
                    dataset_dim = configfile["HDF5"]["datasets"][datasets]["dim"]

                    if JSONutils.json_try_access(configfile, ["HDF5", "store_for_all_repetitions"], default=False):
                        # third dimension: number of repetitions
                        repetition_dim = N_repetitions
                    else:
                        # repetitions are supposed to have the same input, output and secret data, i.e. redundant data
                        # does not need to be stored
                        repetition_dim = 1
                    # do not add attributes of channel, trigger, etc.
                    add_attributes = False

                # generate dataset with specified name, dimension (iterations x dim) and datatype
                dset = h5group.create_dataset(datasets, (N_traces, dataset_dim, repetition_dim), dtype=configfile["HDF5"]["datasets"][datasets]["datatype"])

                if add_attributes:
                    # add all channel attributes
                    channel_nr = JSONutils.json_try_access(configfile, ["HDF5", "datasets", datasets, "record channel"], default=1)
                    for attributes in configfile["scope"]["channel%i" % channel_nr]:
                        dset.attrs[("channel%i: " % channel_nr) + attributes] = configfile["scope"]["channel%i" % channel_nr][attributes]

                    # add all trigger attributes
                    for attributes in configfile["scope"]["trigger"]:
                        dset.attrs["trigger: " + attributes] = configfile["scope"]["trigger"][attributes]

                    # add all sampling attributes
                    for attributes in configfile["scope"]["sampling"]:
                        dset.attrs[attributes] = configfile["scope"]["sampling"][attributes]

                    # save information about the scope
                    dset.attrs["scope: type"] = JSONutils.json_try_access(configfile, ["scope", "type"], default="")
                    dset.attrs["scope: url"] = JSONutils.json_try_access(configfile, ["scope", "url"], default="")

                    diff_datasets.append([channel_nr, datasets])
        # Add timestamp of the entire group (mainly for AISEC-format)
        h5group.attrs["timestamp"] = time.strftime("%s")
        return h5filehandle, diff_datasets

    @staticmethod
    def hdf5_add_data(h5filehandle, dataset_name, data, trace_number, group=0, repetition_number=0):
        """
        Adds an data set to the dataset of the HDF5 filehandle specified
        :param h5filehandle: hdf5 filehandle
        :param dataset_name: name of the dataset to which data shall be added
        :param data: data
        :param trace_number: index of the trace
        :param group: acquisition group (more relevant if table is used)
        :param repetition_number: index of the repeated measurement with same input data
        :return:
        """
        if not isinstance(data, list):
            if len(data.shape) > 1:
                if data.shape[1] == 1:
                    data = data[:, 0]
        h5filehandle["%.4i" % group][dataset_name][trace_number, :, repetition_number] = data
        return h5filehandle

    @staticmethod
    def hdf5_add_data_multitrace(h5filehandle, dataset_name, data, trace_indices=[0, None], group=0, repetition_indices=[0, None]):
        """
        Adds data from multiple traces (i.e. more than one dimension) to the dataset of the HDF5 filehandle specified
        :param h5filehandle: hdf5 filehandle
        :param dataset_name: name of the dataset to which data shall be added
        :param data: data
        :param trace_indices: first and last index in the dataset, where data shall be added
        :param group: acquisition group (more relevant if table is used)
        :param repetition_indices: first and last index in the dataset, where data shall be added
        :return:
        """
        if not isinstance(data, list):
            if len(data.shape) > 1:
                if data.shape[1] == 1:
                    data = data[:, 0]

        h5filehandle["%.4i" % group][dataset_name][trace_indices[0] : trace_indices[1], :, repetition_indices[0] : repetition_indices[1]] = data
        return h5filehandle

    @staticmethod
    def hdf5_file_close(h5filehandle):
        """
        Close HDF5 file
        :param h5filehandle:
        :return:
        """
        try:
            h5filehandle.close()
            _logger.info("HDF5 file was successfully closed.")
        except BaseException:
            _logger.warning("HDF5 file was not appropriately closed.")

        return h5filehandle

    @staticmethod
    def hdf5_store_binary(h5filehandle, dataset_name, binaryfile):
        """
        Stores the binary data of a file (e.g. bit stream, hex file) to a data set, such that it can be retreived
        lateron to reprodruce the experiment.
        :param h5filehandle: hdf5 filehandle
        :param dataset_name: name of the dataset that shall be created
        :param binaryfile: path of the binary file
        """

        # inspired by: https://blade6570.github.io/soumyatripathy/hdf5_blog.html
        try:
            # load the specified file as binary data
            with open(binaryfile, mode="rb") as file:  # b is important -> binary
                fileContent = file.read()

            # convert binary to numpy array
            fileContent_binary = np.asarray(fileContent)

            # create a new dataset with the binary blob
            dset = h5filehandle.create_dataset(dataset_name, data=fileContent_binary)
            # store original file path (just because we can - should be obvious from HDF5 file anyway,)
            dset.attrs["Original file path"] = binaryfile
        except BaseException:
            _logger.warning("Something went wrong when trying to store the binary file %s." % binaryfile)

        return h5filehandle

    @staticmethod
    def hdf5_recover_binary(h5filehandle, dataset_name, binary_recover="."):
        """
        Recovers the binary data of a file (e.g. bit stream, hex file) stored in an HDF5 data set and stores it to the
        filename specified
        :param h5filehandle: hdf5 filehandle
        :param dataset_name: name of the dataset that shall be recovered
        :param binary_recover: path or directory for recovery. If directory is given, 'dataset_name' is used as filename
        """

        # Abort if file already exists (to avoid unintentional data loss)
        if os.path.isfile(binary_recover):
            _logger.warning("File " + binary_recover + " already exists, recovery of binary file skipped...")
            return h5filehandle

        filedir, filename = os.path.splitext(binary_recover)

        # make directory if is does not exist
        if not os.path.isdir(filedir):
            os.mkdir(filedir)

        # use data set name if a directory is specified
        if filename == "":
            # append data set name to path
            binary_recover = os.path.abspath(binary_recover) + "/" + dataset_name

        # load binary blob and convert to bytes again
        data = np.array(h5filehandle[dataset_name])
        binary_content = bytes(data)

        with open(binary_recover, mode="wb") as file:  # b is important -> binary
            file.write(binary_content)

        return h5filehandle

    @staticmethod
    def hdf5_store_pythonenvironment(h5handle, dataset_name="requirements.txt"):
        """
        Stores the installed python packages as well as the python version that was used.
        :param h5handle: hdf5 handle, from either root or a group
        :param dataset_name: name of the dataset in which the requirements of the python environment are stored.
        :return: h5handle: for further use the handle is returned.
        """

        try:
            # storing installed packages from pip
            s = subprocess.check_output(["pip", "freeze"])
            # create a new dataset with the binary blob
            dset = h5handle.create_dataset(dataset_name, data=np.asarray(s))
            s = subprocess.check_output(["python", "--version"])
            # get python version (decode for conversion of byte to string, rstrip to remove line break)
            dset.attrs["python version"] = s.decode().rstrip()
        except BaseException:
            _logger.warning("Something went wrong when trying to store python environment.")

        return h5handle

    @staticmethod
    def hdf5_store_attackversion(h5handle):
        """
        Store the version of the attack framework
        :param h5handle: hdf5 handle
        :return:
        """
        try:
            # use pip show: the second line of the output is the Version
            h5handle.attrs["attack-framework version"] = MISCutils.subprocess_output("pip show attack").split("\n")[1].split()[1]
        except BaseException as e:
            _logger.warning("Accessing Attack-Framework version fails: %s" % e)
        return

    @staticmethod
    def hdf5_store_git(h5handle):
        """
        Adds information about the git used
        :param h5handle: hdf5 handle
        :return:
        """

        try:
            # get the current commit
            h5handle.attrs["git - commit hash"] = MISCutils.subprocess_output("git rev-parse HEAD")
            h5handle.attrs["git - commit #"] = MISCutils.subprocess_output("git rev-list --count HEAD")
            h5handle.attrs["git - branch"] = MISCutils.subprocess_output("git rev-parse --abbrev-ref HEAD")
            # get the basename of the git (to avoid confusion in case you are calling the script, and have a different git repo open):
            h5handle.attrs["git - which"] = MISCutils.subprocess_output("git rev-parse --show-toplevel")
            # get the remote URL of origin (basically to check in which git you are living, e.g. if a fork exists)
            h5handle.attrs["git - URL (origin)"] = MISCutils.subprocess_output("git remote get-url origin")
        except Exception as e:
            _logger.warning("Could not access a git:")
            _logger.warning(e)
        return

    @staticmethod
    def hdf5_recover_documentation(h5file, folder="."):
        """
        Recovers the documentory data from a HDF5 file into the specified folder
        :param h5file: hdf5 file name (not a handle!)
        :param folder: directory for recovery.
        """
        # load the HDF5 file
        h5filehandle = h5py.File(h5file, "r")

        # check whether documentation exists
        try:
            docgroup = h5filehandle["__documentation__"]
        except KeyError:
            _logger.error("No documentation available.")
            return

        # if documentation exist recover all entries
        for keys in docgroup.keys():
            HDF5utils.hdf5_recover_binary(h5filehandle=docgroup, dataset_name=keys, binary_recover=folder)
        return

    @staticmethod
    def copy_attributes(handle, handle_out):
        """
        Copies all attributes 1:1 from a handle (file/group/dataset) to a new handle
        :param handle: HDF5 handle with the original attributes
        :param handle_out:n HDF5 handle to which the attributes shall be copied
        :return:
        """
        for name, value in handle.attrs.items():
            handle_out.attrs[name] = value

    @staticmethod
    def copy_dataset(handle, handle_out, dset_name, trace_select=None, repetititon_select=None, dtype=None, copy_doc=False):
        """
        Copies a dataset, where the number of traces (rows of the dataset) can be selected, and the datatype can be
        adapted. Adaption of the datatype maybe beneficial if raw measurement data (uint8) is processed, e.g., by
        averaging or filtering and thus converted (e.g. float).
        WARNING: only repetitions or traces can be selected!
        :param handle: handle that contains the original dataset
        :param handle_out: handle to which the dataset shall be copied
        :param dset_name: name of the dataset
        :param trace_select: array with indices of traces that shall be copied
        :param repetititon_select: array with indices of repetitions that shall be copied
        :param dtype: optional: new datatype of the copied dataset
        :return:
        """
        if copy_doc:
            handle_out.create_dataset(dset_name, data=handle)
        else:
            if trace_select is None:
                trace_select = np.arange(0, handle.shape[0])

            if repetititon_select is None:
                repetititon_select = np.arange(0, handle.shape[2])

            # create dataset
            if dtype is None:
                handle_out.create_dataset(dset_name, shape=(len(trace_select), handle.shape[1], len(repetititon_select)), dtype=handle.dtype)
            else:
                handle_out.create_dataset(dset_name, shape=(len(trace_select), handle.shape[1], len(repetititon_select)), dtype=dtype)
            # copy dataset (currently only one array can be used for selection: do it one after another)
            tmp = handle[trace_select, :, :]
            handle_out[dset_name][:] = tmp[:, :, repetititon_select]

    @staticmethod
    def create_filecopy(handle, handle_out, trace_select=None, repetition_select=None, conversion=[[None, None]]):
        """
        Create a copy of an HDF5 file containing
        :param handle: handle of the original HDF5 file
        :param handle_out: handle of the HDF5 file to which shall be copied
        :param trace_select: array with indices of that shall be copied
        :param repetition_select: array with indices of that shall be copied
        :param conversion: list with [<datasetname>,<desired data type>] lists
        :return:
        """

        HDF5utils.copy_attributes(handle, handle_out)

        conversion_datasets = [item[0] for item in conversion]
        # iterate over all groups
        for keys in handle.keys():
            if keys == "__documentation__":
                is_doc_group = True
            else:
                is_doc_group = False
            # create group
            handle_out.create_group(keys)
            # copy attributes of group
            HDF5utils.copy_attributes(handle[keys], handle_out[keys])
            # iterate over all datasets
            for dsets in handle[keys].keys():

                if dsets in conversion_datasets:
                    # if dataset is in the list of datasets that shall be converted to a different datatype,
                    # retrieve the desired datatype

                    # find the list
                    set_idx = [i for i, x in enumerate(conversion_datasets) if x == dsets]
                    # retrieve desired datatype
                    chosen_dtype = conversion[set_idx[0]][1]
                else:
                    # if no datatype is given, the created dataset has the same datatype as the original one.
                    chosen_dtype = None

                # copy data set and attributes
                HDF5utils.copy_dataset(handle[keys][dsets], handle_out[keys], dset_name=dsets, trace_select=trace_select, dtype=chosen_dtype, repetititon_select=repetition_select, copy_doc=is_doc_group)
                # copy attributes
                HDF5utils.copy_attributes(handle[keys][dsets], handle_out[keys][dsets])

    @staticmethod
    def hdf5_get_positions(h5filehandle):
        """
        Retrieve a list of the four-digit groups corresponding to the measurement positions.
        :param h5filehandle: handle of the HDF5 file
        :return positions: list of group names
        """
        group_list = list(h5filehandle.keys())
        # measurement positions correspond to groups with a four-digit name
        r = re.compile(r"\d{4}")
        positions = list(filter(r.match, group_list))
        return positions

    @staticmethod
    def hdf5_get_xy_values(h5filehandle, positions):
        """
        Return the x and y values in mm of the measurement positions
        :param h5filehandle: handle of the HDF5 file
        :param positions: list with positions group names
        :return x: x-positions in mm
        :return y: y-positions in mm
        """

        x = np.ones((len(positions))) * -1
        y = np.ones((len(positions))) * -1
        for gdx, group in enumerate(positions):
            position_handle = h5filehandle["/" + group]
            x[gdx] = position_handle.attrs["x position [mm]"]
            y[gdx] = position_handle.attrs["y position [mm]"]
        return x, y

    @staticmethod
    def hdf5_convert_xy_to_tiles(x, y):
        """
        Convert x and y values of a regular grid into tile values needed for the AISEC attacktool
        :param x: array with x-values in mm for each position
        :param y: array with y-values in mm for each position
        :return tile_x: tile value for x for each position
        :return tile_y: tile value for y for each position
        """

        x_pos = np.unique(x)
        y_pos = np.unique(y)
        # assume a regular grid, i.e. all positions have the same distance from each other.
        tile_x = np.int_((x - np.min(x_pos)) / (x_pos[-1] - x_pos[-2]))
        tile_y = np.int_((y - np.min(y_pos)) / (y_pos[-1] - y_pos[-2]))
        return tile_x, tile_y

    @staticmethod
    def hdf5_apply_selection(sample_handle, traces, repetitions, sample_min=None, sample_max=None):
        """
        Takes the 'sample_handle' with data of dim [traces, samples, repetitions] and applies the selection of 'traces' and
        'repetitions', such that an array of dim [samples, traces/repetitions] is returned.
        IMPORTANT: either 'traces' or 'repetitions' needs to be of single dimension, i.e. selection of multiple traces and
        repetitions at the same time is not possible!
        :param sample_handle: handle
        :param traces: list with indices of traces that are selected, if 'None' all traces are selected
        :param repetitions: list with indices of repetitions that are selected, if 'None' all repetitions are selected
        :param sample_min: first sample of selection
        :param sample_max: last sample of selection
        :return samples: array with the selected data
        :return traces: ist with indices of traces that are selected
        :return repetitions: list with indices of repetitions that are selected
        """
        # Set defaults in case of None values
        if traces is None:
            # Use all traces
            traces = list(np.arange(0, sample_handle.shape[0]))
            _logger.info("Using all %i traces of %s." % (sample_handle.shape[0], sample_handle.name))
            # Use the first repetition (if not a single repetition is provided)
            if repetitions is None or len(repetitions) != 1:
                repetitions = [0]
            _logger.info("Using repetition %i of %s." % (repetitions[0], sample_handle.name))
        elif repetitions is None and len(traces) == 1:
            # If a particular trace, but no repetitions are provided, use all repetitions
            repetitions = list(np.arange(0, sample_handle.shape[2]))
            _logger.info("Using all %i repetitions of %s." % (sample_handle.shape[2], sample_handle.name))
        elif repetitions is None:
            # If more than one trace, but no repetitions are provided, use the first repetition
            repetitions = [0]

        # Defaults: start with first sample, until last sample
        if sample_min is None:
            sample_min = 0
        if sample_max is None:
            sample_max = sample_handle.shape[1]

        # apply selection
        if len(traces) != 0 and len(repetitions) == 1:
            # for single repetition: first dimension: trace(s), second dimension: time
            samples = np.array(sample_handle[traces, sample_min : sample_max + 1, repetitions[0]])
            # change order of dimensions to first dimension: time, second dimension: trace(s)
            samples = samples.transpose()
        elif len(repetitions) != 0 and len(traces) == 1:
            # for single trace, but multiple repetitions: first dimension: time, second dimension: repetitions
            samples = np.array(sample_handle[traces[0], sample_min : sample_max + 1, repetitions])
        else:
            _logger.error("Either 'traces' or 'repetitions' needs to be of single dimension!")
            sys.exit(1)

        return samples, traces, repetitions


class MISCutils:
    @staticmethod
    def sendmail(sender, receiver, subject, message):
        """
        Send an e-mail
        TODO: works only on puppet managed clients
        sender   - string
        receiver - string
        subject  - string
        message  - string
        """
        try:
            msg = MIMEText(message)
            msg["From"] = sender
            msg["To"] = receiver
            msg["Subject"] = subject
            p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
            p.communicate(msg.as_bytes())
            _logger.info("E-mail sent to %s" % (receiver))
        except Exception as e:
            _logger.warning("Sending of e-mail did not work: %s." % e)

    @staticmethod
    def subprocess_output(command):
        """
        Launch a process and readback from stdout
        :param command: string with the command
        :return stdout: result from stdout
        """
        # Launch the process
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        # Decode the results from bytes to string and remove the line break at the end.
        stdout = process.communicate()[0].decode()[:-1]
        return stdout

    @staticmethod
    def configure_logger(verbose=False, loglevel="info", format=None, filename=None):
        """
        Configures a logger with loglevel, format and logfile. For verbose flag, DEBUG level is used, otherwise INFO
        is default, but can be substituted.
        :param verbose: flag whether to use debug or the level specified by 'loglevel'
        :param loglevel: debug/info/warning are supported
        :param format: format of the logger, c.f. python logging docs
        :param filename: if a filename is provided, the log is written to it, otherwise outputs to the terminal
        :return:
        """

        if verbose:
            loglevel = logging.DEBUG
        else:
            # Configure the logger
            if loglevel == "debug":
                loglevel = logging.DEBUG
            elif loglevel == "warning":
                loglevel = logging.WARNING
            else:
                loglevel = logging.INFO

        if format is None:
            format = "[%(module)30s]  %(levelname)10s \t %(asctime)s: %(message)s"

        logging.basicConfig(filename=filename, format=format, level=loglevel)
        return


class FrequencyUtils:
    @staticmethod
    def single_sided_fft(x, fs=1, NFFT=None, conv_dec=True, windowing="Hanning", FFT_dim=0):
        """
        Calculates the single-sided FFT for a real valued signal and returns the frequency domain representation as well as
        the corresponding frequency values of the FFT bins
        :param x: array with signal, FFT is calculated along dim=1 [dim=0 for legacy]
        :param fs: sampling frequency [Hz]; default: 1
        :param NFFT: number of FFT bins (default: maximum determined by length of measurement)
        :param conv_dec: flag to convert spectrum to decibel straight away
        :param windowing: kind of window that is applied to avoid aliasing issues
        :param FFT_dim: dimension along which the FFT is calculated (default: 0 = time),
        :return: Y: frequency domain representation of x
        :return freqs: frequency values of the FFT bins
        :return NFFT: returns length of the FFT ()
        """

        if NFFT is None:
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.rfft.html#scipy.fft.rfft
            # for odd NFFT the result is complex (which we rather want to avoid)
            NFFT = FrequencyUtils.get_NFFT(x.shape[FFT_dim])
            # alternative default: get the next binary power to chose efficient FFT length --> zero padding is done
            # nextpow_2 = np.ceil(np.log2(x.shape[FFT_dim]))
            # NFFT = int(np.power(2, nextpow_2))

        if windowing == "Hanning":
            window_array = np.hanning(x.shape[FFT_dim])
        elif windowing == "Hamming":
            window_array = np.hamming(x.shape[FFT_dim])
        elif windowing == "Flattop":
            window_array = np.ones((x.shape[FFT_dim], 1))
            window_array[:, 0] = signal.windows.flattop(x.shape[FFT_dim])
        else:
            window_array = np.ones((x.shape[FFT_dim], 1))

        if len(x.shape) > 2:
            window = np.reshape(np.repeat(window_array, x.shape[(FFT_dim + 1) % 2] * x.shape[2], axis=0), [-1, x.shape[(FFT_dim + 1) % 2], x.shape[2]])
        else:
            window = np.reshape(np.repeat(window_array, x.shape[(FFT_dim + 1) % 2], axis=0), [-1, x.shape[(FFT_dim + 1) % 2]])
        if FFT_dim == 1:
            window = np.swapaxes(window, axis1=0, axis2=1)
        x = x * window

        # calculate FFT
        Y = np.fft.rfft(x, NFFT, axis=FFT_dim)

        if conv_dec:
            # convert to decibel (convert 0 input to Floating-point relative accuracy)
            Y = 10 * np.log10(np.clip(2 * abs(Y), a_min=np.spacing(1), a_max=None))

        # calculate frequency bins
        freqs = fs / 2 * np.linspace(0, 1, int(NFFT / 2 + 1))

        return Y, freqs, NFFT

    @staticmethod
    def get_NFFT(data_length):
        """
        :param data_length: integer with the length of the time domain signal that is to transfered to frequency domain
        :param NFFT: even number that is closest to the length and can be used for DFT such that [0, fs/2] is represented
        """

        """
         https: // docs.scipy.org / doc / scipy / reference / generated / scipy.fft.rfft.html  # scipy.fft.rfft
         Only for even number of NFFT the DFT/FFT represent fs/2, thus we want to be sure to only use even values.
        """

        # for odd numbers floor to the next even integer (crops the last sample)
        NFFT = data_length - data_length % 2
        # make sure we output an
        NFFT = int(NFFT)

        return NFFT

    @staticmethod
    def fft_smooth(data, order=2, cut=12000, filterdim=0):
        """
        Smoothes the FFT data by applying a Butterworth low pass filter
        :param data: FFT values
        :param order: Order of the filter
        :param cut: inverse coefficient of aggressiveness of the filter (100 = very aggressive)
        :param filterdim: dimension along which the filter is applied
        :return smmoth: smoothed spectrum
        """

        # cutoff is in radians/sample, scale this with fft data length to obtain similar filter results for different
        # array lengths we need to scale this as FFT delta_f changes with change in length
        cutoff = cut / data.shape[filterdim]
        # generate a Butterworth filter of desired order
        B, A = signal.butter(order, cutoff, output="ba")
        # apply filter along desired axis
        smooth = signal.filtfilt(b=B, a=A, x=data, axis=filterdim)
        return smooth

    @staticmethod
    def get_frequency_bins(freqs, freq_min=None, freq_max=None):
        """
        Get the bin corresponding to a minimum and a maximum frequency
        :param freqs: array with (sorted) frequencies [Hz]
        :param freq_min: minimum frequency [Hz]
        :param freq_max: maximum frequency [Hz]
        :return: freq_min_bin, freq_max_bin: indices/bins corresponding to the respective values in the array
        """

        # get corresponding indices of the frequency bins
        if freq_min is not None:
            # The first bin must include freq_min, i.e. freq_min is always contained
            freq_min_bin = max(0, np.argmax(freqs > freq_min) - 1)
        else:
            # Default: start with the lowest frequency available
            freq_min_bin = 0
        if freq_max is not None:
            # The last bin should be at least as high as freq_max, i.e. freq_max is always contained
            freq_max_bin = np.argmax(freqs >= freq_max)
            if freq_max_bin == 0:
                # if no value is greater equal to the desired maximum, use the maximum frequency available
                # catches also cases, where the desired freq_max is bigger than the available one!
                freq_max_bin = len(freqs) - 1
            else:
                # limit to the maximum frequency available
                freq_max_bin = min(len(freqs) - 1, freq_max_bin)
        else:
            freq_max_bin = len(freqs) - 1

        # make sure, the maximum frequency is at least as high as the lowest frequency
        freq_max_bin = max(freq_max_bin, freq_min_bin)

        if freq_min is not None and freqs[freq_min_bin] > freq_min:
            _logger.warning("Desired minimal frequency %0.f Hz is not contained, actual minimal frequency is %0.f Hz." % (freq_min, freqs[freq_min_bin]))

        if freq_max is not None and freqs[freq_max_bin] < freq_max:
            _logger.warning("Desired maximum frequency %0.f Hz is not contained, actual maximum frequency is %0.f Hz." % (freq_max, freqs[freq_max_bin]))

        return freq_min_bin, freq_max_bin

    def get_noisefloor_frequency_domain(noisefilehandle, group, dataset, freq_min, freq_max, traces, repetitions):
        """
        Extract the noise floor in the frequency domain from a filehandle. If the noise floor is averaged over repetitions
        and traces, i.e. accessing traces and/or repetitions is not possible, the single dimension is used as a noise floor.
        :param noisefilehandle: HDF5 filehandle
        :param group: four-digit group
        :param dataset: name of the dataset
        :param freq_min: minimum frequency [Hz]
        :param freq_max: maximum frequency [Hz]
        :param traces: list of the desired traces
        :param repetitions: list of the desired repetitions
        :return noise: array with noise floor
        """
        # get samples handle
        noise_handle = noisefilehandle["/" + group + "/" + dataset]
        # load frequencies of the noise file
        freqs_noise = np.array(noisefilehandle["/frequencies"])
        # get corresponding bins
        noise_bin_min, noise_bin_max = FrequencyUtils.get_frequency_bins(freqs_noise, freq_min=freq_min, freq_max=freq_max)
        try:
            # get array with selected traces
            noise, _, _ = HDF5utils.hdf5_apply_selection(sample_handle=noise_handle, traces=traces, repetitions=repetitions, sample_min=noise_bin_min, sample_max=noise_bin_max)
        except BaseException as e:
            # if the noise file has only a single dimension (due to averaging over traces and repetitions), use it
            _logger.warning("Could not access the noise trace index, likely the average noise spectrum is used.")
            _logger.warning(e)
            noise = np.transpose(np.array(noise_handle[:, noise_bin_min : noise_bin_max + 1]))
        return noise
