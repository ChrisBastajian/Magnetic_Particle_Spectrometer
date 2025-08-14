#define VIN A0
const float Vcc = 5.0;
const float VQ = 0.5 * Vcc;
float voltages[50], currents[50], voltages_raw[50];
float squares[50], squaresV[50];
float squares_added = 0;
float squares_addedV = 0;
float mean_square, rms_current, mean_squareV, rms_voltage;
int i=0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}


void loop() {
  // put your main code here, to run repeatedly:
  double sensitivity = 0.185; // in V/A

  //finding instantaneous current:
  voltages_raw[i] = (5.0 / 1023.0)* analogRead(VIN);
  voltages[i] = voltages_raw[i] -VQ;
  currents[i] = voltages[i]/sensitivity; 

  //Serial.println(currents[i], 2);

  //Finding rms current:
  squares[i] = pow(currents[i], 2);
  squares_added += squares[i];
  mean_square = squares_added/ (i+1);
  rms_current = sqrt(mean_square);
  
  
  //Finding rms voltage:
  //squaresV[i] = pow(voltages[i], 2);
  //squares_addedV += squares[i];
  //mean_squareV = squares_addedV/(i+1);
  //rms_voltage = sqrt(mean_squareV);
  //Serial.print("Vrms: ");
  //Serial.println(rms_voltage);
  
  i++;
  if (i ==51){
    Serial.print("I(rms): ");
    Serial.println(rms_current);
  }
  delay(10);
  
}
