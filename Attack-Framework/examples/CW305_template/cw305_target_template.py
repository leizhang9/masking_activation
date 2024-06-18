import logging
import serial
import sys
import numpy as np

from attack.targets.CW305 import CW305
from attack.targets.TargetBase import _TargetBase

_logger = logging.getLogger(__name__)


class TargetControl(_TargetBase):
    """
    Template configuration for the CW305
    """

    def __init__(self, port, baudrate=115200, bytesize=8, parity="E", stopbits=1, configfile=None, config=[]):
        """
        Target is initialized with a serial connection and configured (optional)
        :param port: e.g. '/dev/ttyUSB0'
        :param baudrate: baudrate [Baud]
        :param bytesize: bytesize of the serial connection
        :param parity: bytesize of the serial connection
        :param stopbits: number of the serial connection
        :param configfile: string with a filepath to the file used to configure the device (.elf/.bit/...)
        :param config: dictionary with the configuration details
        :return:
        """

        # Try to setup a serial connection
        try:
            self._serial = serial.Serial(port, baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits)
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            _logger.info("Serial connection to port %s successfully established." % port)
        except serial.SerialException as e:
            _logger.warning("Port %s not found, serial connection could not be established." % port)
            _logger.warning(e)
            self._serial = None

        """
        Add here class variables that are needed for your implementation
        """

        return

    def __del__(self):
        """
        Serial connection is closed upon deleting of object
        :return:
        """
        try:
            self._serial.close()
            _logger.info("Serial connection successfully closed.")
        except AttributeError:
            _logger.warning("Tried to close serial connection, but no connection was existent.")
        return

    def configure_device(self, filename=None, config=[]):
        """
        Configure the device e.g. by programming an .elf to uC or sending an bitstream to the FPGA.
        :param filename: filename with the file that is used to configure the device
        :param config: dictionary with the configuration details
        :return:
        """

        # generate a object of the cw305 class
        cw = CW305.CW305()

        # load bitstream
        try:
            # connect to the Board and program the FPGA with the given bit-file
            cw.con(bsfile=filename, force=True)
            _logger.info("CW305 successfully configures using bitstream %s" % filename)
        except Exception:
            _logger.warning("CW305 could not be configured.")

        # set the clock frequency and configure the PLL
        # set value for clock divider
        divider = 100000000 / config["target"]["fclk [Hz]"]
        if np.abs(divider - np.floor(divider)) != 0:
            _logger.info("Could not set clock divider to generate clock frequency!")
            sys.exit(0)
        divider = int(divider)
        # set the frequency of the PLL1 to 100MHz (which is connected to Pin N13)
        # NOTE: Chipwhisperer starts enumerating the PLLs at 0, i.e., PLL1 corresponds to PLL2 of the CDCE906!
        cw.findParam(["PLL Settings", "CLK-N13 (FGPA Pin N13)", "PLL1 Frequency"]).setValue(100000000)
        # enable the clock on Pin N13
        cw.findParam(["PLL Settings", "CLK-N13 (FGPA Pin N13)", "CLK-N13 Enabled"]).setValue(True)
        # setup divider P2 (c.f. page 18 CDCE906 Manual)
        cw.pll.cdce906write(15, divider)
        # connect divider P2 to PLL
        cw.pll.cdce906write(20, 58)

        _logger.info("Clock configured to %dMHz" % (100 / divider))

        # --- Settings for the reference frequency via the SMA Pin X6 ---
        if config["scope"]["clock"]["use_external"]:
            # set value for clock divider
            divider = int(100000000 / config["scope"]["clock"]["external clock frequency"])
            # setup divider P3 (c.f. page 18 CDCE906 Manual)
            cw.pll.cdce906write(16, divider)
            # connect divider P3 to PLL
            cw.pll.cdce906write(11, 18)
            # connect the SMA Pin X6 with the divider P3
            cw.pll.cdce906write(19, 59)

            _logger.info("External clock frequency configured to %dMHz" % (100 / divider))

        # close the connection to the CW305
        cw.dis()
        cw.close()

        return

    def provide_info(self):
        """
        Provide info about the target device / implementation, e.g. by reading back the serial number, information
        provided by the device itself
        :return:
        """
        info = ""
        return info

    def load_data(self, config=[], trace=0):
        """
        Load/modify data on the device before the next execution of the operation under attack.
        E.g. new plaintext, key, mas or anything else you need to pass, e.g. number of an element you want to
        activate, a fixed input, ...
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: list of different input_data
        """

        return

    def execute_trigger(self, config=[], trace=0, repetition=0):
        """
        Start the execution of the operation under attack. A trigger is supposed to be output. Additional parameters can
        be handed over to the trigger function (optional)
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :param repetition: the index of the repetition, if several measurements shall be taken for the same input. Can
               be used to avoid manipulating triggers between different triggers
        :return: list of different trigger_data
        """

        return []

    def read_data(self, config=[], trace=0):
        """
        Read back data after the execution of the operation under attack is finished.
        E.g. get the ciphertext
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: list of different output_data
        """

        return []
