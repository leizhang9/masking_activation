import vxi11
import numpy as np
import logging
import time
import sys

_logger = logging.getLogger(__name__)


class Keysight_DSOS_254A:
    instr = None

    def __init__(self, lan_address="TCPIP::WINDOWS-UH2SI2U.sec.ei.tum.de::inst0::INSTR", reset=True):
        """

        :param lan_address: LAN address of the oscilloscope you want to control. On the Keysight devices, start the
                            Infiniium software and have a look at Utilities->Remote to figure out the correct address
        :param reset:       If True, the oscilloscope is reset to its default state after connection
        """

        self.openUnit(lan_address, reset)

    def __exit__(self):
        """

        :return:
        """
        # clear communication and close unit upon exit.
        self.close_unit()

    def openUnit(self, lan_address, reset):
        """
        establishes a connection to a VISA instrument and displays information about the device
        :param lan_address: VISA instrument address to use the VXI-11 LAN protocol
        :param reset:       Send an *RST command to the device after connection
        :return:
        """

        # initialize the instrument
        self.instr = vxi11.Instrument(lan_address)
        try:
            # clear status
            self.send_command("*CLS")
            # query IDN string
            response = self.send_query("*IDN?")
            _logger.info("Connected to " + response)
            if reset:
                # Load the default setup.
                self.send_command("*RST")
        except Exception:
            _logger.error("Connection to the oscilloscope could not be established! \n " "You were trying to connect to %s. Please make sure the oscilloscope is " "connected and reachable under the given address." % lan_address)
            quit()

    def perform_self_test(self, global_time_out=10):

        # Set the timeout of the communication to a value that exceeds the time of the self test (approx. 30 secs)
        self.instr.timeout = 100

        # Perform a self-test
        test_result = self.send_query("*TST?")

        if test_result == "0":
            _logger.info("Self test was passed.")
        else:
            _logger.warning("The self test from failed. Error message provides was: \n" + test_result + ".")

        # reset the commnunication time out time
        self.instr.timeout = global_time_out
        return test_result

    def send_command(self, command, hide_params=False):
        """
        sent a command and check for errors
        This functions is adapted from the example of the Keysight programmers guide.
        :param command: command string
        :param hide_params: only the command without parameter is sent
        :return:
        """

        if hide_params:
            (header, data) = command.split(" ", 1)
            # added this line compared to programmer's guide as otherwise no command would be sent
            # subsequently the conditional branches can be left out
            command = header

        _logger.debug("\nCmd = '%s'" % command)
        # send command
        self.instr.write("%s" % command)
        # check for error
        self.check_instrument_errors(command)

    def send_command_and_query(self, command):
        """
        send a command and query directly afterwards to see if the desired parameter was accepted. This function works
        for most commands, i.e. for those that follow the structure ':COMMAND:PARAMAETER1:PARAMETER2 VALUE'. In this
        case, the query is done as ':COMMAND:PARAMAETER1:PARAMETER2?'.
        TODO: For different command structures, this would need an adaption.
        :param command:
        :return:
        """
        (header, parameter) = command.split(" ", 1)
        self.send_command(command)
        result = self.send_query("%s?" % header)

        return result

    def send_query(self, query, mute=False):
        """
        send a query, check for errors and return the query result
        This functions is adapted from the example of the Keysight programmers guide.
        :param query: query string
        :param mute: do not provide logging output
        :return: string with the query result
        """

        if not mute:
            _logger.debug("Qys = %s" % str(query))

        # send query
        result = self.instr.ask("%s" % query)
        # check for error
        self.check_instrument_errors(query)

        if not mute:
            _logger.debug("%s is set to: %s" % (query, result))
        return result

    def send_data_query(self, max_block_size=10e6, segmented_rapid=False):  # noqa: C901
        """
        Retrieves data from the oscilloscope.
        inspired by osciTest.py by Thomas Schamberger, the programmers guide and T.Kirchners read_date()-MATLAB function
        :param max_block_size: maximum block size for retrieving the data. If the maximum block size is bigger than the
                               number of samples, all samples are retrieved at once. Otherwise the data is loaded in
                               chunks
        :return: data: numpy array with the data and dimensions [samples x segments]
        :return: n_samples: number of samples
        :return: x_origin: value of the x (time) origin
        :return: x_increment: increment between two points in x-direction
        :return: y_origin: value of the x (voltage) origin
        :return: y_increment: increment between two points in y-direction
        """
        # Query the waveform format to be able to convert the data from the oscilloscope
        waveform_format = self.send_query(":WAVeform:FORMat?", mute=True)

        # The :WAVeform:SEGMented:COUNt? query returns the index number of the last captured segment. A return value of
        # zero indicates that the :ACQuire:MODE is not set to SEGMented.
        # Instead, the :ACQuire:SEGMented:COUNT? query is used, which returns the number of segments control value. This
        # avoid loosing segments if the waveform is not completely finished yet. Furthermore, this command is also used
        # in thr programmer's guide (c.f. page 191) to determine the number of segments.

        mode = self.send_query(":ACQuire:MODE?")
        if "SEG" in mode:
            num_segments = int(self.send_query(":ACQuire:SEGMented:COUNt?", mute=True))
        else:
            num_segments = 0

        # if segmented mode is selected, rapid download of data can be achieved by downloading all segments at once
        if num_segments > 0 and segmented_rapid:
            # The :WAVeform:SEGmented:ALL command configures the DATA query for rapidly
            # downloading all segments in one query.
            # The <start> and <size> optional parameters for the DATA query are still supported
            # and represent the start and size of the data for each segment.
            self.send_command_and_query(":WAVeform:SEGMented:ALL ON")

        # These value are needed to convert the int values from BYTE and WORD formats into voltage values
        x_origin = float(self.send_query(":WAVeform:XORigin?", mute=True))
        x_increment = float(self.send_query(":WAVeform:XINCrement?", mute=True))
        y_origin = float(self.send_query(":WAVeform:YORigin?", mute=True))
        y_increment = float(self.send_query(":WAVeform:YINCrement?", mute=True))

        # get the number of samples. Using the :ACQuire:POINts:ANALog? query is more precise as the :WAVeform:POINts?
        # command will also return interpolated values, so it is not useful. c.f. programmers guide p.190, p.218, p.1416
        n_samples = int(self.send_query(":ACQuire:POINts:ANALog?", mute=True))

        # determine the block size for read out: if overall points are smaller
        block_size = int(min(np.power(2, np.ceil(np.log2(n_samples))), max_block_size))
        num_blocks = int(max(1, np.ceil(n_samples / block_size)))

        # preallocate data array
        if waveform_format == "BYTE":
            data = np.zeros((n_samples, max(num_segments, 1)), dtype=np.int8)
        elif waveform_format == "WORD":
            data = np.zeros((n_samples, max(num_segments, 1)), dtype=np.int16)
        else:
            data = np.zeros((n_samples, max(num_segments, 1)))

        # set byte order to least significant byte first as the data transfer rate is faster using the LSBFirst byte
        # order, c.f. programmers guide p.1385
        if self.instr.ask(":WAVeform:BYTeorder?") != "LSBF":
            self.instr.write(":WAVeform:BYTeorder LSBFirst")

        # download data segment by segment (or as one segment if the segment_rapid is set)
        for seg in range(0, max(num_segments, 1)):
            if num_segments > 0:
                # In segmented mode, place the segment on the screen
                self.send_command(":ACQuire:SEGMented:INDex {}".format(seg + 1))

            # It can be beneficial to download the data in smaller data chunks defined by the maximum block size
            for block in range(0, num_blocks):
                # calculate the starting point and the size of the current data block
                start_point = block * block_size + 1
                end_point = min((block + 1) * block_size, n_samples)
                read_points = end_point - start_point + 1

                # The :WAVeform:DATA? query outputs waveform data to the computer over the remote interface. The data is
                # copied from a waveform memory, function, channel bus, pod, or digital channel previously specified
                # with the :WAVeform:SOURce command.
                self.instr.write(":WAV:DATA? {},{}".format(start_point, read_points))

                # read back all data
                data_raw = self.instr.read_raw(-1)

                """ The data structure returned by the query is as follows:
                Streaming Off: #|N|L(N bytes)|B_0|B_1|B_2|...|B_{L-1}|END
                Streaming On:  #|0|B_0|B_1|B_2|...|B_{L-1}|END
                where END is a line break (\n), B_i are the bytes, L gives the number of bytes and N the length of L.
                """
                # depending on streaming mode, calculate the offset necessary. Do this only for the first block, as
                # other segments are assumed/supposed to have the same streaming mode. Also do it for the last block at
                # it may have a different length.
                # This is only relevant for BYTE and WORD formats.
                if (block == 0 or block == num_blocks - 1) and "ASC" not in waveform_format:
                    if self.send_query("WAVeform:STReaming?", mute=True) == "1":
                        offset = 2
                    else:
                        offset = 2 + int(chr(data_raw[1]))

                # Strip the data from the first two bytes, which are always '#0' and the trailing newline
                # numpy from buffer : https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.frombuffer.html
                # The datatype has to converted to Big-Endian: '>h' =int16 with big endian
                if segmented_rapid:
                    if waveform_format == "BYTE":
                        data_raw = np.frombuffer(data_raw[offset:-1], dtype=np.int8)
                    elif waveform_format == "WORD":
                        data_raw = np.frombuffer(data_raw[offset:-1], dtype=np.dtype(np.int16))
                    elif "ASC" in waveform_format:
                        data_raw = np.fromstring(data_raw[:-1], sep=",")
                    # Reshaping has to be applied
                    data[start_point - 1 : end_point, :] = data_raw.reshape((read_points, num_segments))
                else:
                    if waveform_format == "BYTE":
                        data[start_point - 1 : end_point, seg] = np.frombuffer(data_raw[offset:-1], dtype=np.int8)
                    elif waveform_format == "WORD":
                        data[start_point - 1 : end_point, seg] = np.frombuffer(data_raw[offset:-1], dtype=np.dtype(np.int16))
                    elif "ASC" in waveform_format:
                        data[start_point - 1 : end_point, seg] = np.fromstring(data_raw[:-1], sep=",")

            if segmented_rapid:
                # return directly without iterating over the other segments
                return data, n_samples, x_origin, x_increment, y_origin, y_increment

        return data, n_samples, x_origin, x_increment, y_origin, y_increment

    def check_instrument_errors(self, command):
        """
        checks for errors in the communication.
        This functions is adapted from the example of the Keysight programmers guide.
        :param command: command string
        :return:
        """
        while True:
            error_string = self.instr.ask(":SYSTem:ERRor? STRing")
            if error_string:
                # If there is an error string value.
                if error_string.find("0,", 0, 2) == -1:
                    # Not "No error".
                    _logger.error("ERROR: %s, command: '%s'" % (error_string, command))
                    _logger.error("Exited because of error.")
                    sys.exit(1)
                else:
                    break
                    # "No error"
            else:
                # :SYSTem:ERRor? STRing should always return string.
                _logger.error(":SYSTem:ERRor? STRing returned nothing, command: '%s'" % command)
                _logger.error("Exited because of error.")
                sys.exit(1)

    def setChannel(self, channel=1, coupling="DC", VRange=2.0, VOffset=0.0, enabled=False, BWLimited=0, probeAttenuation=1.0):
        """

        :param channel: channel number. Possible values are [1-4]
        :param coupling: possible values DC (DC coupling 1MΩ impedance), DC50 (DC coupling, 50Ω impedance),
               AC (AC coupling, 1MΩ impedance). With 1153A probe LFR1 | LFR2 (AC 1 M Ω input impedance) is possible for
               low-frequency reject, c.f. programmers guide p.315
        :param VRange:
        :param Offset:
        :param enabled:
        :param BWLimited:
        :param probeAttenuation:
        :return:
        """

        self.send_command(":CHANnel{}:PROBe {},RAT".format(channel, probeAttenuation))
        self.send_command_and_query(":CHANnel{}:INPut {}".format(channel, coupling))
        self.send_command_and_query(":CHANnel{}:RANGe {}".format(channel, VRange))
        self.send_command_and_query(":CHANnel{}:OFFSet {}".format(channel, VOffset))
        if not isinstance(BWLimited, str):
            # make sure that True/False are converted to 1/0
            BWLimited = int(BWLimited)
        self.send_command_and_query(":CHANnel{}:BWLimit {}".format(channel, int(BWLimited)))

        if enabled:
            # Set the channel to sample, the format is set seperately
            self.send_command_and_query(":WAVEFORM:SOURCE CHANNEL{}".format(channel))
            self.send_command_and_query(":CHANnel{}:DISPlay ON".format(channel))

    def setSamplingInterval(self, sampling_duration=10e-6, preTriggerSamples=None, preTriggerRelative=None):
        """
        sets the sampling duration displayed on the screen. The number of samples before the trigger can be specified
        either as an absolute value in [s] using 'preTriggerSamples' or relatively to the sampling duration using
        'preTriggerRelavtive'. The former is used if both values are given
        :param sampling_duration: duration of the measurement in seconds
        :param preTriggerSamples: duration before the trigger in seconds
        :param preTriggerRelative: percentage of the sampling duration that is used for pretrigger sampling
        :return:
        """

        if preTriggerSamples is not None:
            # Set the range that is displayed on the screen as sum of sampling duration and pretrigger samples
            self.send_command_and_query("TIMEBASE:RANGE {}".format(sampling_duration + preTriggerSamples))
            # Set the timeframe to the left of the screen
            self.send_command_and_query("TIMEBASE:REFERENCE LEFT")
            # We want a little offset to capture something right before the trigger event (offset has to be negative)
            self.instr.write("TIMEBASE:POSITION {}".format(-preTriggerSamples))
        elif preTriggerRelative is not None:
            # Set the range that is displayed on the screen
            self.send_command_and_query("TIMEBASE:RANGE {}".format(sampling_duration))
            #
            self.send_command_and_query(":TIMebase:REFerence:PERCent {}".format(preTriggerRelative))
        else:
            # Set the range that is displayed on the screen
            self.send_command_and_query("TIMEBASE:RANGE {}".format(sampling_duration))
            # Set the timeframe to the left of the screen
            self.send_command_and_query("TIMEBASE:REFERENCE LEFT")

    def setSamplingRate(self, sampling_rate):
        """
        Set the sampling rate for acquiistion
        :param sampling_rate:
        :return:
        """
        # set sampling rate
        self.send_command_and_query(":ACQuire:SRATe:ANALog {}".format(sampling_rate))
        # set number of points for acquisition to auto mode
        self.send_command_and_query(":ACQuire:POINts:ANALog AUTO")

    def setSimpleTrigger(self, trigSrc=1, threshold_V=0.0, direction="Rising", delay=0, timeout_ms=100, enabled=True):
        """
        Generate a simple edge trigger
        :param trigSrc: channel of the trigger. Possible values are [1-4], AUX, LINE
        :param threshold_V: trigger threshold in V
        :param direction: "Rising" and "Falling" are supported
        :param delay: TODO: implement delay of the trigger
        :param timeout_ms: TODO: implement a timeout after which the trigger is raised automatically
        :param enabled TODO: figure out whether anything else than "True" makes sense for this parameter
        :return:
        """
        if direction == "Rising":
            self.send_command_and_query(":TRIGger:MODE EDGE")
            self.send_command_and_query(":TRIGger:EDGE:SLOPe POSitive")
        elif direction == "Falling":
            self.send_command_and_query(":TRIGger:MODE EDGE")
            self.send_command_and_query(":TRIGger:EDGE:SLOPe NEGative")

        if isinstance(trigSrc, str):
            source = trigSrc
        else:
            source = "CHANnel%d" % trigSrc

        self.send_command_and_query(":TRIGger:EDGE:SOURCE %s" % source)
        if source.lower() != "line":
            # Line trigger does not support trigger level setting
            self.send_command(":TRIGger:LEVel %s,%f" % (source, threshold_V))
            _logger.debug(":TRIGger:LEVel CHANnel is set to: %s" % self.send_query(":TRIGger:LEVel? %s" % source))

        _logger.warning("Positive trigger delay and timeout are not implemented yet for Keysight!")

    def setExternalClock(self, frequency, threshold):

        _logger.info("Currently, Keysight does not support use of external clock")

    def calculate_max_number_of_segments(self, osci_num_points=200e6):
        """
        Calculates the maximum number of segments that can be set, given the size of the oscilloscope buffer and the
        number of points per acquisition.
        :param osci_num_points:  size of the oscilloscope buffer
        :return:
        """
        s_points = int(self.send_query(":ACQuire:POINts:ANALog?"))

        return int(np.floor(osci_num_points / s_points)), s_points

    def clear_and_start_single(self):
        """
        Clear display and registers and start single acquiistion (polling).
        :return:
        """
        # clear display
        self.send_command(":CDISplay")
        # clear registers
        self.send_command("*CLS")
        # start single acquisition mode
        self.send_command("*CLS;:SINGle")

    def check_processing_done(self, time_out=1, poll_time=None):
        """
        Check whether the acquisition and processing are finished. After the defined timeout, stop querying and assume
        a trigger was missed
        :param time_out: time out in [s]
        :param poll_time: interval in which the PDER query is sent [s]
        :return: boolean whether acquisition is done (True) or whether acquisition was aborted due to timeout (False)
        """
        # Default: poll every 5ms
        if poll_time is None:
            poll_time = 0.005

        # start timer
        start_time = time.time()
        # query processing done event register (PDER)
        ProcDone = int(self.send_query(":PDER?"))
        # calculate wait time
        wait_time = time.time() - start_time

        # as long as PDER does not acknowledge termintation of acquisition and processing, query the PDER
        while ProcDone == 0:
            if wait_time < time_out:
                # as long as time out is not reached, query the PDER
                ProcDone = int(self.send_query(":PDER?"))
                time.sleep(poll_time)
                wait_time = time.time() - start_time
            else:
                # if time out is reached, abort querying the PDER and return "False"
                _logger.error("Acquisition failed due to time out. Maybe a trigger was missed or processing is not " "terminated yet.")
                return False

        return True

    def config_instr(self, waveform_format="WORD", streaming=0):
        """
        :param waveform_format: format for tranmissiom of the waveform data: 'WORD'/'BYTE' (c.f. proguide p. 1413)
        BYTE: signed 8-bit integers
        WORD: signed 16-bit integers in two bytes. The value 31232 represents a  hole level that can occur using the
              equivalent time sampling mode
        :param streaming: 0 (Off) / 1 (On)
        :return: max_num_points: returns the maximum number of data points that can be transferred with the selected
                 combination of waveform format and streaming mode.
        """

        """
        NOTE from Programmers guide (p.1155): Turn headers off when returning values to numeric variables. Headers are
        always off for all common command queries because headers are not defined in the IEEE 488.2 standard.
        """
        self.send_command(":SYSTem:HEADer OFF")

        """
        When the data format is WORD and streaming is off, the number of waveform points must be less than 500,000,000
        or an error occurs and only 499,999,999 words of data are sent. (c.f. programmers guide)
        """
        self.send_command(":WAVEFORM:FORMAT " + waveform_format)
        self.send_command_and_query(":WAVEFORM:STReaming " + str(streaming))
        # The data transfer rate is faster using the LSBFirst byte order. (c.f. programmers guide, p. 1385)
        self.send_command(":WAVEFORM:BYTeorder LSBFirst")

        if streaming:
            """
            When streaming is on there is no limit on the number of waveform data points that
            are returned. It is recommended that any new programs use streaming on to send
            waveform data points. (c.f. programmers guide)
            """
            # -1 is returned as an indicator for infinity
            max_num_points = -1
        else:
            """
            When the data format is BYTE and streaming is
            off, the number of waveform points must be less than 1,000,000,000 or an error
            occurs and only 999,999,999 bytes of data are sent. When the data format is
            WORD and streaming is off, the number of waveform points must be less than
            500,000,000 or an error occurs and only 499,999,999 words of data are sent.
            (c.f. programmers guide)
            """
            if waveform_format == "WORD":
                max_num_points = 499999999
            else:
                max_num_points = 999999999

        return max_num_points

    def set_acquisition(self, interpolation=0, acquisition_mode="RTIMe", num_segments=1):
        """
        Sets the parameters for acquisition, mainly the mode and (in case of segmented mode) the number of segments.
        c.f. programmers guide pp.203
        :param interpolation: turns the sin(x)/x interpolation filter on (1) or off (0) when the oscilloscope is in one
                              of the real time sampling modes. You can also specify the 1, 2, 4, 8, or 16 point Sin(x)/x
                              interpolation ratios using INT1, INT2, INT4, INT8, or INT16. When ON, the number of
                              interpolation points is automatically determined.
        :param acquisition_mode: RTIMe / SEGMented, for other modes refer to the programmers guide pp.215
        :return:
        """

        # Adjust sin(x)/x interpolation
        self.send_command_and_query(":ACQuire:INTerpolate {}".format(interpolation))

        # Set the acquisition mode
        self.send_command_and_query(":ACQuire:MODE {}".format(acquisition_mode))

        if "SEGM" in acquisition_mode:
            # set the number of segments in acquisition mode
            self.send_command_and_query(":ACQuire:SEGMented:COUNt {}".format(num_segments))

    def acquire_data_polling(self, poll_time=0.005):
        """
        Acquires data in polling mode, i.e. using the :SINGLE command in conjunction with polling of the :PDER? request
        c.f. programming guide pp.188
        :param poll_time: wait time between successive polls
        :return:
        """

        # The :SINGle command causes the oscilloscope to make a single acquisition when the next trigger event occurs.
        self.send_command("*CLS;:SINGle")

        # The :PDER? query reads the Processing Done Event Register and returns 1 or 0. After the Processing Done Event
        # Register is read, the register is cleared. The returned value 1 indicates indicates that all math and
        # measurements are complete and 0 indicates they are not complete. :PDER? is non-blocking.
        ProcDone = int(self.send_query(":PDER?"))
        while ProcDone == 0:
            ProcDone = int(self.send_query(":PDER?"))
            time.sleep(poll_time)

    def acquire_data_blocking(self, acquisition_time_out=1, global_time_out=10):
        """
        Acquires data in blocking mode, i.e. using :DIGITIZE in conjunction with *OPC? request. The OPC register is set
        as soon as the acquisition is ended. DIGITIZE is blocking, i.e. during its runtime no other command are executed
        by the oscilloscope. If the osiclloscope does not receive a trigger, you need to clear the communications to
        proceed, which is done automatically after the acquisition_time_out.
        c.f. programing guide pp.186
        :param acquisition_time_out: time out in [s] after which the communication interface is reset
        :param global_time_out: global time out [s] that is reset after acquisition
        :return:
        """

        self.instr.timeout = acquisition_time_out
        _logger.debug("Timeout was set to {} s for acquisition in blocking mode.".format(acquisition_time_out))

        try:
            # Acquire the signal(s) with :DIGItize (blocking) and wait
            # until *OPC? comes back with a one.
            self.send_query(":DIGitize;*OPC?")
            _logger.debug("Signal was acquired.")
            _logger.debug("Timeout was reset to global timeout of {} s.".format(global_time_out))
            self.instr.timeout = global_time_out
        except Exception:
            _logger.warning("The acquisition timed out, most likely due to no trigger or improper setup causing no " "trigger. Clearing the communication interface.")

            _logger.debug("Timeout was reset to global timeout of {} s.".format(global_time_out))
            self.instr.timeout = global_time_out
            self.clear_communication()

    def clear_communication(self):
        """
        Clears the communication interface
        :return:
        """
        # Clear communications interface
        self.instr.clear()
        _logger.info("Communication interface is cleared.")

    def close_unit(self):
        """
        Clears the communication interface and closes the connection to the scope.
        :return:
        """
        # Clear communications interface
        self.clear_communication()

        # Close communications interface
        self.instr.close()
        _logger.info("Communication interface is closed.")

    def close(self):
        """
        Close the scope. For compatibility with the measurement script.
        :return:
        """
        self.close_unit()
