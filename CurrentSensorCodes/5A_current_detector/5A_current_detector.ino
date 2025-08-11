#define VIN A0
const float Vcc = 5.0;
const float VQ = 0.5 * Vcc;
const double sensitivity = 0.185; // in V/A

double voltages_raw[50];
double currents[50];
double squares[50];
double squares_added = 0;

double mean_square, rms_current;
int i = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  voltages_raw[i] = (5.0 / 1023.0) * analogRead(VIN);
  double voltage = voltages_raw[i] - VQ; //remove quiescent voltage in datasheet
  currents[i] = voltage / sensitivity;
  
  //Serial.println(voltages_raw[i]);
  // Print voltage and current
  //Serial.print("Voltage: ");
  //Serial.println(voltage, 2);
  //Serial.print("\tCurrent: ");
  //Serial.print(currents[i], 2);
  
  // Calculate RMS current
  squares[i] = pow(currents[i], 2);
  squares_added += squares[i];
  mean_square = squares_added / (i + 1);
  rms_current = sqrt(mean_square);
  
  i++;
  if (i >= 50) {
    i = 0; // Reset the index to loop through the array
    squares_added = 0; // Reset for the next set of calculations
    Serial.print("I(rms): ");
    Serial.println(rms_current, 2);
  }
  
  delay(10); 
}
