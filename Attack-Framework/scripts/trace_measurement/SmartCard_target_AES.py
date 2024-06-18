import logging
from attack.targets.TargetBase import _TargetBase
import random
from smartcard.CardRequest import CardRequest
from smartcard.CardConnection import CardConnection
from smartcard.CardType import ATRCardType
from smartcard.util import toBytes, bs2hl, hl2bs
import sys
import time

_logger = logging.getLogger(__name__)


class TargetControl(_TargetBase):
    """
    Target class for the smart card emulator running a toy AES (for SIKA / SmartCard Lab)
    """

    def __init__(self, port=None, baudrate=115200, bytesize=8, parity="N", stopbits=1, configfile=None):
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
        # Try to setup a connection to the smart card

        # detect the smart card based on the content of the ATR (card-centric approach)
        _logger.info("Initializing card connection...")
        try:
            cardtype = ATRCardType(toBytes("3B 90 11 00"))
            cardrequest = CardRequest(timeout=5, cardType=cardtype)
            self.cardservice = cardrequest.waitforcard()
            _logger.info("Card connection established correctly")
        except BaseException:
            _logger.error("Timeout exceeded")
            _logger.error("Connection with smart card could not be established.")
            sys.exit(0)
        # connect to the card using T0 protocol.
        self.cardservice.connection.connect(CardConnection.T0_protocol)

        # define constants
        self.N = 3169092109
        self.d = 2439316869
        self.e = 65537
        self.errors = 0

        return

    def __del__(self):
        """
        Serial connection is closed upon deleting of object
        :return:
        """

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
        info = "TUEISEC Smart Card emulator"
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
        # generate a new random data vector
        input = [random.randint(0, 255) for x in range(16)]

        # send data to the card to be decrypted
        output = self.sc_decrypt(input)

        return [input, bs2hl(output)]

    def read_data(self, config=[], trace=0):
        """
        Read back data after the execution of the operation under attack is finished.
        E.g. get the ciphertext
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: list of different output_data
        """

        return []

    def sc_decrypt(self, input):
        _logger.debug("Decrypting")

        # format the command to be sent to the card:
        # format the command to be sent to the card:
        INPUT = [0x88, 0x10, 0, 0, len(input)] + input + [0x10]
        GET_RESPONSE = [0x88, 0xC0, 0x00, 0x00, 0x10]
        # send the commands and retrieve the responses
        # detecting a transmission error
        try:
            time.sleep(0.01)  # this can prevent the transmission error
            response, sw1, sw2 = self.cardservice.connection.transmit(INPUT)
            # This function doesn't terminate sometimes
            # wait and try again after a transmission error
        except Exception as exc:
            _logger.error(exc)
            response, sw1, sw2 = self.cardservice.connection.transmit(INPUT)

        response, sw1, sw2 = self.cardservice.connection.transmit(GET_RESPONSE)
        return hl2bs(response)
