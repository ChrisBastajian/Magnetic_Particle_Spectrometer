# Magnetic Particle Spectrometer Application (MPS App)

## Description

This application provides a user-friendly interface to control the Magnetic Particle Spectrometer at Oakland University, which is made up of a drive coil and a receive coil. It utilizes Python libraries such as `cutsomTkinter`, `matplotlib`, and `nidaqmx` to interact with hardware and visualize results.

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

### 4. Configure your waveform generator and power supply by running:

```python
import pyvisa

rm = pyvisa.ResourceManager()
print(rm.list_resources())
```
---
## Buttons and Their Functionality

### 1. **File Button**
   - **Description**: Opens a dropdown menu for file management (e.g., load/save data).
   - **Function**: When clicked, this button triggers the file handling interface, where the user can load or save data files.

---

### 2. **Auto - Calibrate Button**
   - **Description**: Initiates the automatic calibration process.
   - **Function**: This button starts the calibration routine for the spectrometer, adjusting the system to ensure accurate measurements. Typically, this involves adjusting the magnetic field or correcting signal distortion.

---

### 3. **Run Background Scan Button**
   - **Description**: Starts the background scan process.
   - **Function**: This button runs a background scan to gather baseline data that can be used to subtract noise from measurements during active data collection.

---

### 4. **Run With Sample Button**
   - **Description**: Begins the data acquisition process with a sample present.
   - **Function**: This button starts the spectrometer in "sample mode" to take measurements when a sample is present. It collects data based on predefined parameters such as frequency and amplitude.

---

### 5. **Run Live Frequency Array Button**
   - **Description**: Runs a live frequency array scan to analyze the frequency response of the system.
   - **Function**: This button runs a live scan of the frequency spectrum, allowing the user to view real-time data on the frequency array. Useful for observing how the system responds to varying frequencies.

---

### 6. **Stop Live Acquisition Button**
   - **Description**: Stops the ongoing live data acquisition.
   - **Function**: When clicked, this button halts the live data acquisition process, stopping the ongoing signal measurement and analysis.

---

### 7. **Automated Mode Button**
   - **Description**: Opens the dropdown for automated mode settings.
   - **Function**: This button opens a menu where the user can set the system to an automated mode, allowing for predefined actions and measurements to be taken automatically based on user-selected parameters.

---

## Usage Instructions

- **Running the Application**: Once you have set up your environment, simply run the following command to start the application:
    ```bash
    python mps_app.py
    ```

- **Navigating the Interface**: Use the buttons described above to interact with the application. Each button triggers specific functionalities like calibration, data collection, and background subtraction.

---

## License
*(Add licensing information here, such as MIT License, GPL, or proprietary license.)*
