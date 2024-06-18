#!/usr/bin/env python3

import xmlrpc.client


class Injector:

    # member variables
    ip = None

    def __init__(self, ip="localhost", port=30001):
        self.ip = ip
        self.port = port
        address = str("".join(["http://", str(self.ip), ":", str(self.port)]))
        self.client = xmlrpc.client.ServerProxy(str(address))

    def library_version(self):
        """
        Retrieve BPS library version

        Return values
          0: everything ok

        DLL int bps_library_version(int* major, int* minor, int* patch);
        """
        return self.client.library_version()

    def init(self):
        """
        Inits an exclusive USB connection to the BPS 202 and initializes the BPS 202.

        Remarks
        - wait at least 2 seconds to make sure the initialization routine has finished
        - make sure to call this function before using any of the other functions. Otherwise they will return invalid information.

        Return values
        -1: error
        0: everything ok

        DLL int bps_init();
        """
        return self.client.init()

    def close(self):
        """
        Closes the exclusive USB connection to the BPS 202.

        Remarks
        - make sure to call this function after usage. If not called the USB connection is not closed which prevents the usage of the BPS 202 from other programs.

        Return values
        -1: error
        0: everything ok

        DLL int bps_close();
        """
        return self.client.close()

    def control(self, state):
        """
        Control BPS 202.

        Parameter state
        0: stop pulsing
        1: start pulsing
        2: single shot

        Return values
        -1: bad parameter
        0: everything ok

        DLL int bps_control(int state);
        """
        return self.client.control(state)

    def get_status(self):
        """
        Get status of BPS 202.

        Return values
        -2: error
        -1: not connected
        0: stopped
        1: single
        2: running
        3: waiting for trigger

        DLL int bps_get_status();
        """
        return self.client.get_status()

    def get_alternating(self):
        """
        Get Alternating Polarity Mode.

        Return values
        -1: error
        0: disabled
        1: enabled

        DLL int bps_get_alternating();
        """
        return self.client.get_alternating()

    def get_burst_period_max_ms(self):
        """
        Get Burst Period maximum in milliseconds.

        Return values
        -1: error
        else: current burst period value in milliseconds

        DLL int bps_get_burst_period_max_ms();
        """
        return self.client.get_burst_period_max_ms()

    def get_burst_period_min_ms(self):
        """
        Get Burst Period minimum in milliseconds.

        Return values
        -1: error
        else: current burst period value in milliseconds

        DLL int bps_get_burst_period_min_ms();
        """
        return self.client.get_burst_period_min_ms()

    def get_burst_period_ms(self):
        """
        Get Burst Period in milliseconds.

        Return values
        -1: error
        else: current burst period value in milliseconds

        DLL int bps_get_burst_period_ms();
        """
        return self.client.get_burst_period_ms()

    def get_pulse_counter_init(self):
        """
        Get Pulse Counter init value.

        Return values
        -1: error
        0: disabled
        else: Counter init value

        DLL int bps_get_pulse_counter_init();
        """
        return self.client.get_pulse_counter_init()

    def get_burst_counter_init(self):
        """
        Get Burst Counter init value.

        Return values
        -1: error
        0: disabled
        else: Counter init value

        DLL int bps_get_burst_counter_init();
        """
        return self.client.get_burst_counter_init()

    def get_pulse_counter(self):
        """
        Get Pulse Counter value.

        Return values
        -1: error
        else: Counter init value

        DLL int bps_get_pulse_counter();
        """
        return self.client.get_pulse_counter()

    def get_burst_counter(self):
        """
        Get Burst Counter value.

        Return values
        -1: error
        else: Counter init value

        DLL int bps_get_burst_counter();
        """
        return self.client.get_burst_counter()

    def get_counter_mode(self):
        """
        Get Pulse Counter Mode.

        Return values
        -1: error
        0: disabled
        1: counter
        2: timer

        DLL int bps_get_counter_mode();
        """
        return self.client.get_counter_mode()

    def get_pulse_level_index(self):
        """
        Get Pulse Level Index starting from 0.

        Return values
        -1  : error
        else: current Level Index

        DLL int bps_get_pulse_level_index();
        """
        return self.client.get_pulse_level_index()

    def get_level_unit(self):
        """
        Get Level unit.

        Return values
        'V', 'kV': volt or kilovolt

        DLL char* bps_get_level_unit();
        """
        return self.client.get_level_unit().data

    def get_pulse_polarity(self):
        """
        Get Pulse Polarity.

        Return values
        -1: error
        0: negative
        1: positive

        DLL int bps_get_pulse_polarity();
        """
        return self.client.get_pulse_polarity()

    def get_probename(self):
        """
        Get Probe Name.

        Return values
        'No Probe': no probe connected
        else: current probes name

        DLL char* bps_get_probename();
        """
        return self.client.get_probename().data

    def get_probeid(self):
        """
        Get Probe ID.

        Return values
        -1: no probe connected
        else: specific probe id

        DLL int bps_get_probeid();
        """
        return self.client.get_probeid()

    def get_probetype(self):
        """
        Get Probe Type.

        Return values
        '---': no probe connected
        else: specific probe type

        DLL char* bps_get_probetype();
        """
        return self.client.get_probetype().data

    def get_probemanufacturer(self):
        """
        Get Probe Manufacturer.

        Return values
        '---': no probe connected
        else: specific probe manufacturer

        DLL char* bps_get_probemanufacturer();
        """
        return self.client.get_probemanufacturer().data

    def get_probehardwareversion(self):
        """
        Get Probe Hardware Version.

        Return values
        '---': no probe connected
        else: specific probe hardware version

        DLL char* bps_get_probehardwareversion();
        """
        return self.client.get_probehardwareversion().data

    def get_probeserial(self):
        """
        Get Probe Serial.

        Return values
        '---': no probe connected
        else: specific probe serial

        DLL char* bps_get_probeserial();
        """
        return self.client.get_probeserial().data

    def get_probefirmwareversion(self):
        """
        Get Probe Firmware Version.

        Return values
        '---': no probe connected
        else: specific probe firmware version

        DLL char* bps_get_probefirmwareversion();
        """
        return self.client.get_probefirmwareversion().data

    def get_probetablesignature(self):
        """
        Get Probe Table Signature.

        Return values
        '---': no probe connected
        else: specific probe table signature

        DLL char* bps_get_probetablesignature();
        """
        return self.client.get_probetablesignature().data

    def get_probefeatures(self):
        """
        Get Probe Features.

        Remarks
        - the following probe features exist (bit flags)

          0x00000001 -> probe supports low jitter trigger delay when bypass of trigger logic is enabled
          0x00000002 -> probe supports pin detection
          0x00000004 -> probe supports pulse level range

        Return values
        -1: no probe connected
        else: specific probe features

        DLL int bps_get_probefeatures();
        """
        return self.client.get_probefeatures()

    def get_bpstype(self):
        """
        Get BPS Type.

        Return values
        '---': no bps connected
        else: specific bps type

        DLL char* bps_get_bpstype();
        """
        return self.client.get_bpstype().data

    def get_bpsmanufacturer(self):
        """
        Get BPS Manufacturer.

        Return values
        '---': no bps connected
        else: specific bps manufacturer

        DLL char* bps_get_bpsmanufacturer();
        """
        return self.client.get_bpsmanufacturer().data

    def get_bpshardwareversion(self):
        """
        Get BPS Hardware Version.

        Return values
        '---': no bps connected
        else: specific bps hardware version

        DLL char* bps_get_bpshardwareversion();
        """
        return self.client.get_bpshardwareversion().data

    def get_bpsfirmwareversion(self):
        """
        Get BPS Firmware Version.

        Return values
        '---': no bps connected
        else: specific bps firmware version

        DLL char* bps_get_bpsfirmwareversion();
        """
        return self.client.get_bpsfirmwareversion().data

    def get_bpsserial(self):
        """
        Get BPS Serial.

        Return values
        '---': no bps connected
        else: specific bps serial

        DLL char* bps_get_bpsserial();
        """
        return self.client.get_bpsserial().data

    def get_pulse_burst_mode(self):
        """
        Get Pulse mode or Burst mode.

        Return values
        -1: error
        0: pulse mode
        1: burst mode

        DLL int bps_get_pulse_burst_mode();
        """
        return self.client.get_pulse_burst_mode()

    def get_pulse_range_count(self):
        """
        Get number of pulse level ranges.

        Return:
        -1: error
        else: number of pulse level ranges

        DLL int bps_get_pulse_range_count();
        """
        return self.client.get_pulse_range_count()

    def get_pulse_level_count(self):
        """
        Get number of possible Pulse Levels.

        Return values
        -1: error
        else: number of pulse levels

        DLL int bps_get_pulse_level_count();
        """
        return self.client.get_pulse_level_count()

    def get_pulse_levels(self, size):
        """
        Get possible Pulse Levels.

        Return values
        -1: buffer too small (use bps_get_pulse_level_count);
        0: ok

        DLL int bps_get_pulse_levels(double* levels, int size);
        """
        return self.client.get_pulse_levels(size)

    def get_pulse_period_max_10ns(self):
        """
        Get Pulse Period maximum in 10 nano seconds.

        Return values
        -1: error
        else: maximum pulse period value in 10 nano seconds

        DLL int bps_get_pulse_period_max_10ns();
        """
        return self.client.get_pulse_period_max_10ns()

    def get_pulse_period_min_10ns(self):
        """
        Get Pulse Period minimum in 10 nano seconds.

        Return values
        -1: error
        else: minimum pulse period value in 10 nano seconds

        DLL int bps_get_pulse_period_min_10ns();
        """
        return self.client.get_pulse_period_min_10ns()

    def get_pulse_period_10ns(self):
        """
        Get Pulse Period in 10 nano seconds.

        Return values
        -1: error
        else: current pulse period value in 10 nano seconds

        DLL int bps_get_pulse_period_10ns();
        """
        return self.client.get_pulse_period_10ns()

    def get_pulses_per_burst(self):
        """
        Get number of Pulses per Burst for Burst Mode.

        Return values
        -1: error
        else: pulses per burst

        DLL int bps_get_pulses_per_burst();
        """
        return self.client.get_pulses_per_burst()

    def get_timer_init_ms(self):
        """
        Get Pulse Timer init value in milliseconds.

        Return values
        -1: error
        0: disabled
        <=65535: Timer init value

        DLL int bps_get_timer_init_ms();
        """
        return self.client.get_timer_init_ms()

    def get_timer_ms(self):
        """
        Get Pulse Timer value in milliseconds.

        Return values
        -1: error
        else: current timer value in milliseconds

        DLL int bps_get_timer_ms();
        """
        return self.client.get_timer_ms()

    def get_trigger_delay_max_10ns(self):
        """
        Get Trigger Delay maximum in 10 nanoseconds.

        Return values
        -1: error
        else: current trigger delay maximum value in 10 nanoseconds

        DLL int bps_get_trigger_delay_max_10ns();
        """
        return self.client.get_trigger_delay_max_10ns()

    def get_trigger_delay_min_10ns(self):
        """
        Get Trigger Delay minimum in 10 nanoseconds.

        Return values
        -1: error
        else: current trigger delay minimum value in 10 nanoseconds

        DLL int bps_get_trigger_delay_min_10ns();
        """
        return self.client.get_trigger_delay_min_10ns()

    def get_trigger_delay_10ns(self):
        """
        Get trigger delay in 10 nanoseconds.

        Return values
        -1: error
        else: current trigger delay value in 10 nanoseconds

        DLL int bps_get_trigger_delay_10ns();
        """
        return self.client.get_trigger_delay_10ns()

    def get_low_jitter_trigger_delay(self):
        """
        Get low jitter trigger delay.

        Remarks
        - check probe features to determine if probe supports low jitter trigger delay

        Return values
        -1: error
        else: current low jittertrigger delay value

        DLL int bps_get_low_jitter_trigger_delay();
        """
        return self.client.get_low_jitter_trigger_delay()

    def set_alternating(self, alternate):
        """
        Set Alternating Polarity Mode.

        Parameter alternate
        0: disable alternating
        1: enable alternating

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_alternating(int alternate);
        """
        return self.client.set_alternating(alternate)

    def set_burst_period_ms(self, period):
        """
        Set Burst Period in milliseconds.

        Return values
        -1: parameter exceeds limits
        0: everything ok

        DLL int bps_set_burst_period_ms(int period);
        """
        return self.client.set_burst_period_ms(period)

    def set_pulse_counter_init(self, counter):
        """
        Set Pulse Counter init value.

        Parameter counter
        0: disable counter
        <=65535: set counter to value

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_pulse_counter_init(int counter);
        """
        return self.client.set_pulse_counter_init(counter)

    def set_burst_counter_init(self, counter):
        """
        Set Burst Counter init value.

        Parameter counter
        0: disable counter
        <=65535: set counter to value

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_burst_counter_init(int counter);
        """
        return self.client.set_burst_counter_init(counter)

    def reinit_remaining_counters(self):
        """
        Reinitializes Burst/Pulse remain counter values with init values.

        Return values
        -1: error
        0: everything ok

        DLL int bps_reinit_remaining_counters();
        """
        return self.client.reinit_remaining_counters()

    def set_counter_mode(self, mode):
        """
        Set Pulse CounterMode.

        Parameter CounterMode
        0: disabled
        1: counter
        2: timer

        Return values
        -1: bad counter mode
        0: everything ok

        DLL int bps_set_counter_mode(int mode);
        """
        return self.client.set_counter_mode(mode)

    def set_pulse_range_index(self, rangeindex):
        """
        Set Pulse Level Range index starting from 0.

        Return values
        -1: parameter exceeds limits
        0: everything ok

        DLL int bps_set_pulse_range_index(int rangeindex);
        """
        return self.client.set_pulse_range_index(rangeindex)

    def set_pulse_level_index(self, levelindex):
        """
        Set Pulse Level Index according starting from 0.

        Return values
        -1: parameter exceeds limits
        0: everything ok

        DLL int bps_set_pulse_level_index(int levelindex);
        """
        return self.client.set_pulse_level_index(levelindex)

    def set_pulse_polarity(self, polarity):
        """
        Set Pulse Polarity.

        Parameter Polarity
        0: negative
        1: positive

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_pulse_polarity(int polarity);
        """
        return self.client.set_pulse_polarity(polarity)

    def set_pulse_burst_mode(self, mode):
        """
        Set Pulse mode or Burst mode.

        Parameter PulseBurstMode
        0: pulse mode
        1: burst mode

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_pulse_burst_mode(int mode);
        """
        return self.client.set_pulse_burst_mode(mode)

    def set_pulse_period_10ns(self, period):
        """
        Set Pulse Period in 10 nanoseconds.

        Return values
        -1: parameter exceeds limits
        0: everything ok

        DLL int bps_set_pulse_period_10ns(int period);
        """
        return self.client.set_pulse_period_10ns(period)

    def set_pulses_per_burst(self, pulses):
        """
        Set Number of Pulses per Burst for Burst Mode.

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_pulses_per_burst(int pulses);
        """
        return self.client.set_pulses_per_burst(pulses)

    def set_timer_init_ms(self, timer):
        """
        Set Pulse Timer init in milliseconds.

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_timer_init_ms(int timer);
        """
        return self.client.set_timer_init_ms(timer)

    def set_probe_pin_contact(self, enabled):
        """
        Set Probe Tip Contact detection.

        Remarks
        - check probe features to determine if probe supports contact detection

        Parameter enabled
        0: disable detection
        1: enabled detection

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_probe_pin_contact(int enabled);
        """
        return self.client.set_probe_pin_contact(enabled)

    def reinit_remaining_timer(self):
        """
        Reinitializes remain timer value with init values.

        Return values
        -1: error
        0: everything ok

        DLL int bps_reinit_remaining_timer();
        """
        return self.client.reinit_remaining_timer()

    def set_trigger_config_mode(self, enabled, edge, action, bypasslogic):
        """
        Configure the trigger.

        Parameter enabled
        0: disable trigger
        1: enabled trigger

        Parameter edge
        0: falling edge
        1: rising edge

        Parameter action
        0: start pulsing or bursting (depending on pulse burst mode);
        1: singe pulse or burst (depending on pulse burst mode);

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_trigger_config_mode(int enabled, int edge, int action, int bypasslogic);
        """
        return self.client.set_trigger_config_mode(enabled, edge, action, bypasslogic)

    def set_trigger_delay_10ns(self, delay):
        """
        Set Trigger Delay in 10 nanoseconds.

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_trigger_delay_10ns(int delay);
        """
        return self.client.set_trigger_delay_10ns(delay)

    def set_low_jitter_trigger_delay(self, delay):
        """
        Set Low Jitter Trigger Delay.

        Remarks
        - check probe features to determine if probe supports low jitter trigger delay

        Parameter delay
        Range: 0...510

        Return values
        -1: error
        0: everything ok

        DLL int bps_set_low_jitter_trigger_delay(int delay);
        """
        return self.client.set_low_jitter_trigger_delay(delay)

    def get_error_msg(self):
        """
        Get the error message for the last error.

        Return values
        'message': error message

        DLL char* bps_get_error_msg();
        """
        return self.client.get_error_msg().data
