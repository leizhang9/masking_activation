import attack.oscilloscope.picosdk6000 as scope
import targets.PapilioOne.PapilioOne as PapilioOne
import matplotlib.pyplot as plt
import numpy as np
import time
import logging


def test_block_mode(ps, target, n_captures=100, sample_interval=100e-9, sample_duration=2e-3, acquistion_channel="A", acq_ch_VRange=0.2, pre_trigger=0.0, trigger_channel="D", trigger_threshold=0.1, trigger_timeout=1000, mode="BlockMode"):
    """

    :param ps: object of the oscilloscope
    :param target: object of the DUT
    :param n_captures: number of subsequent acquisitions
    :param sample_interval: sampling interval in [s], will be adapted to possible ranges of the oscilloscope
    :param sample_duration: duration of the measurement period in [s]
    :param acquistion_channel: channel for acquisition ("A", "B", "C", "D", "TriggerAux")
    :param acq_ch_VRange: voltage range in [V] of the acquisition channel
    :param pre_trigger: percentage of pre-trigger samples
    :param trigger_channel: channel of the trigger ("A", "B", "C", "D", "TriggerAux")
    :param trigger_threshold: trigger threshold in [V]
    :param trigger_timeout: time in [ms] after which an acquistion is triggeres, if no trigger event was received
    :param mode: acquisition mode of the oscilloscope "BlockMode", "RapidBlockMode" (TODO)
    :return:
    """

    """
        Channel Set Up
    """
    ps.setChannel(channel="A", enabled=False)
    ps.setChannel(channel="B", enabled=False)
    ps.setChannel(channel="C", enabled=False)
    ps.setChannel(channel="D", enabled=False)
    ps.setChannel(channel=acquistion_channel, coupling="DC", VRange=acq_ch_VRange, enabled=True)
    if trigger_channel == "D":
        ps.setChannel(channel="D", coupling="DC", VRange=1, enabled=True)

    ps.setSamplingInterval(sample_interval, sample_duration)
    # number of samples per segment
    if mode == "RapidBlockMode":
        # TODO: RapidBlockMode needs to be implemented
        sample_per_segment = ps.memorySegments(n_captures)
        ps.setNoOfCaptures(n_captures)
    else:
        sample_per_segment = round(sample_duration / sample_interval)
    """
        Trigger Set Up
    """
    ps.setSimpleTrigger(trigger_channel, threshold_V=trigger_threshold, timeout_ms=trigger_timeout, direction="Rising", delay=0)

    """
        Initialization of Variables
    """
    data = np.zeros((n_captures, sample_per_segment), dtype=np.int16)
    trigger = np.zeros((n_captures, sample_per_segment), dtype=np.int16)
    # run time counters
    record_time = 0
    ram_time = 0

    """
        Run data acquisition
    """
    # run dummy acquisitions
    # after setting up the block mode, the picoscope tends to miss the first trigger(s), c.f.
    # https://www.picotech.com/support/post97941.html and
    # https://www.picotech.com/support/post60001.html.
    # Introducing a small delay before the first measurement as advised did not work out, so
    # recording some random data and discarding it seems to be a good work around.
    for i in range(1):
        # Run Block
        ps.runBlock(pretrig=pre_trigger, segmentIndex=0)
        # activate trigger
        target.serial_send_command(["0x88"], 16)
        # wait for data
        ps.waitReady()
        # acquire data
        ps.getDataRaw(numSamples=sample_per_segment, channel=acquistion_channel, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0)

    # run actuaö data acquisition
    for i in range(n_captures):
        # Run Block
        t1 = time.time()
        ps.runBlock(pretrig=pre_trigger, segmentIndex=0)

        # activate trigger
        target.serial_send_command(["0x88"], 16)

        # wait for data
        # TODO: to use RapidBlockMode, the "ps6000BlockReady" callback must be used instead of "ps6000IsReady"!
        ps.waitReady()
        t2 = time.time()

        if mode != "RapidBlockMode":
            # acquire data from desired channel
            data[i, :], _, _ = ps.getDataRaw(numSamples=sample_per_segment, channel=acquistion_channel, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0)
            # record trigger if possible
            if trigger_channel != "TriggerAux":
                trigger[i, :], _, _ = ps.getDataRaw(numSamples=sample_per_segment, channel=trigger_channel, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0)
        t3 = time.time()

        # update run time counters
        record_time = record_time + t2 - t1
        ram_time = ram_time + t3 - t2

    if mode == "RapidBlockMode":
        # TODO: RapidBlockMode needs to be implemented
        t1 = time.time()
        ps.getDataRawBulk(numSamples=sample_per_segment, channel=acquistion_channel, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0, data=data)

        # retrieve trigger if possible
        if trigger_channel != "TriggerAux":
            ps.getDataRawBulk(numSamples=sample_per_segment, channel=trigger_channel, startIndex=0, downSampleRatio=1, downSampleMode=0, segmentIndex=0, data=trigger)
        t2 = time.time()
        ram_time = t2 - t1

    print(mode, ": Time to record data to scope: ", str(record_time))
    print(mode, ": Time to copy to RAM: ", str(ram_time))

    """
        Plot Measurements
    """
    x = np.linspace(0, sample_per_segment, sample_per_segment)

    f, (ax1, ax2) = plt.subplots(2)
    ax1.plot(x, data.transpose(), color="gray")
    ax1.plot(x, data.mean(axis=0), color="black")

    ax2.plot(x, trigger.transpose(), color="gray")
    ax2.plot(x, trigger.mean(axis=0), color="black")

    plt.show()


def main():
    """
    Test PicoScope 6000
    """
    print("Testing PicoScope 6000")
    # Initialize PS6000
    ps = scope.PS6000()
    # print the device information
    print(ps.getAllUnitInfo())

    # Let the front LED blink 10 times
    ps.flashLed(10)
    """
    Test Papilio One
    """
    print("Testing Papilio One")

    logging.basicConfig(format="%(asctime)s - %(levelname)s: %(message)s")
    target = PapilioOne()
    target.test_target("../targets/PapilioOne/main_bch.bit")

    # connect Papilio board
    target.serial_connect()

    # TestRapidBlockMode(ps, target)
    print("Testing Block Mode of PicoScope 6000")
    test_block_mode(ps, target, n_captures=10, sample_interval=400e-12, sample_duration=400e-9, acquistion_channel="A", acq_ch_VRange=0.1, pre_trigger=0.5, trigger_channel="D", trigger_threshold=0.1, trigger_timeout=1000)

    ps.close()


if __name__ == "__main__":
    main()
