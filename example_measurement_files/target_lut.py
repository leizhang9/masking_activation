import logging
import serial
import sys
import numpy as np
import time
import random

from attack.targets.CW305 import CW305
from attack.targets.TargetBase import _TargetBase
from attack.helper.utils import JSONutils as jsonutils
from serial_test_auto_input_gen import wishbone


class TargetControl(_TargetBase):
    """
    Template configuration for the CW305
    """

    def __init__(
        self,
        port,
        baudrate=9216, #my baudrate, 
        bytesize=8,
        parity="E",
        stopbits=1,
        configfile=None,
        config=[],
    ):
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
            self.wb = wishbone(port, baudrate)
            logging.info(
                "Serial connection to port %s successfully established." % port
            )
        except serial.SerialException as e:
            logging.warning(
                "Port %s not found, serial connection could not be established." % port
            )
            logging.warning(e)
            self.wb = None

        if jsonutils.json_try_access(config, ["experiment", "prng seed"], default=None):
            self.rng = np.random.default_rng(
                jsonutils.json_try_access(config, ["experiment", "prng seed"])
            )
        else:
            self.rng = np.random.default_rng()

        self.byteorder = "little"
        self.lut_size = 64
        return

    def __del__(self):
        """
        Serial connection is closed upon deleting of object
        :return:
        """
        try:
            self.wb.close()
            logging.info("Serial connection successfully closed.")
        except AttributeError:
            logging.warning(
                "Tried to close serial connection, but no connection was existent."
            )
        return

    # don't have to modify
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
            logging.info("CW305 successfully configures using bitstream %s" % filename)
        except Exception:
            logging.warning("CW305 could not be configured.")

        # set the clock frequency and configure the PLL
        # set value for clock divider
        # Register 4: Divider M (1 Byte)
        cw.pll.cdce906write(4, 3)

        # Register 5: Divider N (lower 8 bit)
        cw.pll.cdce906write(5, 25)

        # Register 6: Divider N and some other configs
        # Bit 7: PLL1 fvco selection
        # Bit 6: PLL2 fvco selection
        # Bit 5: PLL3 fvco selection
        # Bit 4-1: upper 4 bit of divider N
        # Bit 0: PLL2 Ref Dev M
        cw.pll.cdce906write(6, 0)

        # Register 10: PLL selection for divider P1 and some other config that is not needed
        # Bit 7-5: PLL selection -> 010 connect PLL2 with P1
        # Bit 4-0: Set to default values 0
        cw.pll.cdce906write(10, 64)

        # Register 14: divider P1
        # Bit 7: Reserved
        # Bit 6-0: value
        divider = 100000000 / config["target"]["fclk [Hz]"]
        if np.abs(divider - np.floor(divider)) != 0:
            logging.info("Could not set clock divider P1 to generate clock frequency!")
            sys.exit(0)
        divider = int(divider)
        cw.pll.cdce906write(14, divider)

        # Register 20: Output config Y1 (provide PLL2 frequency to FPGA Pin N13)
        # Bit 7: Reserved
        # Bit 6: invert output
        # Bit 5-4: Slew rate -> 11 (default)
        # Bit 3: Enable/Disable output  -> 1 (enable)
        # Bit 2-0: Output divider slection -> 001 (P1 = output divider of PLL2)
        cw.pll.cdce906write(20, 57)

        logging.info("Clock on N13 configured to %dMHz" % (100 / divider))

        divider = jsonutils.json_try_access(config, ["target", "fclk2 [Hz]"], default=0)
        if np.abs(divider - np.floor(divider)) != 0:
            logging.info("Could not set clock divider P3 to generate clock frequency!")
            sys.exit(0)
        divider = int(divider)
        if divider > 0:
            # Register 16: divider P3
            # Bit 7: Reserved
            # Bit 6-0: value
            cw.pll.cdce906write(16, divider)

            # Register 23: Output config Y1 (provide PLL2 frequency to FPGA Pin E12)
            # Bit 7: Reserved
            # Bit 6: invert output
            # Bit 5-4: Slew rate -> 11 (default)
            # Bit 3: Enable/Disable output  -> 1 (enable)
            # Bit 2-0: Output divider slection -> 011 (P3 = output divider of PLL2)
            cw.pll.cdce906write(23, 59)

            logging.info("Clock on E12 configured to %dMHz" % (100 / divider))

        # --- Settings for the reference frequency via the SMA Pin X6 ---
        if config["scope"]["clock"]["use_external"]:
            # Register 11: PLL selection for divider P2 + P3 and some other config that is not needed
            # Bit 7-6: input signal source -> 00
            # Bit 5-3: P3 PLL Selection -> 010
            # Bit 2-0: P2 PLL Selection -> 010
            cw.pll.cdce906write(11, 18)

            divider = int(
                100000000 / config["scope"]["clock"]["external clock frequency"]
            )
            if np.abs(divider - np.floor(divider)) != 0:
                logging.info("Could not set clock divider for external clock!")
                sys.exit(0)
            divider = int(divider)

            # Register 15: divider P2
            # Bit 7: Reserved
            # Bit 6-0: value
            cw.pll.cdce906write(15, divider)

            # Register 19: Output config Y0 (provide PLL2 frequency to X6 SMA)
            # Bit 7: Reserved
            # Bit 6: invert output
            # Bit 5-4: Slew rate -> 11 (default)
            # Bit 3: Enable/Disable output  -> 1 (enable)
            # Bit 2-0: Output divider slection -> 010 (P2 = output divider of PLL2)
            cw.pll.cdce906write(19, 58)

            logging.info(
                "External clock frequency configured to %dMHz" % (100 / divider)
            )

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

    # to modify  load data to fpga before measurement happens.  in my case, load input of lut. 1st trace should be with fixed input
    def load_data(self, config=[], trace=0):
        """
        Load/modify data on the device before the next execution of the operation under attack.
        E.g. new plaintext, key, mas or anything else you need to pass, e.g. number of an element you want to
        activate, a fixed input, ...
        :param config: dictionary with the configuration details
        :param trace: id of the trace that is currently measured
        :return: list of different input_data
        """

        if trace == 0:
            input = 30
            rnd = random.randint(0, self.lut_size)
            x1 = input - rnd
            x1 = x1 & (2**8 - 1)
            self.wb.write_multiple(0x40000000, [x1, rnd])  # changed interface

            d = self.wb.read_multiple(0x40000000, 2)
            if not np.allclose([x1, rnd], d):
                logging.warning("Error loading input and rnd!")
            else:
                logging.info("Input and rnd loaded successfully!")
            
        else:
            random_input = random.randint(0, self.lut_size)
            input = random.choice([30, random_input])
            rnd = random.randint(0, self.lut_size)
            x1 = input - rnd
            x1 = x1 & (2**8 - 1)
            self.wb.write_multiple(0x40000000, [x1, rnd])  # changed interface

            d = self.wb.read_multiple(0x40000000, 2)
            if not np.allclose([x1, rnd], d):
                logging.warning("Error loading input and rnd!")
            else:
                logging.info("Input and rnd loaded successfully!")

        input = np.array([input])
        rnd = np.array([rnd])
        return [input, rnd]

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
        # start inference
        self.wb.write(0x20000000, 1)
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