# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2016, NewAE Technology Inc
# All rights reserved.
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
# ==========================================================================
import logging
import time
import usb.backend.libusb0 as libusb0
import usb.core
import usb.util
import math
from threading import Condition, Thread

_logger = logging.getLogger(__name__)


def packuint32(data):
    """Converts a 32-bit integer into format expected by USB firmware"""

    return [data & 0xFF, (data >> 8) & 0xFF, (data >> 16) & 0xFF, (data >> 24) & 0xFF]


def unpackuint32(buf):
    """"Converts an array into a 32-bit integer"""

    pint = buf[0]
    pint |= buf[1] << 8
    pint |= buf[2] << 16
    pint |= buf[3] << 24
    return pint


def packuint16(data):
    """Converts a 16-bit integer into format expected by USB firmware"""

    return [data & 0xFF, (data >> 8) & 0xFF, (data >> 16) & 0xFF, (data >> 24) & 0xFF]


# List of all NewAE PID's
NEWAE_VID = 0x2B3E
NEWAE_PIDS = {
    0xC305: {"name": "CW305 Artix FPGA Board", "fwver": [0, 11]},  # hardcoded
}


class NAEUSB(object):
    """
    USB Interface for NewAE Products with Custom USB Firmware
    """

    CMD_FW_VERSION = 0x17

    CMD_READMEM_BULK = 0x10
    CMD_WRITEMEM_BULK = 0x11
    CMD_READMEM_CTRL = 0x12
    CMD_WRITEMEM_CTRL = 0x13
    CMD_MEMSTREAM = 0x14

    stream = False

    # TODO: make this better
    fwversion_latest = [0, 11]

    def __init__(self):
        self._usbdev = None

    def get_possible_devices(self, idProduct):
        """
        Get a list of matching devices being based a list of PIDs. Returns list of usbdev that match (or empty if none)
        """

        devlist = []

        for id in idProduct:
            try:
                # Connect to device (attempt #1)
                dev = list(usb.core.find(find_all=True, idVendor=0x2B3E, idProduct=id, backend=libusb0.get_backend()))
            except usb.core.NoBackendError:
                try:
                    # An error in the previous one is often caused by Windows 64-bit not detecting the correct library, attempt to force this with paths
                    # that often work so user isn't aware
                    dev = list(usb.core.find(find_all=True, idVendor=0x2B3E, idProduct=id, backend=libusb0.get_backend(find_library=lambda x: r"c:\Windows\System32\libusb0.dll")))
                except usb.core.NoBackendError:
                    raise IOError("Failed to find USB backend. Check libusb drivers installed, check for path issues on library, and check for 32 vs 64-bit issues.")
            # Found something
            if len(dev) > 0:
                devlist.extend(dev)

        return devlist

    def con(self, idProduct=[0xACE2], connect_to_first=False, serial_number=None):
        """
        Connect to device using default VID/PID
        """

        devlist = self.get_possible_devices(idProduct)
        snlist = [d.serial_number + " (" + d.product + ")\n" for d in devlist]
        snlist = "".join(snlist)

        if len(devlist) == 0:
            raise Warning("Failed to find USB Device")

        elif serial_number:
            dev = None
            for d in devlist:
                if d.serial_number == serial_number:
                    dev = d
                    break

            if dev is None:
                raise Warning("Failed to find USB device with S/N %s\n. Found S/N's:\n" + snlist)

        elif len(devlist) == 1:
            dev = devlist[0]

        else:
            if connect_to_first:
                dev = devlist[0]
            else:
                # User did not help us out - throw it in their face
                raise Warning("Found multiple potential USB devices. Please specify device to use. Possible S/Ns:\n" + snlist)
        try:
            dev.set_configuration(0)
            dev.set_configuration()
        except ValueError:
            raise IOError("NAEUSB: Could not configure USB device")

        # Get serial number
        try:
            # New calling syntax
            self.snum = usb.util.get_string(dev, index=3)

        except TypeError:
            # Old calling syntax
            self.snum = usb.util.get_string(dev, length=256, index=3)

        foundId = dev.idProduct

        if foundId in NEWAE_PIDS:
            name = NEWAE_PIDS[foundId]["name"]
            fw_latest = NEWAE_PIDS[foundId]["fwver"]
        else:
            name = "Unknown (PID = %04x)" % foundId
            fw_latest = [0, 0]

        _logger.info("Found %s, Serial Number = %s" % (name, self.snum))

        self._usbdev = dev
        self.rep = 0x81
        self.wep = 0x02
        self._timeout = 200

        fwver = self.readFwVersion()
        _logger.info("SAM3U Firmware version = %d.%d b%d" % (fwver[0], fwver[1], fwver[2]))

        latest = fwver[0] > fw_latest[0] or (fwver[0] == fw_latest[0] and fwver[1] >= fw_latest[1])
        if not latest:
            _logger.warning("Your firmware is outdated - latest is %d.%d" % (fw_latest[0], fw_latest[1]) + ". Suggested to update firmware, as you may experience errors")

        return foundId, self.snum

    def usbdev(self):
        if not self._usbdev:
            raise Warning("USB Device not found. Did you connect it first?")
        return self._usbdev

    def close(self):
        """Close USB connection."""
        try:
            usb.util.dispose_resources(self.usbdev())
        except usb.USBError as e:
            _logger.info("USB Failure calling dispose_resources: %s" % str(e))

    def readFwVersion(self):
        try:
            data = self.readCtrl(self.CMD_FW_VERSION, dlen=3)
            return data
        except usb.USBError:
            return [0, 0, 0]

    def sendCtrl(self, cmd, value=0, data=[]):
        """
        Send data over control endpoint
        """
        # Vendor-specific, OUT, interface control transfer
        return self.usbdev().ctrl_transfer(0x41, cmd, value, 0, data, timeout=self._timeout)

    def readCtrl(self, cmd, value=0, dlen=0):
        """
        Read data from control endpoint
        """
        # Vendor-specific, IN, interface control transfer
        return self.usbdev().ctrl_transfer(0xC1, cmd, value, 0, dlen, timeout=self._timeout)

    def cmdReadMem(self, addr, dlen):
        """
        Send command to read over external memory interface from FPGA. Automatically
        decides to use control-transfer or bulk-endpoint transfer based on data length.
        """

        if dlen < 48:
            cmd = self.CMD_READMEM_CTRL
        else:
            cmd = self.CMD_READMEM_BULK

        # ADDR/LEN written LSB first
        pload = packuint32(dlen)
        pload.extend(packuint32(addr))
        self.sendCtrl(cmd, data=pload)

        # Get data
        if cmd == self.CMD_READMEM_BULK:
            data = self.usbdev().read(self.rep, dlen, timeout=self._timeout)
        else:
            data = self.readCtrl(cmd, dlen=dlen)

        return data

    def cmdWriteMem(self, addr, data):
        """
        Send command to write memory over external memory interface to FPGA. Automatically
        decides to use control-transfer or bulk-endpoint transfer based on data length.
        """

        dlen = len(data)

        if dlen < 48:
            cmd = self.CMD_WRITEMEM_CTRL
        else:
            cmd = self.CMD_WRITEMEM_BULK

        # ADDR/LEN written LSB first
        pload = packuint32(dlen)
        pload.extend(packuint32(addr))

        if cmd == self.CMD_WRITEMEM_CTRL:
            pload.extend(data)

        self.sendCtrl(cmd, data=pload)

        # Get data
        if cmd == self.CMD_WRITEMEM_BULK:
            data = self.usbdev().write(self.wep, data, timeout=self._timeout)
        else:
            pass

        return data

    def cmdReadStream_getStatus(self):
        """
        Gets the status of the streaming mode capture, tells you samples left to stream out along
        with overflow buffer status. When an overflow occurs the samples left to stream goes to
        zero.

        samples_left_to_stream is number of samples not yet streamed out of buffer.
        overflow_lcoation is the value of samples_left_to_stream when a buffer overflow occured.
        unknown_overflow is a flag indicating if an overflow occured at an unknown time.

        Returns:
            Tuple indicating (samples_left_to_stream, overflow_location, unknown_overflow)
        """
        data = self.readCtrl(self.CMD_MEMSTREAM, dlen=9)

        status = data[0]
        samples_left_to_stream = unpackuint32(data[1:5])
        overflow_location = unpackuint32(data[5:9])

        if status == 0:
            unknown_overflow = False
        else:
            unknown_overflow = True

        return (samples_left_to_stream, overflow_location, unknown_overflow)

    def cmdReadStream_size_of_fpgablock(self):
        """Asks the hardware how many BYTES are read in one go from FPGA, which indicates where the sync
        bytes will be located. These sync bytes must be removed in post-processing."""
        return 4096

    def cmdReadStream_bufferSize(self, dlen):
        """
        Args:
            dlen: Number of samples to be requested (will be rounded to something else)

        Returns:
            Tuple: (Size of temporary buffer required, actual samples in buffer)
        """
        num_samplebytes = int(math.ceil(float(dlen) * 4 / 3))
        num_blocks = int(math.ceil(float(num_samplebytes) / 4096))
        num_totalbytes = num_samplebytes + num_blocks
        num_totalbytes = int(math.ceil(float(num_totalbytes) / 4096) * 4096)
        return (num_totalbytes, num_samplebytes)

    def initStreamModeCapture(self, dlen, dbuf_temp, timeout_ms=1000):
        # Enter streaming mode for requested number of samples
        if hasattr(self, "streamModeCaptureStream"):
            self.streamModeCaptureStream.join()
        self.sendCtrl(NAEUSB.CMD_MEMSTREAM, data=packuint32(dlen))
        self.streamModeCaptureStream = NAEUSB.StreamModeCaptureThread(self, dlen, dbuf_temp, timeout_ms)
        self.streamModeCaptureStream.start()

    def cmdReadStream_isDone(self):
        return self.streamModeCaptureStream.isAlive() == False

    def cmdReadStream(self):
        """
        Gets data acquired in streaming mode.
        initStreamModeCapture should be called first in order to make it work.
        """
        self.streamModeCaptureStream.join()

        # Flush input buffers in case anything was left
        try:
            self.usbdev().read(self.rep, 4096, timeout=10)
            self.usbdev().read(self.rep, 4096, timeout=10)
            self.usbdev().read(self.rep, 4096, timeout=10)
            self.usbdev().read(self.rep, 4096, timeout=10)
        except IOError:
            pass

        # Ensure stream mode disabled
        self.sendCtrl(NAEUSB.CMD_MEMSTREAM, data=packuint32(0))

        return self.streamModeCaptureStream.drx, self.streamModeCaptureStream.timeout

    def enterBootloader(self, forreal=False):
        """Erase the SAM3U contents, forcing bootloader mode. Does not screw around."""

        if forreal:
            self.sendCtrl(0x22, 3)

    def flushInput(self):
        """Dump all the crap left over"""
        try:
            # TODO: This probably isn't needed, and causes slow-downs on Mac OS X.
            self.usbdev().read(self.rep, 1000, timeout=0.010)
        except:
            pass

    class StreamModeCaptureThread(Thread):
        def __init__(self, serial, dlen, dbuf_temp, timeout_ms=2000):
            """
            Reads from the FIFO in streaming mode. Requires the FPGA to be previously configured into
            streaming mode and then arm'd, otherwise this may return incorrect information.

            Args:
                dlen: Number of samples to request.
                dbuf_temp: Temporary data buffer, must be of size cmdReadStream_bufferSize(dlen) or bad things happen
                timeout_ms: Timeout in ms to wait for stream to start, otherwise returns a zero-length buffer
            Returns:
                Tuple of (samples_per_block, total_bytes_rx)
            """
            Thread.__init__(self)
            self.dlen = dlen
            self.dbuf_temp = dbuf_temp
            self.timeout_ms = timeout_ms
            self.serial = serial
            self.timeout = False
            self.drx = 0

        def run(self):
            _logger.debug("Streaming: starting USB read")
            start = time.time()
            try:
                self.drx = self.serial.usbdev().read(self.serial.rep, self.dbuf_temp, timeout=self.timeout_ms)
            except IOError as e:
                _logger.warning("Streaming: USB stream read timed out")
            diff = time.time() - start
            _logger.debug("Streaming: Received %d bytes in time %.20f)" % (self.drx, diff))

            # while(self.drx < num_totalbytes):
            #    bytesread = self.serial.usbdev().read(self.serial.rep, buf, timeout=to)
            #    self.dbuf_temp[self.drx:self.drx+bytesread] = buf[:]
            #    self.drx += bytesread
            #    to = 50

            # # Get block size of samples, bytes per block
            # _, self.bsize_samples, self.bsize_bytes = self.serial._cmdReadStream_blockSizes(self.dlen)
            #
            # dlen = self.dlen
            # to = self.timeout_ms
            #
            # self.drx = 0
            #
            # start = time.time()
            # while dlen > 0:
            #     try:
            #         if dlen > 9216:
            #             bsize = self.bsize_bytes
            #         elif dlen >= 6122:
            #             bsize = 4096*3
            #         elif dlen >= 3072:
            #             bsize = 4096*2
            #         else:
            #             bsize = 4096
            #
            #         #Commented out normally for performance
            #         #_logger.debug("USB Read Request: %d bytes, %d samples left"%(bsize, dlen))
            #         diff = time.time() - start
            #         _logger.debug("Sending USB read request at %.20f" % diff)
            #
            #         #self.dbuf_temp[self.drx:(self.drx+bsize)] = (self.serial.usbdev().read(self.serial.rep, bsize, timeout=to))
            #         self.serial.usbdev().read(self.serial.rep, bsize, timeout=to)
            #     except IOError as e:
            #         self.timeout = True
            #         if self.drx == 0:
            #             _logger.debug("Timeout during stream mode with no data - assumed no trigger")
            #         else:
            #             _logger.debug("Timeout during stream mode after %d bytes" % self.drx)
            #         break
            #
            #     #once we have a block of data, quicker timeout is OK
            #     to = 50
            #
            #     dlen -= (bsize / 4) * 3
            #     self.drx += bsize


if __name__ == "__main__":
    from fpga import FPGA
    from serial import USART

    cwtestusb = NAEUSB()
    cwtestusb.con()

    # Connect required modules up here
    fpga = FPGA(cwtestusb)
    usart = USART(cwtestusb)

    force = True
    if fpga.isFPGAProgrammed() == False or force:
        from datetime import datetime

        starttime = datetime.now()
        fpga.FPGAProgram(open(r"C:\E\Documents\academic\sidechannel\chipwhisperer\hardware\capture\chipwhisperer-lite\hdl\cwlite_ise\cwlite_interface.bit", "rb"))
        # fpga.FPGAProgram(open(r"C:\Users\colin\dropbox\engineering\git_repos\CW305_ArtixTarget\temp\artix7test\artix7test.runs\impl_1\cw305_top.bit", "rb"))
        # fpga.FPGAProgram(open(r"C:\E\Documents\academic\sidechannel\chipwhisperer\hardware\api\chipwhisperer-lite\hdl\cwlite_ise_spifake\cwlite_interface.bit", "rb"))
        stoptime = datetime.now()
        print("FPGA Config time: %s" % str(stoptime - starttime))
