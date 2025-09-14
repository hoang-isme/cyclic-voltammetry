#include <Wire.h>
#include <Math.h>
#include <Adafruit_MCP4725.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

#define MCP4725_ADDR 0x60

const int HANDSHAKE = 0;
const int START_PAUSE = 4; 
const int READ_SWEEPTIME = 5;
const int READ_VLOW = 6;
const int READ_VHIGH = 7;
const int READ_NUM_SCAN = 8;
const int STOP = 9;

bool continue_scan;
float sweeptime = 20; //seconds
float vLow = -1;
float vHigh = 0.6; 
int numScan = 1; 
float vLow_comp = vLow + 1;
float vHigh_comp = vHigh + 1;

const float ADC_CONVERSION_FACTOR = 4.096 / 32767.0;

Adafruit_MCP4725 dac;

void setup() {
  dac.begin(MCP4725_ADDR);
  ads.setGain(GAIN_ONE); 
  
  Serial.begin(115200);
  
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS1115. Check wiring.");
    while (1);
  }
  
  vLow_comp = vLow + 1;
  vHigh_comp = vHigh + 1;
  Serial.println("Arduino Ready.");
}

bool check_start_pause_cmd() {
  if (Serial.available() > 0) {
    int inByte = Serial.read();
    if (inByte == START_PAUSE) {
      continue_scan = !continue_scan;
    }
    if (inByte == STOP) {
      return false;
    }
    return true;
  }
  return true;
}

void sweep_voltage() {
  for (int scan_i = 1 ; scan_i <= numScan ; scan_i++) {
    uint32_t dac_vLow = uint32_t(round(vLow_comp / 5.0 * 4095.0));
    uint32_t dac_vHigh = uint32_t(round(vHigh_comp / 5.0 * 4095.0));
    
    // Quét lên
    for (uint32_t counter_up = dac_vLow; counter_up < dac_vHigh; counter_up++) {
      if (continue_scan) {
        dac.setVoltage(counter_up, false);
        delay(sweeptime / 2.0 / (dac_vHigh - dac_vLow) * 1000.0);
        
        int16_t raw_v_Sweep = ads.readADC_SingleEnded(0);
        int16_t raw_v_TIA = ads.readADC_SingleEnded(1);
        float voltage_Sweep = raw_v_Sweep * ADC_CONVERSION_FACTOR - 1.0; // Trừ offset 1V
        float voltage_TIA = raw_v_TIA * ADC_CONVERSION_FACTOR;

        // *** THAY ĐỔI: Thêm log để debug trên Serial Monitor của Arduino ***
        Serial.print("DEBUG -> RawSweep: ");
        Serial.print(raw_v_Sweep);
        Serial.print(" | V_Sweep: ");
        Serial.print(voltage_Sweep, 4);
        Serial.print(" | RawTIA: ");
        Serial.print(raw_v_TIA);
        Serial.print(" | V_TIA: ");
        Serial.println(voltage_TIA, 4);

        unsigned long timeMilliseconds = millis();
        Serial.println(String(timeMilliseconds) + "," + String(voltage_Sweep, 4) + "," + String(voltage_TIA, 4));

        if (check_start_pause_cmd() == false) { dac.setVoltage(uint32_t(819), false); return; }
      } else {
        while (continue_scan == false) {
          if (check_start_pause_cmd() == false) { dac.setVoltage(uint32_t(819), false); return; }
        }
      }
    }

    // Quét xuống
    for (uint32_t counter_dn = dac_vHigh; counter_dn > dac_vLow; counter_dn--) {
       if (continue_scan) {
        dac.setVoltage(counter_dn, false);
        delay(sweeptime / 2.0 / (dac_vHigh - dac_vLow) * 1000.0);
        
        int16_t raw_v_Sweep = ads.readADC_SingleEnded(0);
        int16_t raw_v_TIA = ads.readADC_SingleEnded(1);
        float voltage_Sweep = raw_v_Sweep * ADC_CONVERSION_FACTOR - 1.0;
        float voltage_TIA = raw_v_TIA * ADC_CONVERSION_FACTOR;

        Serial.print("DEBUG -> RawSweep: ");
        Serial.print(raw_v_Sweep);
        Serial.print(" | V_Sweep: ");
        Serial.print(voltage_Sweep, 4);
        Serial.print(" | RawTIA: ");
        Serial.print(raw_v_TIA);
        Serial.print(" | V_TIA: ");
        Serial.println(voltage_TIA, 4);

        unsigned long timeMilliseconds = millis();
        // Gửi dữ liệu cho Python
        Serial.println(String(timeMilliseconds) + "," + String(voltage_Sweep, 4) + "," + String(voltage_TIA, 4));

        if (check_start_pause_cmd() == false) { dac.setVoltage(uint32_t(819), false); return; }
      } else {
        while (continue_scan == false) {
          if (check_start_pause_cmd() == false) { dac.setVoltage(uint32_t(819), false); return; }
        }
      }
    }
  }
  dac.setVoltage(uint32_t(819), false);
  Serial.println("DONE SWEEPING");
}

void loop() {
  if (Serial.available() > 0) {
    int inByte = Serial.read();
    switch(inByte) {
      case START_PAUSE:
        continue_scan = true;
        sweep_voltage();
        break;
      case READ_SWEEPTIME:
        sweeptime = Serial.readStringUntil('x').toFloat();
        break;
      case READ_VLOW:
        vLow = Serial.readStringUntil('x').toFloat();
        vLow_comp = vLow + 1;
        break;
      case READ_VHIGH:
        vHigh = Serial.readStringUntil('x').toFloat();
        vHigh_comp = vHigh + 1;
        break;
      case READ_NUM_SCAN:
        numScan = Serial.readStringUntil('x').toInt();
        break;
      case HANDSHAKE:
        if (Serial.availableForWrite()) {
          Serial.println("Message received.");
        }
        break;
    }
  }
}