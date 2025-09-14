# Electrochemical Sensor Measurement Module

## Overview
This project is my undergraduate thesis at Hanoi University of Science and Technology (HUST).  
The goal is to design and implement a **low-cost, customizable potentiostat system** capable of measuring voltage and current from a three-electrode electrochemical cell.

The system is built around an **Arduino microcontroller**, with integrated DAC (MCP4725), ADC (ADS1115), and JFET-input op-amps (LF412CN) for signal processing. It provides flexible waveform generation (triangular, square, differential pulse) and accurate current/voltage measurement for electrochemical experiments such as **Cyclic Voltammetry (CV)**, **Square Wave Voltammetry (SWV)**, and **Differential Pulse Voltammetry (DPV)**.

## Features
- Three-electrode potentiostat configuration (WE, RE, CE).
- Voltage sweep generation using **MCP4725 DAC** over I2C.
- High-resolution current/voltage measurement with **ADS1115 ADC** (16-bit).
- Low-noise signal amplification using **LF412CN dual JFET op-amp**.
- DC–DC buck-boost supply with **XL6009** to generate ±5V rails.
- PC software interface built with **Python**, enabling:
  - Parameter setup (scan rate, voltage range, cycles).
  - Real-time voltammogram plotting.
  - Data export to CSV.

## Hardware
- Arduino Uno R3 (MCU).
- MCP4725 (12-bit DAC).
- ADS1115 (16-bit ADC).
- LF412CN dual op-amp.
- XL6009 DC–DC converter (dual supply).
- Supporting passive components, prototype board.

## Software
- **Arduino IDE** for firmware (C/C++).
- **Python GUI** for user interface and data acquisition.
- **Visualization** of CV curves in real-time.

## Results
- Stable triangular waveform generation at multiple scan rates (100–200 mV/s).
- Verified linearity and accuracy of DAC–op-amp–cell system.
- Demonstrated basic CV experiments with NaCl solution (0.9%).
- Flexibility to extend for SWV and DPV methods.

## Future Development
- Improve PCB design for compactness and lower noise.
- Extend Python interface with advanced data analysis.
- Support for more electrochemical techniques (e.g., Chronoamperometry).
- Wireless communication (ESP32 / BLE) for portable use.

## Author
- **Le Minh Hoang**  
- Undergraduate Thesis, Hanoi University of Science and Technology (2025)  
- Contact: hoang.lm206641@sis.hust.edu.vn

---

### Note
This repository contains source code, hardware schematics, and documentation for academic and research purposes. Contributions and suggestions are welcome!
