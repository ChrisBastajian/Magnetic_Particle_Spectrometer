# Magnetic Particle Spectrometer Application (MPS App)

## Description

This application provides a user-friendly interface to control the Magnetic Particle Spectrometer at Oakland University, which is made up of dc biasing helholtz coils, drive coil, a receive coil, and a cancelation coil. It utilizes Python libraries such as `cutsomTkinter`, `matplotlib`, and `nidaqmx` to interact with hardware and visualize results.

---

## Getting Started

### Prerequisites

To run this application, you'll need Python 3.7+ installed along with the required dependencies. You can set up the environment by following the steps below.

### Installation

1. Clone this repository to your local machine:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2. Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up your **National Instruments DAQ** hardware if you're using a data acquisition system. Ensure that the channels are configured according to the script (`Dev3/ai0`, `Dev3/ai1`, etc.).

4. Configure your waveform generator and power supply by running:

    ```python
    import pyvisa
    
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    ```
5. Note that the waveform generator **KEYSIGHT 33500B** is connected via GPIB connection. The power supply **GWINSTEK PFR-100L** is connected via usb. More information can be found in the 'wave_gen.py' script
---
## Buttons and Their Functionality

### 1. Settings Button
   - **Description**: This button opens a dropdown menu for system and file management options.
   - **Functionality**: When clicked, it displays several options for the user to choose from:
     - **Save Results**
     - **Setup Analysis**
     - **Plot Settings**
   - **Usage**: 
     - The dropdown allows users to navigate and choose which action they want to perform.

#### 1.10. Dropdown Options:
   - **Save Results**: Allows users to save their results after performing an operation.
   - **Setup Analysis**: Opens a new window where users can input parameters for waveform generation, like amplitude, frequency, and triggering settings.
   - **Plot Settings**: Opens a settings window for adjusting plot settings, such as enabling zoom to 11 harmonics.

##### 1.11. Setup Analysis Window
   - **Description**: A window that allows the user to change multiple parameters related to the excitation (Waveform Parameters) and the aquisition (DAQ Card Input Channels).
   - **Functionality**:
     - The Waveform Parameter Frame Offers the following options:
       - **AC Amplitude**: Set the amplitude of the waveform (mT).
       - **Frequency**: Set the frequency of the waveform (Hz).
       - **Channel**: Select which waveform generator channel to apply the waveform settings.
       - **DC Offset**: Set the DC biasing field that is applied by Hemholtz Coils by setting the current (A).
       - **Harmonics**: Choose whether to include the full spectrum or to only look at harmonics of the fundamental frequency.
       - **Triggering**: Choose whether to enable triggering for waveform generation.
     - The DAQ Card Input Channels Frame Offers the following options:
       - **Signal Channel**: Set which channel to select for signal reception.
       - **Current Channel**: Set the Channel which the current sensor is connected to.
       - **Trigger Channel**: Set the channel that handles triggering based on a square signal with rising edge detection.
       - **Sample Rate**: Adjust the sample rate of data aquisition.
       - **Num Periods**: Select the number of periods that you want to be recorded (this increases the number of samples). 

   - **Usage**: 
     - After adjusting the settings, users can click a **Save Settings** button to store their configurations.

###### 1.12. Plot Settings Window
   - **Description**: A window for adjusting plot-related settings, such as zoom functionality.
   - **Functionality**:
     - Users can enable or disable the zoom feature for plotting the first 11 harmonics of the waveform.
     - This allows you to zoom into the fourrier frequency spectrum at all times for more convenience.
     - You may also filter out noise from the data and plot the curves by cosidering the effects of harmonics only and vice versa

##### 1.13. Saving Settings and Parameters
   - **Description**: After configuring the waveform and plot settings, users can save their changes.
   - **Functionality**: 
     -When you are done running your experiment. Click on this button to save the data that was recorded.
     -Make sure you do this for every sample you test (after clicking 'Run With Sample')

   - **Usage**: 
     - The arrays for the spectrums, raw daq readouts, harmonics data and more will be saved in a .mat file with parameters as well.
     - The following conventional names are utilized for the saved data:
        - background = background
        - signal = sample with background
        - sample = signal - background
        - xxxx_frequency_array_amplitude = complex coefficients an and bn
        - xxxx_frequency_array_magnitude = magnitude Cn = sqrt(an^2 + bn^2)
        - xxxx_frequency_array_phase = phase θn = arctan(bn/an)
        - xxxx_frequency_array_frequency = frequency array for specific "xxxx" component

---

### 2. **Auto - Calibrate Button**
   - **Description**: Initiates the automatic calibration process between the voltage (Vac) and magnetic field (μoH).
   - **Function**: When clicked, the system will send test signals from the waveform generator and calibrate based on the
                 current, I, being sent to the drive coil.

---

### 3. **Run Background Scan Button**
   - **Description**: Starts the background scan process.
   - **Function**: This button runs a background scan to gather baseline data containing noise that is later subtracted to get a pure sample-based signal.

---

### 4. **Run With Sample Button**
   - **Description**: Begins the data acquisition process with a sample present.
   - **Function**: This button starts the spectrometer in "sample mode" to take measurements when a sample is present. Run this method after a background scan is established.

---

### 5. **Run Live Frequency Array Button**
   - **Description**: Runs a live frequency array scan to adjust the cancellation coil as necessary.
   - **Function**: This button runs a live scan of the frequency spectrum, allowing the user to view real-time data on the frequency array.
                   Use this to manually turn/ adjust the cancellation coil as required and cancel the background before running other modes

---

### 6. **Stop Live Acquisition Button**
   - **Description**: Stops the ongoing live data acquisition.
   - **Function**: When clicked, this button the live frequency array display and turns off the waveform generator and power supply.

---

### 7. **Automated Mode Button**
   - **Description**: Opens the dropdown for automated mode settings.
   - **Function**: This button opens a menu where the user can set the system to an automated mode.
#### 7.1. Run With Static ac:
   - **Description**: Performs an automatic sweep of the dc output current while the ac field remains constant at preset value.
   - **Functionality**: 
     -When clicked, the system will sweep through a range of dc currents from 0A to 10A.
     -Harmonics data from the first till the eleventh harmonic will be recorded and plotted after the run
#### 7.2. Run With Static dc:
   - **Description**: Performs an automatic sweep of the ac output waveform amplitude while the dc field remains constant at preset value.
   - **Functionality**: 
     -When clicked, the system will sweep through a range of ac fields from 0 till 2.45V ~ 20mT
     -Harmonics data from the first till the eleventh harmonic will be recorded and plotted after the run
- **Note**: You may decide how many datapoints you want to save for each array by adjusting num_steps and saving the value (press the "Save Settings" button)
---

## Usage Instructions

- **Running the Application**: Once you have set up your environment, simply run the following command to start the application:
    ```bash
    python mps_app.py
    ```

---

