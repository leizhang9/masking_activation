#!/usr/bin/env python3
"""
trace_measurement: Script to take measurements at the TUEISEC
"""

__version__ = "2.5"

import argparse
import importlib
import commentjson as cjson
import logging
import numpy as np
import time
import sys
import os

from attack.helper.utils import HDF5utils as h5utils
from attack.helper.utils import JSONutils as jsonutils
from attack.helper.utils import DATAutils as datautils
from attack.helper.utils import MISCutils as miscutils
from attack.helper.Meander import Meander as tableutils

import attack.oscilloscope.picosdk6000 as PicoScope6000
import attack.oscilloscope.Keysight_254A as Keysight_254A
from attack.table.LangerICS105 import Koordinatentisch as LangerICS

_logger = logging.getLogger(__name__)


class Measurement(object):
    scope = None
    segment_counter = -1
    num_segs = -2

    def __init__(self, config, module_name, no_scope=False):
        # get configuration
        # Open config file
        with open(config, "r") as configfile:
            self.config = cjson.load(configfile)

        if no_scope:
            # for non-scope debugging replace scope by empty string
            self.config["scope"]["type"] = "no-scope"
            _logger.info("Running in 'no-scope' mode, i.e. scope configuration from config is ignored")

        # store path of config and target module in order to store the files in the HDF5
        self.config_path = config
        self.module_path = module_name

        # Import the module from a file path by adding its folder to the path
        try:
            # add path of the module to python path
            sys.path.append(os.path.realpath(os.path.dirname(self.module_path)))
            # import module
            self.target = importlib.import_module(os.path.splitext(os.path.basename(self.module_path))[0])
            # path is removed after import to avoid import issues
            sys.path.remove(os.path.realpath(os.path.dirname(module_name)))
            _logger.info("Target module %s successfully imported.", self.module_path)
        except ModuleNotFoundError as e:
            _logger.error("Could not import target module %s: %s" % (self.module_path, e))
            sys.exit(1)

        # change to the configfile's directory such that the entries in the config file can be relative
        # otherwise all relatively defined path will refer to the directory in which this script is living
        os.chdir(os.path.realpath(os.path.dirname(config)))

        self.trigger_delay = 0

    def __enter__(self):
        _logger.info("Startup...")
        # connect to the target (overwrite self.target with class TargetControl)
        try:
            self.target = self.target.TargetControl(
                port=jsonutils.json_try_access(self.config, ["target", "uart port"], default="/dev/ttyUSB0"),
                baudrate=jsonutils.json_try_access(self.config, ["target", "uart baudrate [Baud]"], default=115200),
                bytesize=jsonutils.json_try_access(self.config, ["target", "uart bytesize"], default=8),
                parity=jsonutils.json_try_access(self.config, ["target", "uart parity"], default="N"),
                stopbits=jsonutils.json_try_access(self.config, ["target", "uart stopbits"], default=1),
                config=self.config,
            )
        except AttributeError:
            _logger.error("The class 'TargetControl' could not be found in your --targetmodule file.")
            sys.exit(1)
        except TypeError as e:
            _logger.warning("Since version 2.3.0 of the Attack-Framework, Targetfile supports the argument 'config'. Please add it to your legacy Targetclass.")
            _logger.debug(e)
            try:
                self.target = self.target.TargetControl(
                    port=jsonutils.json_try_access(self.config, ["target", "uart port"], default="/dev/ttyUSB0"),
                    baudrate=jsonutils.json_try_access(self.config, ["target", "uart baudrate [Baud]"], default=115200),
                    bytesize=jsonutils.json_try_access(self.config, ["target", "uart bytesize"], default=8),
                    parity=jsonutils.json_try_access(self.config, ["target", "uart parity"], default="N"),
                    stopbits=jsonutils.json_try_access(self.config, ["target", "uart stopbits"], default=1),
                )
            except Exception as e:
                _logger.error(e)
                sys.exit(1)

        # configure target
        self.target.configure_device(jsonutils.json_try_access(self.config, ["target", "binary"], default=None), self.config)

        # retrieve scope type
        self.scope_type = jsonutils.json_try_access(self.config, ["scope", "type"], default="")

        # establish connection to the scope
        if "PicoScope 6" in self.scope_type:
            # try to connect to the PicoScope
            try:
                self.scope = PicoScope6000.PicoSDK6000()
                self.scope.open()
            except Exception:
                _logger.error("Connection to PicoScope 6000 could not be established.")
                exit()
        elif "Keysight 254A" in self.scope_type:
            # Try to connect to the Keysight
            try:
                self.scope = Keysight_254A.Keysight_DSOS_254A(jsonutils.json_try_access(self.config, ["scope", "url"]))
            except BaseException:
                _logger.error("Connection to Keysight 254A could not be established.")
                exit()
        else:
            _logger.warning('Scope "%s" not supported yet. Currently ("PicoScope 6", "Keysight 254A") are supported.' % self.scope_type)
            _logger.warning("Measurement script will be executed anyway without storing measurement data, i.e. target communication can be debugged.")

        self.scope_init()

        if jsonutils.json_try_access(self.config, ["table", "active"], default=False):
            # initialize the table
            self.table = self.table_init()

        # generate the coordinates
        self.table_coordinates()

        # set up HDF5 file
        self.h5filehandle = h5utils.hdf5_file_init(configfile=self.config, target_info=self.target.provide_info(), target_module_path=self.module_path, configfile_path=self.config_path, trace_measurement_version=__version__)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _logger.info("Closing...")

        if jsonutils.json_try_access(self.config, ["logging", "e-mail address for notification"], default=None) is not None:
            msg = "Measurement terminated: %s" % jsonutils.json_try_access(self.config, ["target", "description"])
            subj = "Measurement terminated."
            miscutils.sendmail(sender="", receiver=self.config["logging"]["e-mail address for notification"], message=msg, subject=subj)

        # close scope
        try:
            self.scope.close()
            _logger.info("Scope successfully closed.")
        except BaseException:
            _logger.warning("Scope could not be closed.")

        # save performance measures and recorded number of traces
        try:
            end_time = time.time()

            time_elapsed = end_time - self.start_time
            self.h5filehandle.attrs["Time elapsed [s]"] = time_elapsed
            self.h5filehandle.attrs["Overall number of traces"] = self.N_done
            self.h5filehandle.attrs["Throughput [traces/sec]"] = self.N_done / time_elapsed
        except BaseException:
            _logger.warning("Throughput attribute could not be written.")

        self.h5filehandle = h5utils.hdf5_file_close(self.h5filehandle)

    def scope_init(self):  # noqa: C901
        """
        Function to initialize the oscilloscope
        :return:
        """
        try:
            if "PicoScope 6" in self.scope_type:
                num_channels = 5
                capture_trigger = True
            elif "Keysight 254A" in self.scope_type:
                # TODO: currently only a single channel (plus trigger channel) is supported for Keysight
                num_channels = 2
                capture_trigger = False
                # execute some additional commands for Keysight
                self.scope_init_keysight()
            else:
                # should never happen as init should capture this already.
                # However, for debugging without scope this may be helpful
                num_channels = 0
                capture_trigger = False
                self.scope = type("obj", (object,), {"noSamples": 0})
                return

            for i in range(1, num_channels):
                # adapt default channel numbers
                if "PicoScope 6" in self.scope_type:
                    # Picoscope starts counting channels from 0
                    ch_idx = i - 1
                elif "Keysight 254A" in self.scope_type:
                    # Keyside starts counting channels from 1
                    ch_idx = i
                # activate channel for measurements
                self.scope.setChannel(
                    channel=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "channel"], default=ch_idx),
                    coupling=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "coupling"], default="DC"),
                    VRange=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "range [V]"], default=5.0),
                    BWLimited=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "BWLimited"], default=False),
                    enabled=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "enable"], default=False),
                    VOffset=jsonutils.json_try_access(self.config, ["scope", "channel%i" % i, "offset [V]"], default=0),
                )

            # Warning: The trigger has to be enabled. There will be no warning and the osci will work normally but the measurements are crap!
            # You tried to remove this, it did not work!
            if capture_trigger:
                # activate trigger channel if needed
                if self.config["scope"]["trigger"]["channel"] != 5:
                    self.scope.setChannel(channel=self.config["scope"]["trigger"]["channel"], coupling=self.config["scope"]["trigger"]["coupling"], VRange=self.config["scope"]["trigger"]["range [V]"], enabled=self.config["scope"]["trigger"]["enable"])  # Trigger Channel
                else:
                    _logger.info("You are using the Aux trigger")

            # external clock
            if self.config["scope"]["clock"]["use_external"]:
                # external clock threshold: use 100mV if not specified
                clock_ext_threshold = jsonutils.json_try_access(self.config, ["scope", "clock", "external clock threshold [V]"], default=100e-3)
                self.scope.setExternalClock(self.config["scope"]["clock"]["external clock frequency"], clock_ext_threshold)

            """
            **NOTE regarding PicoScope 6000**
            The osci has different timebases that can be divided by 156250000
            This means we have to set desired sample rate and the driver selects the closest sampling frequency and
            therefore caculates the needed number of samples -->  (timebase–4) / 156 250 000 --> timebase can be integers >= 5
            """
            try:
                sampling_rate = self.config["scope"]["sampling"]["sampling rate [S/s]"]
            except KeyError:
                # legacy support
                sampling_rate = self.config["scope"]["sampling"]["sampling rate [GS/s]"]
                _logger.warning("LEGACY: Your config file contains the field 'sampling rate [GS/s]', use 'sampling rate [S/s]' instead.")

            if "PicoScope 6" in self.scope_type:
                # set the interval and sampling rate
                self.scope.setSamplingInterval(sampleInterval=1.0 / sampling_rate, duration=self.config["scope"]["sampling"]["sampling duration [s]"])
                # The PicoScope uses multiples of 156.25 MHz as sampling frequency, i.e. it is important to read back
                # actual sampling frequency used by the scope. Otherwise the f_s value written to the HDF5 file differs
                # from the actually used one..
                # The resulting float is rounded to MHZ
                self.config["scope"]["sampling"]["sampling rate [S/s]"] = round(self.scope.sampleRate, -4)

            elif "Keysight 254A" in self.scope_type:
                # take into account negative trigger values only
                preTriggerSamples = max(0, -self.config["scope"]["trigger"]["delay [s]"])
                # set sampling interval
                self.scope.setSamplingInterval(sampling_duration=self.config["scope"]["sampling"]["sampling duration [s]"], preTriggerSamples=preTriggerSamples)

                # set the sampling rate
                self.scope.setSamplingRate(sampling_rate=sampling_rate)

            try:
                # calculate the trigger delay in samples as time [s] * sampling rate [S/s] = delay [S]
                self.trigger_delay = self.config["scope"]["trigger"]["delay [s]"]
                trigger_delay = int(sampling_rate * self.trigger_delay)
            except KeyError:
                try:
                    # legacy: until version 1.1.0 of the attack framework delay was given in samples
                    # This is likely to cause errors if the sampling rate is changed and thus replaced by calculating
                    # the number of samples from desired offset in seconds
                    trigger_delay = self.config["scope"]["trigger"]["delay [samples]"]
                    self.trigger_delay = trigger_delay / sampling_rate
                    _logger.warning("LEGACY: Your config file contains the field 'delay [samples]', use 'delay [s]' instead.")
                    _logger.warning("        Using seconds instead of samples is less error prone in case you change sampling rate.")
                except KeyError:
                    trigger_delay = 0
                    _logger.warning("Delay was neither specified in samples nor in seconds. Is set to default, i.e., 0.")

            # make sure not negative delays are used for setSimpleTrigger
            trigger_delay = max(trigger_delay, 0)

            self.scope.setSimpleTrigger(self.config["scope"]["trigger"]["channel"], threshold_V=self.config["scope"]["trigger"]["threshold [V]"], timeout_ms=self.config["scope"]["trigger"]["timeout [s]"] * 1000, direction=self.config["scope"]["trigger"]["direction"], delay=trigger_delay)

            if "Keysight 254A" in self.scope_type:
                # get the maximum number of segments and the number of samples that are used for acquisition
                self.max_segments, self.scope.noSamples = self.scope.calculate_max_number_of_segments()
                # Limit the number of segments (mainly debugging reasons)
                limit_segs = jsonutils.json_try_access(self.config, ["scope", "data_acquisition", "maximum segments"], default=self.max_segments)
                if limit_segs is not None:
                    self.max_segments = min(self.max_segments, limit_segs)
            _logger.info("Scope correctly initialized.")
        except BaseException:
            _logger.info("ERROR: Problem initializing scope: ", sys.exc_info()[0])
            sys.exit(0)

    def scope_init_keysight(self):
        """
        Init for the Keysight 254A. Sets up channels and the trigger.
        :return:
        """

        # Before applying any changes, stop the oscilloscope
        self.scope.send_query(":STOP;*OPC?")

        # set waveform format that is transmitted, turn headers off and set streaming mode on/off
        self.scope.config_instr(waveform_format="WORD", streaming=0)

        # set sweep mode to triggered
        self.scope.send_command_and_query(":TRIGger:SWEep TRIGgered")

    def scope_run(self):
        """
        Start acquisition
        :return:
        """

        if "PicoScope 6" in self.scope_type:
            # make sure that pretrigger is only used for negative trigger delays
            pretriggerTime = max(0, -self.trigger_delay)
            self.scope.runBlock(pretriggerTime)
        elif "Keysight 254A" in self.scope_type:

            if (self.segment_counter == 0) or (self.segment_counter == self.num_segs):
                # initialize the acquisition of different segments
                # last segment: reset segment counter to start new acquisition

                # make sure, the maximum number of segments contains a multiple of the number of repetitions
                # this allows easier indexing if many traces are stored at once
                max_segs = self.max_segments - (self.max_segments % self.N_repetitions)
                # make sure to capture only traces at a single position in one set, to avoid any inconvenience when
                # storing. Remaing traces for the current group are calculated:
                N_remaining_ingroup = int((self.N_overall - self.N_done) % (self.N_overall / self.N_positions))
                # if no traces remain, use as many as possible for a single position
                if N_remaining_ingroup == 0:
                    N_remaining_ingroup = int(self.N_overall / self.N_positions)

                # either use as many segments as possible (multiple of #ofRepetitions) or use as many as traces as
                # remaining for the current measurement position.
                self.num_segs = min(N_remaining_ingroup, max_segs)
                # make sure to measure only multiples of the repetitions
                self.num_segs = self.num_segs - (self.num_segs % self.N_repetitions)
                # set acquisition mode to segmented mode and switch off interpolation, chose maximum number of segments
                self.scope.set_acquisition(interpolation=0, acquisition_mode="SEGM", num_segments=self.num_segs)
                # clear display and registers and start single (polling) acquisition
                self.scope.clear_and_start_single()

                # insert short delay
                time.sleep(jsonutils.json_try_access(self.config, ["msmt", "delay [s]"], default=0))

                # reset segment counter
                self.segment_counter = 1
            else:
                # increase segment counter
                self.segment_counter = self.segment_counter + 1
                # TODO: check whether Keysight needs a slightly higher delay for first segment [could be included here]

    def scope_get_trace(self, channel=1):
        """
        Retrieve data
        :param channel:
        :return:
        """
        if "PicoScope 6" in self.scope_type:
            self.scope.waitReady()
            data, t_samples, test = self.scope.getDataRaw(self.config["scope"]["channel%i" % channel]["channel"], self.scope.noSamples)
        elif "Keysight 254A" in self.scope_type:
            # segment mode: retrieve data only after the last segment
            if self.segment_counter == self.num_segs:
                # check whether the processing is finished
                acquisition_done = self.scope.check_processing_done(time_out=jsonutils.json_try_access(self.config, ["scope", "trigger", "timeout [s]"]), poll_time=None)

                if acquisition_done:
                    time.sleep(jsonutils.json_try_access(self.config, ["msmt", "delay [s]"], default=0))
                    # acquire data from scope
                    data, t_samples, x_origin, x_increment, y_origin, y_increment = self.scope.send_data_query(max_block_size=jsonutils.json_try_access(self.config, ["scope", "data_acquisition", "maximum blocksize"], default=10e6))

                    # reshape the data such that
                    # 1st dim = samples
                    # 2end dim = traces (per position)
                    # 3rd dim = repetitions
                    data = np.reshape(data, (self.scope.noSamples, int(self.num_segs / self.N_repetitions), -1), order="F")
                    # swap axes such that 1st dimension=traces, 2nd=samples, 3rd=repetitions
                    data = np.swapaxes(data, 0, 1)
                else:
                    # return all-zero array
                    # TODO: develop a smarter way if a trigger gets lost. I.e. instead of storing zeros, repeating
                    # measurements could make sense
                    data = np.zeros((int(self.num_segs / self.N_repetitions), self.scope.noSamples, self.N_repetitions), dtype=np.int16)
            else:
                data = None
        else:
            data = None
        return data

    def table_init(self):
        """
        initialize the xyz table.
        Make sure to start the VM before and connect via socat (legacy), c.f. documentation in the attack framework.
        :return:
        """

        # create class of the langer table
        table = LangerICS()
        # If the table is not calibrated, calibrate it (requires user interaction)
        if not table.isCalibrated():
            table.calibratePos()

        return table

    def table_coordinates(self):
        """
        generate table coordinates from the config file
        :return:
        """

        if jsonutils.json_try_access(self.config, ["table", "active"], default=False):
            # get the desires coordinates from the config file
            meander_coordinates = tableutils.horMeander(
                xOrigin=jsonutils.json_try_access(self.config, ["table", "xOrigin [mm]"], default=0),
                yOrigin=jsonutils.json_try_access(self.config, ["table", "yOrigin [mm]"], default=0),
                xLen=jsonutils.json_try_access(self.config, ["table", "xLen [mm]"], default=0),
                yLen=jsonutils.json_try_access(self.config, ["table", "yLen [mm]"], default=0),
                resolution=jsonutils.json_try_access(self.config, ["table", "resolution [mm]"], default=0),
            )

            self.x = meander_coordinates[0]
            self.y = meander_coordinates[1]
            self.z = jsonutils.json_try_access(self.config, ["table", "zOrigin [mm]"], default=0)
        else:
            self.x = [None]
            self.y = [None]
            self.z = None
        return

    def table_move(self, position):
        """
        Move the table
        :return:
        """

        if jsonutils.json_try_access(self.config, ["table", "active"], default=False):
            xPos = float(self.x[position])
            yPos = float(self.y[position])
            zPos = self.z
            # retract z-Axis
            self.table.moveRelPos(x=0, y=0, z=jsonutils.json_try_access(self.config, ["table", "zRetractHeight [mm]"], default=5))

            # move the table to the next position, the z-axis remains contant
            self.table.moveAbsPos(x=xPos, y=yPos, z=zPos)
        return

    def get_traces(self):  # noqa: C901
        self.N_traces = int(jsonutils.json_try_access(self.config, ["msmt", "number of traces"], default=0))
        self.N_dummy = int(jsonutils.json_try_access(self.config, ["msmt", "number of dummy traces"], default=0))
        self.N_repetitions = int(jsonutils.json_try_access(self.config, ["msmt", "repetitions"], default=1))
        self.dummytime = int(jsonutils.json_try_access(self.config, ["msmt", "dummy time [s]"], default=0))

        # Determine number of different positions
        self.N_positions = len(self.x)

        # Number of desired overall measurements
        self.N_overall = self.N_traces * self.N_repetitions * self.N_positions
        self.N_perposition = self.N_traces * self.N_repetitions
        # counter of the traces that have been acquired so far
        self.N_done = 0

        # Setup scope and wait
        # Done here since the first trigger is often lost with PicoScopes. Could be avoided if someone has a smart idea.
        self.scope_run()
        time.sleep(5)

        if "PicoScope 6" in self.scope_type:
            if self.N_dummy > 0:
                _logger.info("Taking %i dummy measurements..." % self.N_dummy)
                for trace in range(0, self.N_dummy):
                    _logger.info("Dummy measurement: %i / %i" % (trace + 1, self.N_dummy))

                    # load data to the target
                    self.target.load_data(self.config, trace)

                    self.scope_run()
                    time.sleep(self.config["msmt"]["delay [s]"])

                    # set the key on the target
                    self.target.execute_trigger(config=self.config, trace=trace, repetition=0)

            elif self.dummytime > 0:
                start_dummy_time = time.time()
                dummy_time = 0
                _logger.info("Taking %i min dummy measurements..." % (self.dummytime / 60))
                while dummy_time < self.dummytime:
                    # load data to the target
                    self.target.load_data(self.config, trace=0)

                    self.scope_run()
                    time.sleep(self.config["msmt"]["delay [s]"])

                    # set the key on the target
                    self.target.execute_trigger(config=self.config, trace=0, repetition=0)

                    dummy_time = time.time() - start_dummy_time

                _logger.info("Dummy measurements finished...")

        self.start_time = time.time()
        for position in range(0, self.N_positions):
            if self.N_positions > 1:
                _logger.info("Position %i / %i: (x,y) = (%.2f,%.2f)" % (position + 1, self.N_positions, self.x[position], self.y[position]))

            # add group for meaurements
            self.h5filehandle, diff_datasets = h5utils.hdf5_add_group(h5filehandle=self.h5filehandle, configfile=self.config, N_traces=self.N_traces, noSamples=self.scope.noSamples, group=position, N_repetitions=self.N_repetitions, x=self.x[position], y=self.y[position], z=self.z)

            # move the table
            self.table_move(position=position)

            for trace in range(0, self.N_traces):
                _logger.info("Measurement: %i / %i" % (trace + 1, self.N_traces))

                # load data to the target
                input_data = self.target.load_data(self.config, trace)

                for repetition in range(0, self.N_repetitions):
                    _logger.debug("Repetition: %i / %i" % (repetition + 1, self.N_repetitions))
                    # activate the scope and add short delay, s.t. the trigger is armed
                    self.scope_run()
                    time.sleep(self.config["msmt"]["delay [s]"])

                    # set the key on the target
                    trigger_data = self.target.execute_trigger(config=self.config, trace=trace, repetition=repetition)
                    # get measurements

                    # read back data from device
                    output_data = self.target.read_data(config=self.config, trace=trace)

                    # update number of measurements done
                    self.N_done = self.N_done + 1

                    # add the measurements from different channels
                    for channel in diff_datasets:
                        # check if trigger is exceeded or not and repeat measurement if necessary
                        trigger_exceeded = True
                        while trigger_exceeded:
                            # measure time until measurement is finished
                            t_start = time.time()
                            data = self.scope_get_trace(channel=channel[0])
                            t_end = time.time()
                            trigger_time = int(np.around(t_end - t_start))
                            # check if measured time is near the defined trigger timeout
                            if trigger_time >= jsonutils.json_try_access(self.config, ["scope", "trigger", "timeout [s]"]):
                                _logger.warning("Trigger exceeded and not recognized! Try to repeat measurement %i with repetition %i" % (trace + 1, repetition + 1))
                                self.scope_run()
                                # reset the key on the target
                                trigger_data = self.target.execute_trigger(config=self.config, trace=trace, repetition=repetition)
                                # read back data from device
                                output_data = self.target.read_data(config=self.config, trace=trace)
                            else:
                                trigger_exceeded = False

                        # some scopes (e.g. PicoScope 6000) return int16 because certain timesampling modes need a higher
                        # resolution. However, in normal mode only 8-bit resolution is actually achieved. Hence, data space
                        # can be saved by storing only 8-bit values.
                        if data is None:
                            pass
                        elif self.config["HDF5"]["datasets"][channel[1]]["datatype"] == "int8" and data.dtype == np.int16:
                            # convert int16 to int8
                            data = datautils.convert_int16toint8(data)
                        elif self.config["HDF5"]["datasets"][channel[1]]["datatype"] == "uint8" and data.dtype != np.uint8:
                            # directly convert to uint8
                            data = datautils.convert_to_uint8(data)

                        if data is None:
                            # do nothing
                            pass
                        elif len(data.shape) == 1:
                            # for PicoScope only a single dimension is returned
                            self.h5filehandle = h5utils.hdf5_add_data(self.h5filehandle, channel[1], data, trace, position, repetition)
                        elif len(data.shape) > 1:
                            # if more than one trace (i.e. dimension) is returned, write it to the respective place in
                            # the dataset
                            # TODO: check whether correct indices are addressed.
                            self.h5filehandle = h5utils.hdf5_add_data_multitrace(h5filehandle=self.h5filehandle, dataset_name=channel[1], data=data, trace_indices=[int(trace - self.num_segs / self.N_repetitions + 1), trace + 1], group=position, repetition_indices=[0, None])

                    # add the input, output and trigger data
                    if repetition == 0 or jsonutils.json_try_access(self.config, ["HDF5", "store_for_all_repetitions"], default=False):
                        # store data only for the first repetition

                        # add the different input datasets
                        for input_datasets in self.config["HDF5"]["saving"]["input_data"]:
                            self.h5filehandle = h5utils.hdf5_add_data(h5filehandle=self.h5filehandle, dataset_name=self.config["HDF5"]["saving"]["input_data"][input_datasets], data=input_data[int(input_datasets)], trace_number=trace, group=position, repetition_number=repetition)
                        # add the different trigger datasets
                        for trigger_datasets in self.config["HDF5"]["saving"]["trigger_data"]:
                            self.h5filehandle = h5utils.hdf5_add_data(h5filehandle=self.h5filehandle, dataset_name=self.config["HDF5"]["saving"]["trigger_data"][trigger_datasets], data=trigger_data[int(trigger_datasets)], trace_number=trace, group=position, repetition_number=repetition)

                        # add the different output datasets
                        for output_datasets in self.config["HDF5"]["saving"]["output_data"]:
                            self.h5filehandle = h5utils.hdf5_add_data(h5filehandle=self.h5filehandle, dataset_name=self.config["HDF5"]["saving"]["output_data"][output_datasets], data=output_data[int(output_datasets)], trace_number=trace, group=position, repetition_number=repetition)

        end_time = time.time()

        time_elapsed = end_time - self.start_time
        self.h5filehandle.attrs["Time elapsed [s]"] = time_elapsed
        self.h5filehandle.attrs["Overall number of traces"] = self.N_done
        self.h5filehandle.attrs["Throughput [traces/sec]"] = self.N_done / time_elapsed

        _logger.info("Finished.")
        _logger.info("Time elapsed: %.1f seconds (about %.2f hours) for %i measurements" % (time_elapsed, time_elapsed / 3600, self.N_done))


def main():
    # Argument parse
    parser = argparse.ArgumentParser(description="Script for measuring consecutive loadings of a key.")
    parser.add_argument("-c", "--configfile", dest="configfile", metavar="filename", help="Config file name (*.json).", type=str, required=True)
    parser.add_argument("-t", "--targetmodule", dest="targetmodule", metavar="filename", help="Path (absolute or relative) to the file with the TargetControl class (*.py).", type=str, required=True)
    parser.add_argument("--no-scope", dest="no_scope", action="store_true", help="Flag for debugging without scope attached.")

    args = parser.parse_args()

    # Open config file
    with open(args.configfile, "r") as configfile:
        config = cjson.load(configfile)

    # Configure the logger
    if "debug" in config["logging"]["level"]:
        loglevel = logging.DEBUG
    elif "warning" in config["logging"]["level"]:
        loglevel = logging.WARNING
    else:
        loglevel = logging.INFO

    logging.basicConfig(filename=config["logging"]["file"], level=loglevel, format=config["logging"]["logformat"])

    # check whether the path to the target module is a valid input
    if ".py" not in os.path.splitext(args.targetmodule)[-1]:
        _logger.error("Target module requires a .py file.")
        sys.exit(1)

    with Measurement(args.configfile, args.targetmodule, args.no_scope) as meas:
        meas.get_traces()

    _logger.info("Exit.")


# run program
if __name__ == "__main__":
    main()
