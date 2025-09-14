import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.signal import savgol_filter # <-- THÊM THƯ VIỆN NÀY

class CVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cyclic Voltammetry Controller")
        self.root.geometry("950x750")

        self.HANDSHAKE, self.START_PAUSE, self.READ_SWEEPTIME = 0, 4, 5
        self.READ_VLOW, self.READ_VHIGH, self.READ_NUM_SCAN, self.STOP = 6, 7, 8, 9
        self.arduino, self.connected = None, False
        self.data = {'time_ms': [], 'voltage': [], 'current': [], 'streaming': False}
        self.data_thread, self.stop_thread = None, False
        
        self.setup_gui()
        self.refresh_ports()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # ... (code giao diện Connection không đổi)
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=(0, 5))
        self.refresh_btn = ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=(0, 5))
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_arduino)
        self.connect_btn.grid(row=0, column=3, padx=(0, 5))
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=4, padx=(5, 0))

        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="5")
        params_frame.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        
        # --- Group Scan Parameters ---
        scan_params_frame = ttk.LabelFrame(params_frame, text="Scan Parameters")
        scan_params_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(scan_params_frame, text="TIA Feedback Resistor (kΩ):").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.rf_var = tk.DoubleVar(value=100.0)
        self.rf_entry = ttk.Entry(scan_params_frame, textvariable=self.rf_var, width=10)
        self.rf_entry.grid(row=1, column=0, sticky="w", pady=(0, 10), padx=5)

        ttk.Label(scan_params_frame, text="Scan Rate (mV/s):").grid(row=2, column=0, sticky="w", padx=5)
        self.scanrate_var = tk.DoubleVar(value=100.0)
        self.scanrate_scale = tk.Scale(scan_params_frame, from_=10, to=500, resolution=10, orient=tk.HORIZONTAL, variable=self.scanrate_var, command=self.update_scanrate)
        self.scanrate_scale.grid(row=3, column=0, sticky="ew", pady=2, padx=5)
        ttk.Label(scan_params_frame, text="Voltage Low (V):").grid(row=4, column=0, sticky="w", padx=5)
        self.vlow_var = tk.DoubleVar(value=-1.0)
        self.vlow_scale = tk.Scale(scan_params_frame, from_=-2.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.vlow_var, command=self.update_vlow)
        self.vlow_scale.grid(row=5, column=0, sticky="ew", pady=2, padx=5)
        ttk.Label(scan_params_frame, text="Voltage High (V):").grid(row=6, column=0, sticky="w", padx=5)
        self.vhigh_var = tk.DoubleVar(value=0.6)
        self.vhigh_scale = tk.Scale(scan_params_frame, from_=-1.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.vhigh_var, command=self.update_vhigh)
        self.vhigh_scale.grid(row=7, column=0, sticky="ew", pady=2, padx=5)
        ttk.Label(scan_params_frame, text="Number of Scans:").grid(row=8, column=0, sticky="w", padx=5)
        self.numscan_var = tk.IntVar(value=1)
        self.numscan_scale = tk.Scale(scan_params_frame, from_=1, to=10, resolution=1, orient=tk.HORIZONTAL, variable=self.numscan_var, command=self.update_numscan)
        self.numscan_scale.grid(row=9, column=0, sticky="ew", pady=2, padx=5)

        smoothing_frame = ttk.LabelFrame(params_frame, text="Graph Smoothing (Savitzky-Golay)")
        smoothing_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=10)

        self.smoothing_enabled = tk.BooleanVar(value=False)
        self.smoothing_check = ttk.Checkbutton(smoothing_frame, text="Enable Smoothing", variable=self.smoothing_enabled, command=self.update_plot)
        self.smoothing_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=5)

        ttk.Label(smoothing_frame, text="Window Size:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.smooth_window = tk.IntVar(value=15)
        self.smooth_window_scale = tk.Scale(smoothing_frame, from_=5, to=51, resolution=2, orient=tk.HORIZONTAL, variable=self.smooth_window, command=self.validate_smoothing_params)
        self.smooth_window_scale.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5)

        ttk.Label(smoothing_frame, text="Poly Order:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.smooth_poly = tk.IntVar(value=2)
        self.smooth_poly_scale = tk.Scale(smoothing_frame, from_=1, to=10, resolution=1, orient=tk.HORIZONTAL, variable=self.smooth_poly, command=self.validate_smoothing_params)
        self.smooth_poly_scale.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5)

        control_frame = ttk.Frame(params_frame)
        control_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        self.start_btn = ttk.Button(control_frame, text="Start/Pause", command=self.start_pause_scan, state='disabled')
        self.start_btn.pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_scan, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        self.reset_btn = ttk.Button(control_frame, text="Reset", command=self.reset_data)
        self.reset_btn.pack(side=tk.LEFT, padx=2)
        
        save_frame = ttk.LabelFrame(params_frame, text="Save Data", padding=5)
        save_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(save_frame, text="Filename:").grid(row=0, column=0, sticky="w")
        self.filename_var = tk.StringVar(value="voltammogram.csv")
        self.filename_entry = ttk.Entry(save_frame, textvariable=self.filename_var, width=20)
        self.filename_entry.grid(row=1, column=0, sticky="ew", padx=(0,5))
        self.save_btn = ttk.Button(save_frame, text="Save", command=self.save_data)
        self.save_btn.grid(row=1, column=1)
        save_frame.columnconfigure(0, weight=1)

        plot_frame = ttk.LabelFrame(main_frame, text="Voltammogram", padding="5")
        plot_frame.grid(row=1, column=1, sticky="nsew")
        
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.update_plot_labels()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

    def validate_smoothing_params(self, *args):
        """Ensure polynomial order is less than window size."""
        window = self.smooth_window.get()
        poly = self.smooth_poly.get()
        if poly >= window:
            self.smooth_poly.set(window - 1)
        self.update_plot()
        
    def update_plot(self, *args):
        if not self.data['voltage'] or not self.data['current']:
            return
        
        self.ax.clear()
        
        voltages = np.array(self.data['voltage'])
        currents = np.array(self.data['current'])

        if self.smoothing_enabled.get():
            window = self.smooth_window.get()
            poly = self.smooth_poly.get()

            if len(currents) > window:
                self.ax.plot(voltages, currents, 'r-', linewidth=1, alpha=0.3, label='Raw Data')
                smoothed_currents = savgol_filter(currents, window, poly)
                self.ax.plot(voltages, smoothed_currents, 'b-', linewidth=1.5, label='Smoothed Data')
                self.ax.legend()
            else:
                self.ax.plot(voltages, currents, 'b-', linewidth=1.5)
        else:
            self.ax.plot(voltages, currents, 'b-', linewidth=1.5)

        self.update_plot_labels()
        
        v_min, v_max = self.vlow_var.get(), self.vhigh_var.get()
        self.ax.set_xlim(min(v_min, v_max) - 0.1, max(v_min, v_max) + 0.1)
        
        if len(currents) > 0:
            c_min, c_max = np.min(currents), np.max(currents)
            c_range = c_max - c_min if c_max > c_min else 1.0
            pad = c_range * 0.1
            self.ax.set_ylim(c_min - pad, c_max + pad)

        self.canvas.draw()

    def update_plot_labels(self):
        self.ax.set_xlabel('Voltage (V)')
        self.ax.set_ylabel('Current (µA)')
        self.ax.set_title('Cyclic Voltammogram')
        self.ax.grid(True)
        self.fig.tight_layout()
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports: self.port_combo.set(ports[0])
    def connect_arduino(self):
        if self.connected:
            self.disconnect_arduino()
            return
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        try:
            self.arduino = serial.Serial(port, baudrate=115200, timeout=2)
            time.sleep(2)
            self.arduino.reset_input_buffer()
            self.arduino.write(bytes([self.HANDSHAKE]))
            response = self.arduino.readline()
            if b"Message received" in response:
                self.connected = True
                self.status_label.config(text="Connected", foreground="green")
                self.connect_btn.config(text="Disconnect")
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='normal')
                self.update_all_parameters()
            else:
                self.arduino.close()
                messagebox.showerror("Error", f"Arduino handshake failed. Response: {response.decode(errors='ignore')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
    def disconnect_arduino(self):
        if self.arduino and self.arduino.is_open:
            try:
                self.stop_thread = True
                if self.data_thread: self.data_thread.join(timeout=1)
                self.arduino.write(bytes([self.STOP]))
                time.sleep(0.1)
                self.arduino.close()
            except: pass
        self.connected = False
        self.data['streaming'] = False
        self.status_label.config(text="Disconnected", foreground="red")
        self.connect_btn.config(text="Connect")
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
    def send_to_arduino(self, command, value):
        if not self.connected: return
        try:
            message = bytes([command]) + (str(value) + "x").encode('ascii')
            self.arduino.write(message)
        except Exception as e:
            self.disconnect_arduino()
    def update_all_parameters(self):
        self.update_scanrate(); self.update_vlow(); self.update_vhigh(); self.update_numscan()
    def update_scanrate(self, *args):
        v_range = abs(self.vhigh_var.get() - self.vlow_var.get())
        rate_Vs = self.scanrate_var.get() / 1000.0
        if rate_Vs > 0: self.send_to_arduino(self.READ_SWEEPTIME, v_range / rate_Vs)
    def update_vlow(self, *args):
        self.send_to_arduino(self.READ_VLOW, self.vlow_var.get()); self.update_scanrate()
    def update_vhigh(self, *args):
        self.send_to_arduino(self.READ_VHIGH, self.vhigh_var.get()); self.update_scanrate()
    def update_numscan(self, *args):
        self.send_to_arduino(self.READ_NUM_SCAN, self.numscan_var.get())
    def start_pause_scan(self):
        if not self.connected: return
        self.send_to_arduino(self.START_PAUSE, "")
        self.data['streaming'] = not self.data['streaming']
        if self.data['streaming']:
            if not self.data_thread or not self.data_thread.is_alive():
                self.stop_thread = False
                self.data_thread = threading.Thread(target=self.data_collection_thread, daemon=True)
                self.data_thread.start()
            self.toggle_controls('disabled')
        else:
            self.toggle_controls('normal')
    def stop_scan(self):
        if not self.connected: return
        self.send_to_arduino(self.STOP, "")
        self.data['streaming'] = False; self.stop_thread = True
        self.toggle_controls('normal')
    def reset_data(self):
        self.data = {'time_ms': [], 'voltage': [], 'current': [], 'streaming': self.data.get('streaming', False)}
        self.ax.clear(); self.update_plot_labels(); self.canvas.draw()
    def data_collection_thread(self):
        self.arduino.reset_input_buffer()
        while not self.stop_thread and self.connected:
            if not self.data['streaming']: time.sleep(0.1); continue
            try:
                if self.arduino.in_waiting > 0:
                    line = self.arduino.readline()
                    if b'DONE' in line:
                        self.data['streaming'] = False; self.stop_thread = True
                        self.root.after(0, self.toggle_controls, 'normal'); break
                    try:
                        line_str = line.decode('ascii').strip()
                        parts = line_str.split(',')
                        if len(parts) == 3:
                            t_ms, v_sweep, v_tia = int(parts[0]), float(parts[1]), float(parts[2])
                            v_tia_offset_removed = v_tia - 2.545
                            rf_ohm = self.rf_var.get() * 1000.0
                            if rf_ohm == 0: continue
                            current_uA = (v_tia_offset_removed / rf_ohm) * 1e6
                            self.data['time_ms'].append(t_ms)
                            self.data['voltage'].append(v_sweep)
                            self.data['current'].append(current_uA)
                            if len(self.data['voltage']) % 20 == 0:
                                self.root.after(0, self.update_plot)
                    except (ValueError, IndexError, UnicodeDecodeError): pass
            except serial.SerialException: self.root.after(0, self.disconnect_arduino); break
        self.root.after(0, self.update_plot)
    def toggle_controls(self, state):
        for widget in [self.rf_entry, self.scanrate_scale, self.vlow_scale, self.vhigh_scale, self.numscan_scale]:
            widget.config(state=state)
    def save_data(self):
        if not self.data['voltage']: messagebox.showwarning("Warning", "No data to save"); return
        filename = self.filename_var.get();
        if not filename.endswith('.csv'): filename += '.csv'
        try:
            data_df = pd.DataFrame({'time (ms)': self.data['time_ms'], 'Voltage (V)': self.data['voltage'], 'Current (µA)': self.data['current']})
            with open(filename, 'w') as f:
                f.write(f"# TIA Feedback Resistor (kΩ): {self.rf_var.get()}\n")
                f.write(f"# Scan Rate (mV/s): {self.scanrate_var.get()}\n")
                f.write(f"# Voltage Low (V): {self.vlow_var.get()}\n")
                f.write(f"# Voltage High (V): {self.vhigh_var.get()}\n")
                f.write(f"# Number of Scans: {self.numscan_var.get()}\n\n")
            data_df.to_csv(filename, mode='a', index=False)
            messagebox.showinfo("Success", f"Data saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
    def on_closing(self):
        self.disconnect_arduino(); self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CVApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()