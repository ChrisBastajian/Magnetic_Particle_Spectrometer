from nidaqmx.constants import Edge
import matplotlib.pyplot as plt
import wave_gen
import nidaqmx
import receive_and_analyze as analyze
import numpy as np

#Signal Parameters:
gpib_address = 10
fs = 100000
num_periods = 2
channel = 1
voltage = 1 #volts
f = 1000 #signal frequency in Hz

# Daq Card Parameters:
sig_chan = "Dev3/ai0"
curr_chan = "Dev3/ai1"
trig_chan = "/Dev3/pfi0"

#Connect and generate signal:
waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
wave_gen.send_voltage(waveform_generator, voltage, f, channel)

#Receive signal with trigger:
num_pts_per_period = fs/f
num_samples = int(num_pts_per_period*num_periods)


plt.figure()
voltage = analyze.receive_raw_voltage(sig_chan, fs, num_samples)
plt.plot(voltage, alpha=0.6)

plt.title("Waveform Generator Voltage")
plt.xlabel("Sample")
plt.ylabel("Voltage (V)")
plt.grid(True)
plt.show()


wave_gen.turn_off(waveform_generator, channel)