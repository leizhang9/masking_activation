#!/usr/bin/env python

"""
This is a small example script setting up an arbitrary waveform output
with a Keysight 33622A. The waveform generator is programmed with a NumPy
array containing voltage samples, set up for single-cycle burst mode and
then triggered over using an SCPI command.
"""

from attack.waveform_generator.Keysight_Trueform import Keysight_Trueform as Arb
import logging
import numpy as np

logging.basicConfig()
logging.getLogger().setLevel(level=logging.DEBUG)

if __name__ == "__main__":
    arb = Arb("TCPIP::A-33622A-00922.sec.ei.tum.de::inst0::INSTR")

    # Set the output load first, as the voltage calculation depends on it
    arb.set_output_load(None)

    # Generate an example waveform: a ramp between -0.5 V and 1 V
    waveform = np.linspace(-0.5, 1, 1000)
    waveform = np.pad(waveform, (1, 1))
    arb.load_arb(waveform, 1_000_000)

    # Select bus trigger
    arb.set_trigger_source("bus")

    # Enable triggered burst mode so the generator will output a single
    # cycle for each bus trigger
    arb.triggered_burst(cycles=1)

    # Enable signal output and trigger output
    arb.enable_output()
    arb.configure_trigger_out(True, level=3.3)

    # Trigger
    arb.trigger()
