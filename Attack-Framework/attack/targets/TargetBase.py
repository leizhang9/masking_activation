import serial
import logging

_logger = logging.getLogger(__name__)


class _TargetBase(object):
    """
    Base class for targets of the TUEISEC-AttackFramework
    """

    def __init__(self, port, baudrate=115200, bytesize=8, parity="N", stopbits=1, configfile=None, config=[]):
        """
        Target is initialized with a serial connection
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
            _logger.info("Serial connection to port %s successfully established." % port)
        except serial.SerialException:
            _logger.warning("Port %s not found, serial connection could not be established." % port)
            self._serial = None

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
        return

    def provide_info(self):
        """
        Provide info about the target device / implementation, e.g. by reading back the serial number, information
        provided by the device itself
        :return:
        """
        info = None
        return info

    def load_data(self, config=[], trace=0):
        """
        Load/modify data on the device before the next execution of the operation under attack.
        E.g. new plaintext, key, mask or anything else you need to pass, e.g. number of an element you want to
        activate, a fixed input, ...
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: list of different input_data
        """

        return []

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
