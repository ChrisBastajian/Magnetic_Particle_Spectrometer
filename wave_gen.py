import pyvisa
import time

def connect_waveform_generator(gpib_address):
    try:
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(f'GPIB::{gpib_address}')
        return inst
    except pyvisa.Error as e:
        print(f"Error connecting to the waveform generator: {e}")
        return None

def send_voltage(inst, voltage, frequency, channel):
    try:
        inst.write(f"SOURCE{channel}:VOLTage {voltage}Vpp")
        inst.write(f"SOURCE{channel}:FREQuency {frequency} HZ")
        inst.write(f"OUTPUT{channel} ON")
        inst.write(f"OUTPUT:SYNC{channel} ON")  # Enable synchronization for the channel
        inst.write(f"TRIGger:MODE:SOURCE{channel} IMM")  # Set trigger mode to immediate for the channel
        inst.write(f"TRIGger:SOURCE{channel} BUS")  # Set trigger source to bus for the channel
        print(f"Voltage set to {voltage} V")
        print(f"Output on Channel {channel} enabled with synchronization and triggering.")
    except pyvisa.Error as e:
        print(f"Error: {e}")
    time.sleep(0.01) #to receive better data (allows time for system to adapt)

#Turn off:
def turn_off(inst, channel):
    inst.write(f"OUTPUT{channel} OFF")
    inst.close()
#example
#waveform_generator = connect_waveform_generator(10)
#send_voltage(waveform_generator, 0.1, 1000,1)

#time.sleep(5)

#waveform_generator.write(f"OUTPUT{1} OFF")
#waveform_generator.close()

################################################################################################################################################
#For DC Power Supply:

rm = pyvisa.ResourceManager()
print(rm.list_resources())

def connect_power_supply(serial_address):
    try:
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(serial_address)
        inst.baud_rate = 9600  # Set the baud rate (example: 9600)
        inst.data_bits = 8
        #inst.parity = pyvisa.constants.Parity.none  # Set parity (example: none)
        #inst.stop_bits = pyvisa.constants.StopBits.one  # Set stop bits (example: one)
        #inst.timeout = 5000  # Set timeout (example: 5000 ms)
        return inst
    except pyvisa.Error as e:
        print(f"Error connecting to the power supply: {e}")
        return None

def send_dc_voltage(inst, voltage, current):
    try:
        # Sending the command to set the voltage level
        inst.write(f":SOURce:VOLTage:LEVel {voltage}")  # Set the voltage level
        inst.write(f":SOURce:CURRent:LEVel {current}")
        inst.write(":OUTPut:STATe ON")  # Turn on the output
        #print(f"DC voltage set to {voltage} V")

    except pyvisa.Error as e:
        print(f"Error: {e}")
    time.sleep(0.01)  # Allow some time for the system to adapt

def turn_off_dc_output(inst):
    try:
        inst.write(":OUTPut:STATe OFF")  # Turn off the output
        print("Output turned off")
    except pyvisa.Error as e:
        print(f"Error: {e}")

# Example usage

# Connect to the power supply via serial port
#power_supply = connect_power_supply('ASRL5::INSTR')

#if power_supply:
#   send_dc_voltage(power_supply, 5, 0.01)  # Set voltage to 2V

#   time.sleep(20) #keep voltage applied for 5 seconds

#   turn_off_dc_output(power_supply)  # Turn off the output
#   power_supply.close()

def DC_offset(current):
    power_supply = connect_power_supply('ASRL5::INSTR') #connecting via usb
    voltage = 12 #volts since thisis the max of the power supply
    if power_supply:
        send_dc_voltage(power_supply, voltage, current)
        return power_supply