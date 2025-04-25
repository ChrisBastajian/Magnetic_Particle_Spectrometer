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
amplitude = 1 #volts
f = 1000 #signal frequency in Hz

# Daq Card Parameters:
sig_chan = "Dev3/ai0"
curr_chan = "Dev3/ai1"
trig_chan = "/Dev3/pfi0"

#Connect and generate signal:
waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
wave_gen.send_voltage(waveform_generator, amplitude, f, channel)

#Receive signal with trigger:
num_pts_per_period = fs/f
num_samples = int(num_pts_per_period*num_periods)


plt.figure()
voltage = analyze.receive_raw_voltage(sig_chan, fs, num_samples, trigger_location=trig_chan)
plt.plot(voltage, alpha=0.6)

plt.title("Waveform Generator Voltage")
plt.xlabel("Sample")
plt.ylabel("Voltage (V)")
plt.grid(True)



# Compute the FFT of the voltage signal
fft_voltage = np.fft.fft(voltage)

# Get the frequency bins
frequencies = np.fft.fftfreq(len(voltage), 1/fs)

# Find the index corresponding to the frequency of interest (f)
index_of_interest = np.argmax(np.abs(fft_voltage[:len(fft_voltage)//2]))  # Only look at the positive frequencies

# Extract the phase at that frequency
phase = np.angle(fft_voltage[index_of_interest])

# Print the phase (in radians and degrees)
print(f"Phase of the signal at {f} Hz: {phase} radians ({np.degrees(phase)} degrees)")

# Plot the phase
plt.figure()
plt.plot(frequencies[:len(frequencies)//2], np.angle(fft_voltage)[:len(frequencies)//2])  # Only positive frequencies
plt.title("Phase Spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase (radians)")
plt.grid(True)

plt.show()

# Turn off the waveform generator
wave_gen.turn_off(waveform_generator, channel)