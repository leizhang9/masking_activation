import vxi11
import numpy as np
import logging

_logger = logging.getLogger(__name__)


class Keysight_Trueform:
    """
    This class provides an interface to Keysight’s Trueform arbitrary
    waveform generatores. Note that at this point in time, its
    functionality is far from complete: it is focussed on the ‘arbitrary
    waveform’ part, so basic signal generation (e.g. sine, rectangle)
    is missing completely for now.

    This class has so far only been tested on the 33622A and not on the
    33500B models (as these don’t have the arbitrary waveform option).
    """

    _instr = None
    max_log_length = 100

    def __init__(self, lan_address="TCPIP::A-33622A-00922.sec.ei.tum.de::inst0::INSTR", reset=True):
        """
        Given a VXI-11 LAN address, connect to a Keysight Series 33600A
        waveform generator and optionally reset it to its default state.
        """

        self._instr_open(lan_address, reset)

    def __exit__(self):
        self._instr_close()

    def load_arb(self, waveform, sample_rate, channel=1, waveform_name="unnamed"):
        """
        Load an arbitrary waveform into the instrument and select it. The
        waveform must be provided as a (NumPy) array of voltages, the
        sample rate must be an integer (in Sa/s).

        Note that trying to load a waveform with the same name as a
        previously loaded one will result in an error. To reuse a
        waveform name, the signal memory has to be cleared first.
        """

        # DAC value corresponding to the peak voltage
        DAC_LIMIT = 32_767

        waveform_min, waveform_max = np.min(waveform), np.max(waveform)
        max_voltage = np.max(np.abs(waveform))
        # Normalise waveform, convert to DAC samples as 16-bit big-endian
        # integers
        waveform = np.array(np.around(waveform / max_voltage * DAC_LIMIT), dtype=">i2")
        waveform_bytes = waveform.tobytes()

        # Build a binary block with the waveform data, starting with '#',
        # followed by the length of the length, the binary data length
        # and the data itself
        binary_block = str(len(waveform_bytes))
        binary_block = ("#" + str(len(binary_block)) + binary_block).encode("utf-8")
        binary_block += waveform_bytes

        # Send the waveform data with a raw command
        command = "SOURCE{}:DATA:ARB1:DAC {}, ".format(channel, waveform_name)
        self._send_raw_command(command.encode("utf-8") + binary_block)

        # Select the freshly loaded waveform
        self._send_command("SOURCE{}:FUNCTION:ARB {}".format(channel, waveform_name))
        self._send_command("SOURCE{}:FUNCTION ARB".format(channel))

        # Set sample rate
        self._send_command("SOURCE{}:FUNCTION:ARB:SRATE {:f}".format(channel, sample_rate))

        # Set voltage range
        self._send_command("SOURCE{}:VOLTAGE:HIGH {:f}".format(channel, waveform_max))
        self._send_command("SOURCE{}:VOLTAGE:LOW {:f}".format(channel, waveform_min))

    def get_arb_name(self, channel=1):
        """
        Query the currently active arbitrary waveform name used for a
        channel. The quotes enclosing the name are stripped
        automatically.

        Note: a returned waveform name does not necessarily mean that
        this waveform is currently selected. The waveform generator could
        also be e.g. outputting a sine signal and not use the arbitrary
        waveform at all. Check if get_function() is 'ARB' if you want to
        be sure.
        """
        name = self._send_query("SOURCE{}:FUNCTION:ARB?".format(channel))
        if not name.startswith('"') or not name.endswith('"'):
            raise ValueError('Expected a waveform name enclosed in quotes, received "{}".'.format(name))

        return name[1:-1]

    def get_function(self, channel=1):
        """
        Query the currently selected function for a channel. Will return
        one of 'SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS',
        'ARB', 'DC'.
        """
        return self._send_query("SOURCE{}:FUNCTION?".format(channel))

    def clear_signal_memory(self, channel=1):
        """
        Clear the volatile memory to allow storing new waveform data.
        """
        self._send_command("SOURCE{}:DATA:VOLATILE:CLEAR".format(channel))

    def set_output_load(self, load=50, channel=1):
        """
        Select the output load impedance. None or np.inf select high-
        impedance mode.
        """
        if load is None or np.isinf(load):
            self._send_command("OUTPUT{}:LOAD INFINITY".format(channel))
        else:
            self._send_command("OUTPUT{}:LOAD {}".format(channel, load))

    def enable_output(self, channel=1):
        """
        Enable an output channel.
        """
        self._send_command("OUTPUT{} ON".format(channel))

    def disable_output(self, channel=1):
        """
        Disable an output channel.
        """
        self._send_command("OUTPUT{} OFF".format(channel))

    def set_trigger_source(self, source, channel=1):
        """
        Set the trigger source to one of 'immediate', 'external',
        'timer', or 'bus'
        """
        self._send_command("TRIGGER{}:SOURCE {}".format(channel, source))

    def configure_trigger_out(self, enabled=True, source_channel=1, level=3.3, falling_edge=False):
        """
        Configure the trigger output (located on the back of the
        instrument).
        """
        if not enabled:
            self._send_command("OUTPUT:TRIGGER OFF")
        else:
            self._send_command("OUTPUT:TRIGGER:SOURCE CH{}".format(source_channel))

            if falling_edge:
                self._send_command("OUTPUT:TRIGGER:SLOPE NEGATIVE")
            else:
                self._send_command("OUTPUT:TRIGGER:SLOPE POSITIVE")

            self._send_command("TRIGGER:LEVEL {:f}".format(level))

            self._send_command("OUTPUT:TRIGGER ON")

    def triggered_burst(self, cycles=1, channel=1):
        """
        Configure triggered burst mode. Currently, only the number of
        burst cycles can be configured, burst period (for internal
        trigger) and burst phase are not supported.
        """
        self._send_command("SOURCE{}:BURST:MODE TRIGGERED".format(channel))
        self._send_command("SOURCE{}:BURST:NCYCLES {}".format(channel, cycles))
        self._send_command("SOURCE{}:BURST:STATE ON".format(channel))

    def trigger(self):
        """
        Issue a bus trigger. Only effective if the trigger source has
        been set to 'bus'.
        """
        self._send_command("*TRG")

    def _instr_open(self, lan_address, reset):
        """
        Establish a connection to a VISA instrument using the VXI-11 LAN
        protocol and log information about the device, given a VISA
        instrument address. The instrument is reset to its default set-up
        immediately after a successful connection if the `reset`
        parameter is set to `True`.
        """
        self._instr = vxi11.Instrument(lan_address)
        try:
            # Clear status
            self._send_command("*CLS")

            # Query instrument identifier
            response = self._send_query("*IDN?")
            _logger.info("Connected to {}.".format(response))

            if reset:
                # Load the default setup
                _logger.info("Resetting to default set-up.")
                self._send_command("*RST")

            _logger.info("Waveform generator ready.")

        except Exception as e:
            _logger.error("Connection to the waveform generator could not be established! You were trying to connect to {}.".format(lan_address))
            raise e

    def _instr_close(self):
        """
        Clear the communication interface and close the connection to the
        waveform generator.
        """
        # Clear and close communications interface
        self._instr.clear()
        self._instr.close()
        _logger.info("Communication interface is closed.")

    def _check_communication_errors(self):
        """
        Fetch an error from the SCPI error queue. If an error occurred,
        log it and raise an exception.
        """
        error_string = self._instr.ask(":SYST:ERR?")
        if error_string:
            if error_string != '+0,"No error"':
                _logger.error(error_string)
                raise Exception("Communication error: '{}'.".format(error_string))
        else:
            # :SYST:ERR? should always return string
            _logger.error(":SYST:ERR? returned nothing")
            raise Exception("Could not query instrument error status.")

    def _send_command(self, command):
        """
        Send a command string to the instrument and check for errors.
        """
        _logger.debug(self._ellipsise("Sending command '{}'.".format(command)))
        self._instr.write(command)
        self._check_communication_errors()

    def _send_raw_command(self, command):
        """
        Send a command consisting of raw bytes and check for errors.
        """
        _logger.debug(self._ellipsise("Sending raw command {}.".format(command)))
        self._instr.write_raw(command)
        self._check_communication_errors()

    def _send_query(self, query):
        """
        Send a query, check for errors and return the query result as a
        string.
        """
        _logger.debug("Sending query '{}'.".format(query))
        result = self._instr.ask("%s" % query)
        self._check_communication_errors()
        _logger.debug(self._ellipsise("Query '{}' returned '{}'.".format(query, result)))
        return result

    def _ellipsise(self, message):
        """
        Ellipsise a string if it is longer than self.max_log_length.
        """
        if len(message) > self.max_log_length:
            return message[0 : self.max_log_length - 11] + " […] " + message[-6:]
        return message
