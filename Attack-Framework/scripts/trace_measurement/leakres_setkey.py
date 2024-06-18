import logging
import random
import shlex
import subprocess

import target_STMF2
from attack.targets.TargetBase import _TargetBase

_logger = logging.getLogger(__name__)


class TargetControl(_TargetBase):
    def __init__(self, port, baudrate=115200, bytesize=8, parity="N", stopbits=1, configfile=None):
        """
        Target is initialized with a serial connection and configured (optional)
        :param port: e.g. '/dev/ttyUSB0'
        :param baudrate: baudrate [Baud]
        :param bytesize: bytesize of the serial connection
        :param parity: bytesize of the serial connection
        :param stopbits: number of the serial connection
        :param configfile: string with a filepath to the file used to configure the device (.elf/.bit/...)
        :return:
        """
        # initialize
        super().__init__(port, baudrate, bytesize, parity, stopbits, configfile)

        # import functions from a general target implementation
        self.functions = target_STMF2.TargetCommunication(self._serial)

    def configure_device(self, filename=None):
        """
        Configure the device e.g. by programming an .elf to uC or sending an bitstream to the FPGA.
        :param filename: filename with the file that is used to configure the device
        :return:
        """
        if filename is not None and ".elf" in filename:
            output = subprocess.Popen(shlex.split('openocd -f cw308_STM32F2.cfg -c "program %s verify reset" -c shutdown' % filename), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            #
            stdout = output.stdout.read().decode("utf-8").split("\n")

            output.communicate()
            if output.returncode == 0:
                _logger.info("Device successfully configured with file '%s'." % filename)
                # debug: display stdout
                for i in range(0, len(stdout)):
                    _logger.debug(stdout[i])

            else:
                # if an error occurred, displya warning
                _logger.warning("Something went wrong during configuration file '%s'." % filename)
                for i in range(0, len(stdout)):
                    _logger.warning(stdout[i])
        else:
            _logger.info("Device not configured, no valid path to configuration file is provided.")
        return

    def provide_info(self):
        """
        Provide info about the target device / implementation, e.g. by reading back the serial number, information
        provided by the device itself
        :return:
        """
        info = self.functions.get_info()
        return info

    def load_data(self, config=[], trace=0):
        """
        Load/modify data on the device before the next execution of the operation under attack.
        E.g. new plaintext, key, mask. Data can be anything you need to pass, e.g. number of an element you want to
        activate, a fixed input, ...
        :param data: list of elements needed by the underlying functions (optional)
        :return:
        """
        input_data = []
        return input_data

    def execute_trigger(self, config=[], trace=0, repetition=0):
        """
        Start the execution of the operation under attack. A trigger is supposed to be output. Additional parameters can
        be handed over to the trigger function (optional)
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :param repetition: the index of the repetition, if several measurements shall be taken for the same input. Can
               be used to avoid manipulating triggers between different triggers
        :return: First entry: key that is written
        """

        if repetition == 0:
            # generate a random key only for the first repetition and assign it to the class
            self.key_data = [random.randint(0, 255) for x in range(16)]

        _logger.debug("Loading Key")
        _logger.debug(str(self.key_data))

        # set key
        self.functions.set_key_128(bytes(self.key_data))

        return [self.key_data]

    def read_data(self, config=[], trace=0, repetition=0):
        """
        Checks whether the key was correctly written
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: empty list
        """
        if config["experiment"]["check result"]:
            check_key = self.functions.get_key_128()

            if list(check_key) == self.key_data:
                _logger.debug("Key was correctly written")
            else:
                _logger.debug("Something is strange...")

        output_data = []

        return output_data
