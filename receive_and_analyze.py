import numpy as np
import nidaqmx
import wave_gen
from nidaqmx.constants import AcquisitionType, Edge
import matplotlib.pyplot as plt

######################## USED IN main.py only (Example Code) #######################################
def background_subtraction(daq_location, sense_location, sample_rate, num_samples, gpib_address, amplitude, frequency, channel, isclean):
    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    ##################### Eventually add a live frequency domain for cancellation coil before measuring background#######

    background = receive_raw_voltage(daq_location, sample_rate, num_samples) #receive the background
    background_magnitude, background_frequency, sample_phase, background_complex = fourier(background, sample_rate, num_samples)

    #Turn the waveform generator off:
    waveform_generator.write(f"OUTPUT{channel} OFF")

    #Let user start the second signal to measure SPIO charactristics
    insert_sample = input("Did you insert the sample? ")

    if insert_sample == 'yes':
        wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

        #Receive signal
        signal = receive_raw_voltage(daq_location, sample_rate, num_samples)
        signal_magnitude, signal_frequency, sample_phase, signal_complex = fourier(signal, sample_rate, num_samples)


        #Get the rms current
        i_rms = get_rms_current(sense_location, fs=sample_rate, num_samples=num_samples, trigger_location=None)

    else:
        print("Okay")
        sample_complex, signal_frequency = -99, -99 #will be used as error values

    #Turn off waveform generator and close:
    wave_gen.turn_off(waveform_generator, channel)

    # subtract background:
    sample_complex = signal_complex - background_complex
    sample_magnitude = np.abs(sample_complex)
    sample_phase = np.angle(sample_complex)

    return sample_magnitude, signal_frequency, i_rms, sample_phase, signal

################################# Used in MPS_app.py: ###############################################
def receive_raw_voltage(daq_location, sample_rate, n_samps, trigger_location=None,):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(daq_location)
        # Add a trigger source and set it to rising edge
        if trigger_location is not None:
            task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_location, Edge.RISING)

        task.timing.cfg_samp_clk_timing(sample_rate, samps_per_chan=n_samps)
        voltage_raw = task.read(number_of_samples_per_channel= n_samps)
        return voltage_raw

def DC_offset(current):
    power_supply = wave_gen.connect_power_supply('ASRL5::INSTR') #connecting via usb
    voltage = 12 #volts since thisis the max of the power supply
    if power_supply:
        wave_gen.send_dc_voltage(power_supply, voltage, current)
        return power_supply

def get_background(daq_location, source_location, trigger_location, sample_rate, num_periods, gpib_address,
                   amplitude, frequency, channel, dc_current):
    num_pts_per_period = sample_rate/ frequency #Fs/F_drive
    num_samples = int(num_periods * num_pts_per_period)

    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    #Connect to the DC power supply and send the current through the helmholtz coils:
    power_supply = DC_offset(dc_current)

    background = receive_raw_voltage(daq_location, sample_rate, num_samples, trigger_location) #receive the background (raw daq readout)

    #Turn the waveform generator and power supply off:
    wave_gen.turn_off(waveform_generator, channel)
    if power_supply:
        wave_gen.turn_off_dc_output(power_supply)
        power_supply.close()

    background_magnitude, background_frequency, background_phase, background_complex = fourier(background, sample_rate, num_samples)
    #Apply a mask for the background magnitude if needed:
    #background_magnitude = cutoff(background_amplitude)

    return num_samples, background_magnitude, background_frequency, background_phase, background, background_complex

def odd_harmonics(fourier, fourier_frequency, f_d, sample_rate):
    #This is to get a fourier amplitudes array and return one with only odd harmonics:
    main_harmonic = f_d/1000 #in kHz
    odd_numbers = []
    odd_range = sample_rate//2 #highest frequency detected by daq card

    for l in range(odd_range):
        if l%2 !=0:
            odd_numbers = np.append(odd_numbers, l)

    odd_harmonics = main_harmonic * odd_numbers

    for i, frequency in enumerate(fourier_frequency):
        frequency_kHz = np.abs(frequency / 1000)

        if frequency_kHz not in odd_harmonics:
            fourier[i] = 0

        else:
            fourier = abs(fourier)
    return fourier

def get_sample_signal(daq_location, sense_location, trigger_location, sample_rate, num_periods, gpib_address, amplitude,
                      frequency, channel, dc_current, background_complex, isClean):
    num_pts_per_period = sample_rate/ frequency #Fs/F_drive
    num_samples = int(num_periods * num_pts_per_period)

    #Connect to the DC power supply and send the current through the helmholtz coils:
    power_supply = DC_offset(dc_current)

    #connect waveform generator and send signal:
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    # Receive signal
    signal_with_background = receive_raw_voltage(daq_location, sample_rate, num_samples, trigger_location)

    # Get the rms current
    i_rms = get_rms_current(sense_location, fs=sample_rate, num_samples=num_samples, trigger_location=trigger_location)

    #Turn off waveform generator and power supply and close:
    wave_gen.turn_off(waveform_generator, channel)
    if power_supply:
        wave_gen.turn_off_dc_output(power_supply)
        power_supply.close()

    signal_with_background_magnitude, signal_frequency, sample_with_background_phase, signal_complex = fourier(signal_with_background, sample_rate,
                                                                 num_samples)

    # subtract background:
    sample_complex = signal_complex - background_complex
    sample_magnitude = np.abs(sample_complex)
    sample_phase = np.angle(sample_complex)

    #If odd harmonics are selected:
    if isClean:
        sample_magnitude = odd_harmonics(sample_magnitude, signal_frequency, frequency, sample_rate) #will give the magnitudes of the odd harmonics only

    return num_samples, sample_magnitude, signal_frequency, signal_with_background, sample_phase, i_rms

def fourier(waveform, sample_rate, num_samples):
    #Find real and imaginary amplitudes
    fourier_complex = np.fft.fft(waveform)/num_samples #dividing by num_samples for normalization

    #Setup a frequency array for the amplitudes
    fourier_frequency = np.fft.fftfreq(num_samples, d = 1/sample_rate) #array of length equal to the
                                                                        # number of samples and spaced by
                                                                        # the period = 1/sample rate
    abs_mask = fourier_frequency>=0 #getting positive frequency data only (expected)
    fourier_frequency = fourier_frequency[abs_mask]
    fourier_complex = fourier_complex[abs_mask]

    Cn= np.abs(fourier_complex)
    phase = np.angle(fourier_complex)

    return Cn, fourier_frequency, phase, fourier_complex

def reconstruct_and_integrate(num_samples, frequency_array, cn, f_drive, phase=None):
    f = frequency_array[:num_samples]
    coeff = cn[:num_samples]
    omega = 2 * np.pi * f
    if phase is not None:
        phase = phase[:num_samples]
    else:
        phase= np.zeros(num_samples)

    t = np.linspace(0, 4 / f_drive, 40000)
    integral = np.zeros(len(t))
    recon = np.zeros(len(t))

    for i in range(len(coeff)):
        if omega[i] != 0:
           recon += coeff[i] * np.cos((omega[i] * t) + phase[i])
           integral += (coeff[i] / omega[i]) * np.sin((omega[i] * t) +phase[i])

    first_idx = len(t)//8 +len(t)//16
    second_idx = first_idx + len(t)//4 #so we can get 1 period
    recon_half = recon[first_idx: second_idx]
    integral_half = integral[first_idx: second_idx] - np.mean(integral[first_idx: second_idx]) #get rid of DC offset
    return recon_half, integral_half

def general_reconstruction(amplitude, frequency):
    t= np.linspace(0, 1/frequency, 10000)

    recon = np.zeros(len(t))
    omega = 2 * np.pi * frequency
    recon = amplitude * np.cos(omega * t - np.pi)

    return recon

def dMdH(M, H): #differentiate M with respect to H and keep it the same length to plot
    dMdH = np.gradient(M, edge_order= 2)/np.gradient(H, edge_order= 2)
    dMdH[0]=0
    dMdH[-1]=0 #to get rid of unnecessary artifacts

    return dMdH

def get_rms_current(daq_location, fs, num_samples, trigger_location):
    # current sensing variables:
    Vcc = 5.0
    VQ = 0.5 * Vcc
    sensitivity = 0.1
    voltages_raw = np.zeros(num_samples)
    currents = np.zeros(num_samples)
    squares = np.zeros(num_samples)
    squares_added = 0
    i = 0
    voltage = receive_raw_voltage(daq_location, fs, num_samples, trigger_location)
    squares_added = 0

    for i in range(num_samples):
        voltages_raw[i] = voltage[i]
        voltage_corrected = voltages_raw[i] - VQ
        currents[i] = voltage_corrected / sensitivity

        squares[i] = currents[i] ** 2
        squares_added += squares[i]

    mean_square = squares_added / num_samples
    rms_current = np.sqrt(mean_square)

    print(f"I(rms): {rms_current:.2f}")

    return rms_current

####################################### Old/ Not Updated / Unused ######################################################

def cutoff(fourier):
    #fourier is the fourier coefficients:
    fourier = abs(fourier)
    max_coeff = max(fourier)
    sum = 0

    for i in range(len(fourier)):
        if fourier[i] !=max_coeff:
            sum += fourier[i]
        elif fourier[i] == max_coeff:
            sum+=0

    mean = sum/len(fourier)

    square_sample_mean = 0
    for j in range(len(fourier)):
        if fourier[i] !=max_coeff:
            square_sample_mean += pow((fourier[j] - mean), 2)
        elif fourier[i] == max_coeff:
            square_sample_mean +=0

    std_dev = np.sqrt(square_sample_mean/len(fourier))

    for l in range(len(fourier)):
        if fourier[l]> mean+std_dev:
            fourier[l] = fourier[l]
        elif fourier[l] <= mean+std_dev:
            fourier[l] = 0
    return fourier

def normalize(input_array):

   # min = np.min(input_array)
    average = np.mean(input_array)
    input_array -=average
    max = np.max(np.abs(input_array))

    new_array = input_array
    for i in range(len(input_array)):
            new_array[i] = (input_array[i])/max

    return new_array

#To Plot spectrums:
def get_frequency_spectra(daq_location, sample_rate, num_samples, gpib_address, #not up to date
                   amplitude, frequency, channel, odd_harmonics):
    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    wave = receive_raw_voltage(daq_location, sample_rate, num_samples) #receive the raw daq readout
    fourier_amplitude, fourier_frequency, phase, complex = fourier(wave, sample_rate, num_samples)
    print(fourier_amplitude)

    waveform_generator.write(f"OUTPUT{channel} OFF")
    waveform_generator.close()

    return fourier_amplitude, fourier_frequency
