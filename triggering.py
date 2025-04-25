from nidaqmx.constants import Edge
import matplotlib.pyplot as plt
import wave_gen
import nidaqmx

#Signal Parameters:
gpib_address = 10
fs = 100000
num_periods = 2
channel = 1
voltage = 0.2 #volts
f = 1000 #signal frequency in Hz

# Daq Card Parameters:
sig_chan = "Dev3/ai0"
trig_chan = "/Dev3/pfi0"

#Connect and generate signal:
waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
wave_gen.send_voltage(waveform_generator, voltage, f, channel)

#Receive signal with trigger:
num_pts_per_period = fs/f
num_samples = int(num_pts_per_period*num_periods)

def receive_voltage(daq_location, sample_rate, n_samps, trigger_location=None,):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(daq_location)
        # Add a trigger source and set it to rising edge
        if trigger_location is not None:
            task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_location, Edge.RISING)

        task.timing.cfg_samp_clk_timing(sample_rate, samps_per_chan=n_samps)
        voltage_raw = task.read(number_of_samples_per_channel= n_samps)
        return voltage_raw


plt.figure()
plt.subplot(2,1,1)
for _ in range(5):
    voltage = receive_voltage(sig_chan, fs, num_samples)
    plt.plot(voltage, alpha=0.6)

plt.title("Overlay of  Non-triggered Waveforms")
plt.xlabel("Sample")
plt.ylabel("Voltage (V)")
plt.grid(True)

plt.subplot(2,1, 2)
for _ in range(5):
    voltage = receive_voltage(sig_chan, fs, num_samples, trigger_location=trig_chan)
    plt.plot(voltage, alpha=0.6)

plt.title("Overlay of Triggered Waveforms")
plt.xlabel("Sample")
plt.ylabel("Voltage (V)")
plt.grid(True)
plt.tight_layout()
plt.show()

wave_gen.turn_off(waveform_generator, channel)