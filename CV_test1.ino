#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <Adafruit_INA219.h>
#include <LiquidCrystal_I2C.h>

Adafruit_MCP4725 MCP4725;
Adafruit_INA219 ina219;

LiquidCrystal_I2C lcd(0x27, 16, 2);

uint32_t MCP4725_value;
float MCP4725_expected_output;  
float voltageRead = 0;
float Vout = 0, I = 0, P = 0;
const int buttonPin = 2;
int buttonState = 0;
int lastButtonState = 0;
int displayMode = 0;

void setup(void) {
  pinMode(buttonPin, INPUT_PULLUP); 
  Serial.begin(9600);


  MCP4725.begin(0x60);

  // Khởi tạo INA219
  if (!ina219.begin()) {
    Serial.println("Failed to initialize INA219.");
    while (1);
  }

  ina219.setCalibration_32V_2A();


  lcd.begin(16, 2); 
  lcd.setBacklight(1);
  lcd.print("MCP4725 & INA219");
  delay(2000);
  lcd.clear();
}

void loop(void) {
  buttonState = digitalRead(buttonPin);

  if (buttonState == LOW && lastButtonState == HIGH) {
    delay(50);
    displayMode = !displayMode; 
  }
  lastButtonState = buttonState;

  for (MCP4725_value = 2200; MCP4725_value >= 1500; MCP4725_value -= 20) {
    MCP4725_expected_output = (5.0 / 4096.0) * MCP4725_value;

    MCP4725.setVoltage(MCP4725_value, false);
    delay(500);

    Vout = ina219.getBusVoltage_V();
    I = ina219.getCurrent_mA() / 1000.0;
    P = Vout * I; 

   
    lcd.clear();

    if (displayMode == 0) {
      lcd.setCursor(0, 0);
      lcd.print("V_in: ");
      lcd.print(MCP4725_expected_output, 3);
      lcd.print(" V");
      
      lcd.setCursor(0, 1);
      lcd.print("I: ");
      lcd.print(I, 3);
      lcd.print(" A");
    } 
    else {
      lcd.setCursor(0, 0);
      lcd.print("Power: ");
      lcd.print(P, 3);
      lcd.print(" W");
    }

    Serial.print("V_in: ");
    Serial.print(MCP4725_expected_output, 3);
    Serial.print(" V, V_out: ");
    Serial.print(Vout, 3);
    Serial.print(" V, I: ");
    Serial.print(I, 3);
    Serial.print(" A, P: ");
    Serial.print(P, 3);
    Serial.println(" W");
  }
}
