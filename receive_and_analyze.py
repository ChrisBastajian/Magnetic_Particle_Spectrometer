import numpy as np
import nidaqmx
import wave_gen
from nidaqmx.constants import AcquisitionType, Edge
import matplotlib.pyplot as plt


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
    power_supply = wave_gen.connect_power_supply('ASRL5::INSTR') #connecting by usb
    voltage = 12 #volts since thisis the max of the power supply
    if power_supply:
        wave_gen.send_dc_voltage(power_supply, voltage, current)
        return power_supply

#USED IN main.py only!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def background_subtraction(daq_location, sense_location, sample_rate, num_samples, gpib_address, amplitude, frequency, channel, isclean):
    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    ##################### Eventually add a live frequency domain for cancellation coil before measuring background#######

    background = receive_raw_voltage(daq_location, sample_rate, num_samples) #receive the background
    background_magnitude, background_frequency = fourier(background, sample_rate, num_samples)
    #background_phase = phase(daq_location, sense_location, sample_rate, frequency)
    background_phase = 237.42*(np.pi/180)

    #Turn the waveform generator off:
    waveform_generator.write(f"OUTPUT{channel} OFF")

    #Let user start the second signal to measure SPIO charactristics
    insert_sample = input("Did you insert the sample? ")

    if insert_sample == 'yes':
        wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

        #Receive signal
        signal = receive_raw_voltage(daq_location, sample_rate, num_samples)
        signal_magnitude, signal_frequency = fourier(signal, sample_rate, num_samples)

        # Get the phase:
        sample_with_background_phase = phase(daq_location, sense_location, sample_rate,
                                             frequency)  # pure phase readout when sample is in

        #Get the rms current
        i_rms = get_rms_current(sense_location, fs=sample_rate, num_samples=num_samples)

    else:
        print("Okay")
        back_subtraction, signal_frequency = -99, -99 #will be used as error values

    #Turn off waveform generator and close:
    wave_gen.turn_off(waveform_generator, channel)
    sample_phase = sample_with_background_phase-background_phase

    # subtract background:
    back_subtraction = np.abs(signal_magnitude - background_magnitude)
    sample_phase = (2*np.pi)-sample_phase


    return back_subtraction, signal_frequency, i_rms, sample_phase, signal

#Used in MPS_app.py:
def get_background(daq_location, source_location, trigger_location, sample_rate, num_periods, gpib_address,
                   amplitude, frequency, channel, dc_current):
    num_pts_per_period = sample_rate/ frequency #Fs/F_drive
    num_samples = int(num_periods * num_pts_per_period)

    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    #Connect to the DC power supply and send the current through the helmholtz coils:
    power_supply = DC_offset(dc_current)

    background = receive_raw_voltage(daq_location, sample_rate, num_samples) #receive the background (raw daq readout)

    #Turn the waveform generator and power supply off:
    wave_gen.turn_off(waveform_generator, channel)
    if power_supply:
        wave_gen.turn_off_dc_output(power_supply)
        power_supply.close()

    background_amplitude, background_frequency = fourier(background, sample_rate, num_samples)
    background_magnitude = abs(background_amplitude)
    #Apply a mask for the background magnitude if needed:
    #background_magnitude = cutoff(background_amplitude)

    background_phase = 0

    return num_samples, background_magnitude, background_frequency, background_phase, background

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

#USED IN MPS_app.py:
def get_sample_signal(daq_location, sense_location, trigger_location, sample_rate, num_periods, gpib_address, amplitude,
                      frequency, channel, dc_current, background_magnitude, isClean):
    arduino_COM = 'COM4'
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

    signal_with_background_amplitude, signal_frequency = fourier(signal_with_background, sample_rate,
                                                                 num_samples)

    #signal_with_background_magnitude = cutoff(signal_with_background_amplitude)
    signal_with_background_magnitude = abs(signal_with_background_amplitude)

    # subtract background:
    sample_magnitude = np.abs(signal_with_background_magnitude - background_magnitude)

    #If odd harmonics are selected:
    if isClean:
        sample_magnitude = odd_harmonics(sample_magnitude, signal_frequency, frequency, sample_rate) #will give the magnitudes of the odd harmonics only

    #sample_phase = signal_with_background_phase  # noticed that background was very well cancelled that the
                                                # phase wouldn't make a difference...
    sample_phase = 0
    return num_samples, sample_magnitude, signal_frequency, signal_with_background, sample_phase, i_rms

def fourier(waveform, sample_rate, num_samples):
    #Find real and imaginary amplitudes
    fourier_amplitude = np.fft.fft(waveform)/num_samples #for actual magnitude use np.abs(np.fft.fft(wavefomr)
                                                            # #divide by num_samples to normalize

    #Setup a frequency array for the amplitudes
    fourier_frequency = np.fft.fftfreq(num_samples, d = 1/sample_rate) #array of length equal to the
    fourier_frequency = np.abs(fourier_frequency)                      # number of samples and spaced by
                                                                        # the period = 1/sample rate

    # setup a mask to get rid of low frequencies:
    mask_low = (np.abs(fourier_frequency) >= 500)

    max_frequency = sample_rate//2  #the max frequency the daq card can detect

    # Create a mask for frequencies <= the max the daq card can detect
    mask_high = (np.abs(fourier_frequency) <= max_frequency)
    mask = mask_low & mask_high

    #Turn into only positive frequencies and apply yhe mask:
    fourier_frequency = fourier_frequency[mask]
    fourier_magnitude = fourier_amplitude[mask] #fourier_magnitude = abs(fourier_magnitude[mask])

    return fourier_magnitude, fourier_frequency

def reconstruct_and_integrate(num_samples, frequency, amplitude, f_drive, phase=0):
    coefficients = np.abs(amplitude)
    f = frequency[:num_samples]
    coeff = coefficients[:num_samples]
    omega = 2 * np.pi * f

    t = np.linspace(0, 1 / f_drive, 10000)
    integral = np.zeros(len(t))
    recon = np.zeros(len(t))

    for i in range(len(coeff)):
        if omega[i] != 0:
            #integral -= (coeff[i] / omega[i]) * np.cos((omega[i] * t))
           integral += (coeff[i] / omega[i]) * np.cos((omega[i] * t) - (np.pi/2))
           recon += coeff[i] * np.cos((omega[i] * t))
           # recon += coeff[i] * np.sin((omega[i] * t))
    #shifting them to get integral from low to high (just for visual purposes):
    n = len(t)
    if phase ==0:
        shift = n//4
    else:
        shift = (n*phase//(np.pi))+n//2
    recon = np.roll(recon, shift)
    integral = np.roll(integral, shift)

    return recon, integral

def general_reconstruction(amplitude, frequency):
    t= np.linspace(0, 1/frequency, 10000)

    recon = np.zeros(len(t))
    omega = 2 * np.pi * frequency
    recon = amplitude * np.cos(omega * t - (np.pi))

    return recon

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


#To Plot spectrums:
def get_frequency_spectra(daq_location, sample_rate, num_samples, gpib_address,
                   amplitude, frequency, channel, odd_harmonics):
    #Connect the waveform generator and send a signal for background measurement
    waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
    wave_gen.send_voltage(waveform_generator, amplitude, frequency, channel)

    wave = receive_raw_voltage(daq_location, sample_rate, num_samples) #receive the raw daq readout
    fourier_amplitude, fourier_frequency = fourier(wave, sample_rate, odd_harmonics, num_samples)
    print(fourier_amplitude)

    waveform_generator.write(f"OUTPUT{channel} OFF")
    waveform_generator.close()

    return fourier_amplitude, fourier_frequency

def dMdH(M, H): #differentiate M with respect to H and keep it the same length to plot
    dMdH = np.gradient(M, edge_order= 2)/np.gradient(H, edge_order= 2)
    dMdH[0]=0
    dMdH[-1]=0 #to get rid of unnecessary artifacts

    return dMdH


from scipy.signal import find_peaks

def phase(output_daq_location, source_daq_location, sample_rate, f_drive):

    #Need to record one period of both waveforms:
    num_samples = sample_rate//f_drive

    iterations = 200 #num of iterations for averaging
    samples_shift = np.zeros(iterations)

    for i in range(iterations):
        # Initialize task
        with nidaqmx.Task() as task:
            # Add channels
            task.ai_channels.add_ai_voltage_chan(output_daq_location)
            task.ai_channels.add_ai_voltage_chan(source_daq_location)

            # Configure timing
            task.timing.cfg_samp_clk_timing(sample_rate, samps_per_chan=num_samples, sample_mode=AcquisitionType.FINITE)

            # Read data
            waveform = task.read(number_of_samples_per_channel=num_samples)

            # Extract signals
            output = np.array(waveform[0])
            source = np.array(waveform[1])

        #Find max of both waveforms:
        max_source = max(source)
        max_output = max(output)

        for j in range(num_samples):
            if source[j] == max_source:
                loc_source = j
            if output[j] == max_output:
                loc_output = j

        samples_shift[i] = loc_source-loc_output
        if samples_shift[i] > 0:
            samples_shift[i] = num_samples - samples_shift[i]

    samples_shift_mean = np.median(samples_shift) #get the average of the samples shift

    plt.plot(source, label='source')
    plt.plot(output, label='output')
    plt.legend()

    phase_shift = (samples_shift_mean/num_samples)*(2*np.pi)

    # Convert phase shift to degrees (optional)
    phase_shift_degrees = np.degrees(phase_shift)

    print(phase_shift_degrees)
    return phase_shift