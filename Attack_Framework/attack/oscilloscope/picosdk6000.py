from .picosdk.ps6000 import ps6000 as ps
from .picosdk.functions import assert_pico_ok
import ctypes
import math
import numpy as np


class PicoSDK6000:
    def __init__(self):
        self.NUM_CHANNELS = 5
        self.chandle = ctypes.c_int16()
        self.CHRange = [5.0] * self.NUM_CHANNELS
        self.CHOffset = [0.0] * self.NUM_CHANNELS
        self.ProbeAttenuation = [1.0] * self.NUM_CHANNELS
        self.oversample = None
        self.timebase = None
        self.COUPLING = {"AC": 0, "DC": 1, "DC50": 2}
        self.BW_LIMITS = {"Full": 0, "20MHZ": 1, "25MHZ": 2}
        self.CHANNEL_RANGE = [
            {"rangeV": 20e-3, "apivalue": 1},
            {"rangeV": 50e-3, "apivalue": 2},
            {"rangeV": 100e-3, "apivalue": 3},
            {"rangeV": 200e-3, "apivalue": 4},
            {"rangeV": 500e-3, "apivalue": 5},
            {"rangeV": 1.0, "apivalue": 6},
            {"rangeV": 2.0, "apivalue": 7},
            {"rangeV": 5.0, "apivalue": 8},
            {"rangeV": 10.0, "apivalue": 9},
            {"rangeV": 20.0, "apivalue": 10},
        ]
        self.EXTERNAL_CLOCK_FREQ = [
            {"extclock": None, "apivalue": 0},
            {"extclock": 5e6, "apivalue": 1},
            {"extclock": 10e6, "apivalue": 2},
            {"extclock": 20e6, "apivalue": 3},
            {"extclock": 25e6, "apivalue": 4},
        ]
        self.THRESHOLD_TYPE = {"Above": 0, "Below": 1, "Rising": 2, "Falling": 3, "RiseOrFall": 4}
        self.EXT_MAX_VALUE = 32512
        self.EXT_MIN_VALUE = -32512
        self.EXT_RANGE_VOLTS = 20
        self.MAX_VALUE = 32512
        self.MIN_VALUE = -32512

        self.noSamples = None
        self.sampleInterval = None
        self.maxSamples = None
        self.sampleRate = None
        self.sampleInterval = None
        self.nSamples = None
        self.currentBufferIndex = 0
        self.buffer = None
        self.cOverflow = None
        self.usedChannels = []

    def getTimeBaseNum(self, sampleTimeS):
        """Return sample time in seconds to timebase as int for API calls."""
        maxSampleTime = ((2**32 - 1) - 4) / 156250000

        if sampleTimeS < 6.4e-9:
            timebase = math.floor(math.log(sampleTimeS * 5e9, 2))
            timebase = max(timebase, 0)
        else:
            # Otherwise in range 2^32-1
            if sampleTimeS > maxSampleTime:
                sampleTimeS = maxSampleTime

            timebase = int(math.floor((sampleTimeS * 156250000) + 4))

        return timebase

    def getTimestepFromTimebase(self, timebase):
        """Return timebase to sampletime as seconds."""
        if timebase < 5:
            dt = 2.0**timebase / 5e9
        else:
            dt = (timebase - 4.0) / 156250000.0
        return dt

    def getMaxValue(self):
        """Return the maximum ADC value, used for scaling."""
        # This was a "fix" when we started supported PS5000a
        return self.MAX_VALUE

    def getMinValue(self):
        """Return the minimum ADC value, used for scaling."""
        return self.MIN_VALUE

    def open(self, serialNumber=None):
        """Open the scope, using a serialNumber if given."""
        # Open 6000 series PicoScope
        status = ps.ps6000OpenUnit(ctypes.byref(self.chandle), serialNumber)
        assert_pico_ok(status)

    def setChannel(self, channel=0, coupling="AC", VRange=2.0, VOffset=0.0, enabled=True, BWLimited=0, probeAttenuation=1.0):
        """
        Set up a specific scope channel.

        It finds the smallest range that is capable of accepting your signal.
        Return actual range of the scope as double.

        The VOffset, is an offset that the scope will ADD to your signal.

        If using a probe (or a sense resitor), the probeAttenuation value is
        used to find the approriate channel range on the scope to use.

        e.g. to use a 10x attenuation probe, you must supply the following
        parameters ps.setChannel('A', "DC", 20.0, 5.0, True, False, 10.0)

        The scope will then be set to use the +- 2V mode at the scope allowing
        you to measure your signal from -25V to +15V.
        After this point, you can set everything in terms of units as seen at
        the tip of the probe. For example, you can set a trigger of 15V and it
        will trigger at the correct value.

        When using a sense resistor, lets say R = 1.3 ohm, you obtain the
        relation:
        V = IR, meaning that your probe as an attenuation of R compared to the
        current you are trying to measure.

        You should supply probeAttenuation = 1.3
        The rest of your units should be specified in amps.

        Unfortunately, you still have to supply a VRange that is very close to
        the allowed values. This will change in future version where we will
        find the next largest range to accommodate the desired range.

        If you want to use units of mA, supply a probe attenuation of 1.3E3.
        Note, the authors recommend sticking to SI units because it makes it
        easier to guess what units each parameter is in.

        """
        if not isinstance(coupling, int):
            coupling = self.COUPLING[coupling]

        # converting VRange from float to enum
        # finds the next largest range
        VRangeAPI = None
        for item in self.CHANNEL_RANGE:
            if item["rangeV"] - VRange / probeAttenuation > -1e-4:
                if VRangeAPI is None:
                    VRangeAPI = item
                elif VRangeAPI["rangeV"] > item["rangeV"]:
                    VRangeAPI = item

        if VRangeAPI is None:
            raise ValueError("Desired range %f is too large. Maximum range is %f." % (VRange, self.CHANNEL_RANGE[-1]["rangeV"] * probeAttenuation))

        # store the actually chosen range of the scope
        VRange = VRangeAPI["rangeV"] * probeAttenuation

        if not isinstance(BWLimited, int):
            BWLimited = self.BW_LIMITS[BWLimited]

        if enabled:
            enabled = 1
            if channel not in self.usedChannels:
                self.usedChannels.append(channel)
        else:
            enabled = 0

        if not isinstance(channel, int):
            chNum = self.CHANNELS[channel]
        else:
            chNum = channel

        # if all was successful, save the parameters
        self.CHRange[chNum] = VRange
        self.CHOffset[chNum] = VOffset
        self.ProbeAttenuation[chNum] = probeAttenuation

        status = ps.ps6000SetChannel(self.chandle, channel, enabled, coupling, VRangeAPI["apivalue"], VOffset / probeAttenuation, BWLimited)
        assert_pico_ok(status)
        return VRange

    def setExternalClock(self, frequency, threshold):
        """Set external clock for synchronisation."""
        # representing 1V
        max_threshold = 32512

        for item in self.EXTERNAL_CLOCK_FREQ:
            if item["extclock"] == frequency:
                frequency = item["apivalue"]
                break

        if frequency > 5 or frequency < 0:
            raise ValueError("Given frequency is not possible! Given: ", frequency)

        if not -1 <= threshold <= 1:
            raise ValueError("External clock threshold in false range! Possible range [-1V - 1V]. Given: ", threshold)
        else:
            discrete_threshold = int(threshold * max_threshold)
            if threshold < 0:
                discrete_threshold = -discrete_threshold

        status = ps.ps6000SetExternalClock(self.chandle, frequency, discrete_threshold)
        assert_pico_ok(status)

    def setSamplingInterval(self, sampleInterval, duration, oversample=0, segmentIndex=0):
        """Return (actualSampleInterval, noSamples, maxSamples)."""

        self.oversample = oversample
        self.timebase = self.getTimeBaseNum(sampleInterval)

        timebase_dt = self.getTimestepFromTimebase(self.timebase)
        if timebase_dt != sampleInterval:
            raise ValueError("Specified Sampling Frequency is not supported! Next possible frequency is %.2f MHz." % ((1 / timebase_dt) / 10**6))

        noSamples = int(round(duration / timebase_dt))

        cSampleInterval = ctypes.c_float()
        cMaxSamples = ctypes.c_int32()

        status = ps.ps6000GetTimebase2(self.chandle, self.timebase, noSamples, ctypes.byref(cSampleInterval), self.oversample, ctypes.byref(cMaxSamples), segmentIndex)
        assert_pico_ok(status)
        self.maxSamples = cMaxSamples.value
        # scale sampleInterval from ns to seconds
        self.sampleInterval = cSampleInterval.value
        self.sampleInterval /= 1.0e9
        self.noSamples = noSamples
        self.nSamples = min(self.noSamples, self.maxSamples)
        self.sampleRate = 1.0 / self.sampleInterval
        return self.sampleInterval, self.noSamples, self.maxSamples

    def setSimpleTrigger(self, trigSrc, threshold_V=0, direction="Rising", delay=0, timeout_ms=100, enabled=True):
        """Set up a simple trigger.

        trigSrc can be either a number corresponding to the low level
        specifications of the scope or a string such as 'A' or 'AUX'

        direction can be a text string such as "Rising" or "Falling",
        or the value of the dict from self.THRESHOLD_TYPE[] corresponding
        to your trigger type.

        delay is number of clock cycles to wait from trigger conditions met
        until we actually trigger capture.

        timeout_ms is time to wait in mS from calling runBlock() or similar
        (e.g. when trigger arms) for the trigger to occur. If no trigger
        occurs it gives up & auto-triggers.

        Support for offset is currently untested

        Note, the AUX port (or EXT) only has a range of +- 1V
        (at least in PS6000)
        """
        if not isinstance(trigSrc, int):
            trigSrc = self.CHANNELS[trigSrc]

        if not isinstance(direction, int):
            direction = self.THRESHOLD_TYPE[direction]

        if trigSrc >= self.NUM_CHANNELS:
            threshold_adc = int((threshold_V / self.EXT_RANGE_VOLTS) * self.EXT_MAX_VALUE)

            # The external port is typically used as a clock. So I don't think
            # we should raise errors
            threshold_adc = min(threshold_adc, self.EXT_MAX_VALUE)
            threshold_adc = max(threshold_adc, self.EXT_MIN_VALUE)
        else:
            a2v = self.CHRange[trigSrc] / self.getMaxValue()
            threshold_adc = int((threshold_V + self.CHOffset[trigSrc]) / a2v)

            if threshold_adc > self.getMaxValue() or threshold_adc < self.getMinValue():
                raise IOError("Trigger Level of %fV outside allowed range (%f, %f)" % (threshold_V, -self.CHRange[trigSrc] - self.CHOffset[trigSrc], +self.CHRange[trigSrc] - self.CHOffset[trigSrc]))

        enabled = int(bool(enabled))

        status = ps.ps6000SetSimpleTrigger(self.chandle, enabled, trigSrc, threshold_adc, direction, delay, timeout_ms)
        assert_pico_ok(status)

    def runBlock(self, pretrig=0.0, segmentIndex=0):
        """Run a single block. Pretrigger is given in seconds, which essentially allows to define
        a negative trigger delay.

        Must have already called setSampling for proper setup.

        :param pretrig: duration of pretrigger capture [s]
        :param segmentIndex: segment index for sequence mode
        :return:
        """

        """
        """
        self.buffer = None
        self.currentBufferIndex = 0
        # Calculate the number of pretrigger samples from the sampling rate and time given
        # At most the number of samples can be used!
        nSamples_pretrig = min(self.nSamples, int(round(pretrig * self.sampleRate)))

        # Calculate the number of posttrigger samples: the remaining samples are take from after the trigger
        nSamples_posttrig = self.nSamples - nSamples_pretrig
        status = ps.ps6000RunBlock(self.chandle, nSamples_pretrig, nSamples_posttrig, self.timebase, self.oversample, None, segmentIndex, None, None)
        assert_pico_ok(status)

    def waitReady(self):
        """Block until the scope is ready."""
        ready = 0
        while ready == 0:
            ready = self.isReady()
        return

    def isReady(self):
        """
        Check if scope done.

        Returns: bool.

        """
        # TODO: this is not needed if the callback function is used (c.f. runBlock)
        ready = ctypes.c_int16(0)
        status = ps.ps6000IsReady(self.chandle, ctypes.byref(ready))
        assert_pico_ok(status)
        return np.uint8(ready.value)

    def getDataRaw(self, channel, numSamples, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0):
        """Return the data as an array of voltage values.

        it returns (dataV, overflow) if returnOverflow = True
        else, it returns returns dataV
        dataV is an array with size numSamplesReturned
        overflow is a flag that is true when the signal was either too large
                 or too small to be properly digitized

        if exceptOverflow is true, an IOError exception is raised on overflow
        if returnOverflow is False. This allows you to detect overflows at
        higher layers w/o complicated return trees. You cannot however read the
        'good' data, you only get the exception information then.
        """

        cNumSamples = ctypes.c_int32(numSamples)

        # allocate buffers for data if not allocated and read data from picoscope
        if self.buffer is None:
            # allocate buffers
            self.buffer = []
            self.cOverflow = ctypes.c_int16()
            for i in range(0, len(self.usedChannels)):
                self.buffer.append((ctypes.c_int16 * numSamples)())
                self.buffer.append((ctypes.c_int16 * numSamples)())
                status = ps.ps6000SetDataBuffers(self.chandle, self.usedChannels[i], ctypes.byref(self.buffer[i * 2]), ctypes.byref(self.buffer[i * 2 + 1]), numSamples, downSampleMode)
                assert_pico_ok(status)
            # read data from picoscope (can only be called once and data of all channels is read)
            status = ps.ps6000GetValues(self.chandle, startIndex, ctypes.byref(cNumSamples), downSampleRatio, downSampleMode, segmentIndex, ctypes.byref(self.cOverflow))
            assert_pico_ok(status)
            data = np.array(self.buffer[0], np.int16)
        else:
            # if buffers are allocated return data stored in buffers
            if len(self.usedChannels) > 1:
                data = np.array(self.buffer[self.currentBufferIndex * 2], np.int16)

        overflow = self.cOverflow.value

        # overflow is a bitwise mask
        overflow = bool(overflow & (1 << channel))
        self.currentBufferIndex += 1
        return data, cNumSamples.value, overflow

    def close(self):
        """
        Close the scope.

        You should call this yourself because the Python garbage collector
        might take some time.

        """
        if self.chandle is not None:
            status = ps.ps6000CloseUnit(self.chandle)
            assert_pico_ok(status)
            self.chandle = None

    def __del__(self):
        self.close()
