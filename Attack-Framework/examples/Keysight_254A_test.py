import attack.oscilloscope.Keysight_254A as Keysight_254A
import numpy as np
import matplotlib.pyplot as plt
import logging

logging.basicConfig()
logging.getLogger().setLevel(level=logging.DEBUG)

if __name__ == "__main__":
    """
    This is a minimal script to acquire data with the Keysight S-Series using VXI11. It is assumed that you have a
    trigger on channel 2 and acquire on channel 1. For the segmented mode, two events have to occur within the first
    10 secs, otherwise the blocking mode will time out.
    It may be necessary to adapt some of the parameters, including the LAN address of the scope. Have fun. :)
    """
    # initialize the connection to the scope. You may need to adapt the LAN address here
    scope = Keysight_254A.Keysight_DSOS_254A("TCPIP::WINDOWS-UH2SI2U.sec.ei.tum.de::inst0::INSTR")

    #
    scope.send_query(":STOP;*OPC?")

    # set waveform format that is tranmitted, turn headers off and set streaming mode on/off
    scope.config_instr(waveform_format="WORD", streaming=0)

    # set the properties of channel 1 probe attenuation does not work at the moment!
    voltage_range = 200e-3
    scope.setChannel(channel=1, coupling="DC", VRange=voltage_range, VOffset=0.0, enabled=True, BWLimited=0)

    # set the sampling interval you want to acquire
    scope.setSamplingInterval(sampling_duration=10e-3, preTriggerSamples=None, preTriggerRelative=None)

    # set the sampling rate
    scope.setSamplingRate(sampling_rate=1e9)

    scope.send_command_and_query(":TRIGger:SWEep TRIGgered")
    scope.setSimpleTrigger(trigSrc=2, threshold_V=2.0)

    scope.set_acquisition(interpolation=0, acquisition_mode="SEGM", num_segments=2)

    for i in range(0, 2):
        # clear display
        scope.send_command(":CDISplay")
        scope.send_command("*CLS")
        # acquire data
        if i == 0:
            # poll time [s] is the time to wait between queries if the acquisition is ready
            scope.acquire_data_polling(poll_time=0.005)
        elif i == 1:
            # acquisition timeout [s] is the time to wait until the acquisition is ended, needed in blocking mode
            scope.acquire_data_blocking(acquisition_time_out=10)

        # for some reason, currently a small delay is needed
        # time.sleep(1)

        # read back the data from the oscilloscope
        data_raw, wave_points, x_origin, x_increment, y_origin, y_increment = scope.send_data_query()

        # convert the raw data into voltage values and generate an appropriate time vector
        time_vec = np.arange(x_origin, x_origin + wave_points * x_increment, x_increment)
        data = data_raw * y_increment + y_origin

        plt.figure(i)
        # plot the results. This should equal what you can see on the screen of the oscilloscope
        plt.plot(time_vec, data)
        plt.xlim(x_origin, x_origin + wave_points * x_increment)
        plt.ylim(-voltage_range / 2, voltage_range / 2)
        plt.grid()
        plt.show()

    scope.close_unit()
