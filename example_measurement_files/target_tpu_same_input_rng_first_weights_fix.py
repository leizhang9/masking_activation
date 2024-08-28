import logging
import serial
import sys
import numpy as np
import time

from attack.targets.CW305 import CW305
from attack.targets.TargetBase import _TargetBase
from attack.helper.utils import JSONutils as jsonutils
from serial_test_auto_input_gen import wishbone
from xoroshiro128plus import xoroshiro128plus


class TargetControl(_TargetBase):
    """
    Template configuration for the CW305
    """

    def __init__(
        self,
        port,
        baudrate=921600, #my baudrate
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
        self.n_data = jsonutils.json_try_access(config, ["experiment", "n_data"], default=1)
        self.weights = np.zeros(self.n_data, dtype=np.uint32)
        r = self.rng.integers(0, 2**8, 1, dtype=np.uint32)
        for i in range(0, 4):
            self.weights[0] = self.weights[0] | (r << (i * 8))

        self.rng_input_seed = self.rng.integers(0, 2**64, 2, dtype=np.uint64)
        self.rng_weight_seed = np.zeros(2, dtype=np.uint64)

        self.xoro_input = xoroshiro128plus(self.rng_input_seed[0], self.rng_input_seed[1])

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
            self.init_rngs(self.rng_input_seed, self.rng_weight_seed)
            self.load_lengths(self.n_data, self.n_data)
            self.load_weights()
            data = self.rng.integers(0, 2**8, self.n_data, dtype=np.uint32)
            for i in range(1, 4):
                data = data | (data << (i * 8))
            self.load_input(data)
            
        else:
            data = np.zeros(self.n_data, dtype=np.uint64)
            data[0] = self.xoro_input.state_s0 + self.xoro_input.state_s1
            data[1:] = self.xoro_input.random(self.n_data - 1)
            self.xoro_input.random(1)
            data = np.right_shift(data, np.uint64(32))
            data.astype(np.uint32)
            data = data & 0xff000000
            for i in range(0, 4):
                data = data | (data >> (i * 8))

            if (trace % 100) == 0:
                dr = []
                for i in range(0, self.n_data):
                    dr.append(self.wb.read_multiple_big(0x60000000 + i, 1)[0])
                if not np.allclose(dr, data):
                    logging.warning("Missmatch between expected data and received data.")
                    print(data)
                    print(dr)
                else:
                    logging.info("FPGA and PC data synchronous.")

        weights = self.weights
            
        return [weights, data]

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
    
    
    def load_lengths(self, weight_length, input_length):
        self.wb.write(0x40000000, weight_length)
        self.wb.write(0x40000001, input_length)
        d = self.wb.read_multiple(0x40000000, 2)
        
        if not np.allclose([weight_length, input_length], d):
            logging.warning("Error loading length parameters!")
        else:
            logging.info("Lengths loaded successfully!")
        
        return
    
    def load_weights(self):
        write_data = []
        for i in range(0, len(self.weights)):
            write_data.append(self.weights[i].item())
            self.wb.write_multiple(0x50000000 + i, [write_data[i]])
        
        return

    def load_input(self, data):
        write_data = []
        dr = []
        for i in range(0, len(data)):
            write_data.append(data[i].item())
            self.wb.write_multiple(0x60000000 + i, [write_data[i]])
            dr.append(self.wb.read_multiple_big(0x60000000 + i, 1)[0])
        
        if not np.allclose(write_data, dr):
            logging.warning("Error loading input data!")
        
        
        return np.array(dr, dtype=np.uint32)
    
    def init_rngs(self, seed_input, seed_weight):
        data = np.zeros(8, dtype=np.uint32)
        data[0] = np.uint32(seed_input[0] & np.uint64(2**32 - 1))
        data[1] = np.uint32((seed_input[0] >> np.uint64(32)) & np.uint64(2**32 - 1))
        data[2] = np.uint32(seed_input[1] & np.uint64(2**32 - 1))
        data[3] = np.uint32((seed_input[1] >> np.uint64(32)) & np.uint64(2**32 - 1))
        data[4] = np.uint32(seed_weight[0] & np.uint64(2**32 - 1))
        data[5] = np.uint32((seed_weight[0] >> np.uint64(32)) & np.uint64(2**32 - 1))
        data[6] = np.uint32(seed_weight[1] & np.uint64(2**32 - 1))
        data[7] = np.uint32((seed_weight[1] >> np.uint64(32)) & np.uint64(2**32 - 1))
        write_data = []
        for i in range(0, len(data)):
            write_data.append(data[i].item())
        
        self.wb.write_multiple(0x40000002, write_data)
        d = self.wb.read_multiple(0x40000002, 8)
        if not np.allclose(d, write_data):
            logging.warning("Error loading seed data!")
        else:
            self.wb.write(0x70000000, 1)
            self.wb.write(0x80000000, 1)

        return