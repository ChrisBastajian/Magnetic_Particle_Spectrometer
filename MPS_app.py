import customtkinter as ctk
from tkinter import Listbox, filedialog
import matplotlib.pyplot as plt
import receive_and_analyze as analyze
import numpy as np
import wave_gen
import nidaqmx
import time
import threading

from scipy.io import savemat
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("light_gray")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i_dc = None
        self.mode = None
        self.harmonics = None
        self.slope = 10.339
        self.zoom_to_11_enabled = True
        self.sample_frequency_array_magnitude = None
        self.run = 0
        self.title("MPS App")
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()

        self.geometry(f"{self.width}x{self.height}")
        self.configure(fg="#333333")

        # Initialize parameters with default values
        self.ac_amplitude = 25  # Default AC Amplitude (mT)
        self.frequency = 1000  # Default Frequency (Hz)
        self.channel = "1"
        self.dc_offset = 0
        self.only_odd_harmonics = False
        self.triggering_enabled = False

        # DAQ Card Parameters
        self.daq_signal_channel = "Dev3/ai0"
        self.daq_current_channel = "Dev3/ai1"
        self.daq_trigger_channel = "/Dev3/pfi0"
        self.sample_rate = 100000  #Hz
        self.num_periods = 100

        ########### Title bar frame ########################
        self.title_bar = ctk.CTkFrame(self, height=self.height // 18, width=self.width, corner_radius=0,
                                      fg_color='gray')
        self.title_bar.place(x=self.width // 2, y=self.height // 36, anchor="center")

        # Button properties
        btn_width = int(self.width * 0.10)  # Slightly wider to accommodate longer labels
        btn_height = int(self.height * 0.04)
        btn_y = self.height // 36

        # Total number of buttons (including File)
        num_buttons = 8
        total_spacing_width = self.width * 0.8  # spread buttons across 80% of window
        start_x = (self.width - total_spacing_width) / 2
        btn_spacing = total_spacing_width / (num_buttons - 1)

        # Place each button with consistent spacing
        self.title_bar.file = ctk.CTkButton(self.title_bar, text="File",
                                            font=('Arial', int(self.height * 0.018)),
                                            command=self.open_files_dropdown,
                                            width=btn_width, height=btn_height)
        self.title_bar.file.place(x=start_x + btn_spacing * 0, y=btn_y, anchor='center')

        self.title_bar.calibrate = ctk.CTkButton(self.title_bar, text="Auto - Calibrate",
                                                 font=('Arial', int(self.height * 0.018)),
                                                 command=self.calibrate_H_V,
                                                 width=btn_width, height=btn_height)
        self.title_bar.calibrate.place(x=start_x + btn_spacing * 1, y=btn_y, anchor='center')

        self.title_bar.background_sub = ctk.CTkButton(self.title_bar, text="Run Background Scan",
                                                      font=('Arial', int(self.height * 0.018)),
                                                      command=self.run_background_subtraction,
                                                      width=btn_width, height=btn_height)
        self.title_bar.background_sub.place(x=start_x + btn_spacing * 2, y=btn_y, anchor='center')

        self.title_bar.get_results = ctk.CTkButton(self.title_bar, text="Run With Sample",
                                                   font=('Arial', int(self.height * 0.018)),
                                                   command=self.run_with_sample,
                                                   width=btn_width, height=btn_height)
        self.title_bar.get_results.place(x=start_x + btn_spacing * 3, y=btn_y, anchor='center')

        self.title_bar.live_frequency = ctk.CTkButton(self.title_bar, text="Run Live Frequency Array",
                                                      font=('Arial', int(self.height * 0.018)),
                                                      command=self.run_live_frequency_array,
                                                      width=btn_width, height=btn_height)
        self.title_bar.live_frequency.place(x=start_x + btn_spacing * 4, y=btn_y, anchor='center')

        self.title_bar.stop = ctk.CTkButton(self.title_bar, text="Stop Live Acquisition", hover_color="red",
                                            font=('Arial', int(self.height * 0.018)),
                                            command=self.stop_acquisition,
                                            width=btn_width, height=btn_height)
        self.title_bar.stop.place(x=start_x + btn_spacing * 5, y=btn_y, anchor='center')

        self.title_bar.auto_mode = ctk.CTkButton(self.title_bar, text='Automated Mode',
                                                 font=('Arial', int(self.height * 0.018)),
                                                 command=self.open_auto_mode_dropdown,
                                                 width=btn_width, height=btn_height)
        self.title_bar.auto_mode.place(x=start_x + btn_spacing * 6, y=btn_y, anchor='center')

        self.title_bar.get_stepped_data = ctk.CTkButton(self.title_bar, text="Run Stepped",
                                                        font=('Arial', int(self.height * 0.018)),
                                                        command=self.run_stepped,
                                                        width=btn_width, height=btn_height)
        self.title_bar.get_stepped_data.place(x=start_x + btn_spacing * 7, y=btn_y, anchor='center')

        ############### Figures ########################
        x_fig = 5.5
        y_fig = 4

        self.fig1 = plt.figure(figsize=(x_fig, y_fig))
        self.ax1 = self.fig1.add_subplot(111)

        self.fig2 = plt.figure(figsize=(x_fig, y_fig))
        self.ax2 = self.fig2.add_subplot(111)

        self.fig3 = plt.figure(figsize=(x_fig, y_fig))
        self.ax3 = self.fig3.add_subplot(111)

        self.fig4 = plt.figure(figsize=(x_fig, y_fig))
        self.ax4 = self.fig4.add_subplot(111)

        self.fig5 = plt.figure(figsize=(x_fig, y_fig))
        self.ax5 = self.fig5.add_subplot(111)

        self.fig6 = plt.figure(figsize=(x_fig, y_fig))
        self.ax6 = self.fig6.add_subplot(111)

        y_canvas = [int(self.height *0.25), int(self.height * 0.7)]
        x_canvas = [int(self.width * 0.17), int(self.width * 0.5), int(self.width * 0.83)]

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self)
        self.canvas1.get_tk_widget().place(x=x_canvas[0], y=y_canvas[0], anchor='center')

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self)
        self.canvas2.get_tk_widget().place(x=x_canvas[1], y=y_canvas[0], anchor='center')

        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self)
        self.canvas3.get_tk_widget().place(x=x_canvas[2], y=y_canvas[0], anchor='center')

        self.canvas4 = FigureCanvasTkAgg(self.fig4, master=self)
        self.canvas4.get_tk_widget().place(x=x_canvas[0], y=y_canvas[1], anchor='center')

        self.canvas5 = FigureCanvasTkAgg(self.fig5, master=self)
        self.canvas5.get_tk_widget().place(x=x_canvas[1], y=y_canvas[1], anchor='center')

        self.canvas6 = FigureCanvasTkAgg(self.fig6, master=self)
        self.canvas6.get_tk_widget().place(x=x_canvas[2], y=y_canvas[1], anchor='center')

        # For each canvas
        self.toolbar1 = NavigationToolbar2Tk(self.canvas1, self)
        self.toolbar1.update()
        self.toolbar1.place(x=x_canvas[0]-int(self.width *0.075), y=y_canvas[0] + int(self.height * 0.22), anchor='center')

        self.toolbar2 = NavigationToolbar2Tk(self.canvas2, self)
        self.toolbar2.update()
        self.toolbar2.place(x=x_canvas[1]-int(self.width *0.075), y=y_canvas[0] + int(self.height * 0.22), anchor='center')

        self.toolbar3 = NavigationToolbar2Tk(self.canvas3, self)
        self.toolbar3.update()
        self.toolbar3.place(x=x_canvas[2]-int(self.width *0.075), y=y_canvas[0] + int(self.height * 0.22), anchor='center')

        self.toolbar4 = NavigationToolbar2Tk(self.canvas4, self)
        self.toolbar4.update()
        self.toolbar4.place(x=x_canvas[0]-int(self.width *0.075), y=y_canvas[1] + int(self.height * 0.22), anchor='center')

        self.toolbar5 = NavigationToolbar2Tk(self.canvas5, self)
        self.toolbar5.update()
        self.toolbar5.place(x=x_canvas[1]-int(self.width *0.075), y=y_canvas[1] + int(self.height * 0.22), anchor='center')

        self.toolbar6 = NavigationToolbar2Tk(self.canvas6, self)
        self.toolbar6.update()
        self.toolbar6.place(x=x_canvas[2]-int(self.width *0.075), y=y_canvas[1] + int(self.height * 0.22), anchor='center')

        # Add a button for each figure to open the plot in a new window
        self.add_plot_button(self.fig1, x_canvas[0], y_canvas[0])
        self.add_plot_button(self.fig2, x_canvas[1], y_canvas[0])
        self.add_plot_button(self.fig3, x_canvas[2], y_canvas[0])
        self.add_plot_button(self.fig4, x_canvas[0], y_canvas[1])
        self.add_plot_button(self.fig5, x_canvas[1], y_canvas[1])
        self.add_plot_button(self.fig6, x_canvas[2], y_canvas[1])

        #Clear Comparison Button:
        self.clear_plot_button(self.ax1, x_canvas[0], y_canvas[0])
        self.clear_plot_button(self.ax2, x_canvas[1], y_canvas[0])
        self.clear_plot_button(self.ax3, x_canvas[2], y_canvas[0])
        self.clear_plot_button(self.ax4, x_canvas[0], y_canvas[1])
        self.clear_plot_button(self.ax5, x_canvas[1], y_canvas[1])
        self.clear_plot_button(self.ax6, x_canvas[2], y_canvas[1])

    ################ Functions for user interface ###########################
    def clear_plot_button(self, ax, x, y):
        button = ctk.CTkButton(self, text="Clear", command=lambda: self.clear_plot(ax), width=0)
        button.place(x=x+int(self.width *0.1), y=y + int(self.height * 0.22), anchor="center")

    def clear_plot(self, ax):
        if ax is self.ax6: #if we are resetting ax6 which contains the MH curves compared
            self.run=0

        ax.clear()
        ax.figure.canvas.draw_idle()

    def add_plot_button(self, figure, x, y):
        button = ctk.CTkButton(self, text="View Full Plot", command=lambda: self.open_plot_window(figure), width=0)
        button.place(x=x+int(self.width *0.05), y=y + int(self.height * 0.22), anchor="center")

    def open_plot_window(self, figure):
        # Create a new top-level window with customtkinter
        new_window = ctk.CTkToplevel(self)
        new_window.title("Full Plot")
        new_window.geometry(f"{self.width}x{self.height}")
        new_window.attributes("-topmost", True)

        # Create a CTkFrame for better layout management
        frame = ctk.CTkFrame(new_window, bg_color="gray", fg_color="gray", width=self.width, height=self.height)
        frame.pack(fill="both", expand=True)

        # Create a new figure for the new window (copy the content from the original figure)
        new_figure = plt.Figure(figsize=figure.get_size_inches())
        new_ax = new_figure.add_subplot(111)

        # Copy plot data (lines, labels, etc.)
        for line in figure.axes[0].lines:
            new_ax.plot(line.get_xdata(), line.get_ydata(), label=line.get_label())

        # Copy axis properties
        new_ax.set_xlabel(figure.axes[0].get_xlabel())
        new_ax.set_ylabel(figure.axes[0].get_ylabel())
        new_ax.set_title(figure.axes[0].get_title())
        new_ax.legend()

        # Create a canvas to render the new figure in the new window
        canvas = FigureCanvasTkAgg(new_figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, new_window)
        toolbar.update()
        toolbar.place(x=self.width//2, y=self.height*0.8, anchor='center')

    def open_files_dropdown(self):
        dropdown_window = ctk.CTkToplevel(self)
        dropdown_window.title("Select Option")
        dropdown_window.geometry("200x150")

        dropdown_window.attributes("-topmost", True)
        frame = ctk.CTkFrame(dropdown_window)
        frame.pack(fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        listbox = Listbox(frame, height=6, yscrollcommand=scrollbar.set)
        options = ['Save Results', 'Setup Analysis', 'Plot Settings']
        for option in options:
            listbox.insert("end", option)
        listbox.pack(fill="both", expand=True)
        scrollbar.configure(command=listbox.yview)

        def on_select(event):
            selected = listbox.get(listbox.curselection())
            if selected == "Setup Analysis":
                self.open_setup_analysis_window()
            elif selected == "Save Results":
                self.save_results()
            elif selected == "Plot Settings":
                self.open_plot_settings_window()

        listbox.bind("<<ListboxSelect>>", on_select)

    def open_setup_analysis_window(self):
        setup_window = ctk.CTkToplevel(self)
        setup_window.title("Setup Analysis")
        setup_window.geometry(str(self.width//8) + "x" + str(self.height//8))
        setup_window.attributes("-topmost", True)

        frame_width = int(self.width * 0.45)
        frame_height = int(self.height * 0.5)

        small_frame = ctk.CTkFrame(setup_window, bg_color="gray", fg_color="gray",
                                   width=frame_width, height=frame_height)
        small_frame.place(x=self.width * 0.25, y=self.height * 0.3, anchor="center")

        # Spacing and positions based on percentage of window size
        x_spacing = self.width * 0.1
        y_start = self.height * 0.05
        label_font = ("Arial", int(self.height * 0.02))
        input_width = int(self.width * 0.2)
        input_height = int(self.height * 0.05)
        radio_button_width = int(self.width * 0.15)

        y = y_start

        # Title
        wavegen_label = ctk.CTkLabel(small_frame, text="Waveform Parameters:", font=("Arial", int(self.height * 0.03)))
        wavegen_label.place(x=x_spacing, y=y, anchor="center")
        y += self.height * 0.07

        # AC Amplitude
        amp_label = ctk.CTkLabel(small_frame, text="AC Amplitude (mT)", font=label_font)
        amp_label.place(x=x_spacing, y=y, anchor="center")
        amp_entry = ctk.CTkEntry(small_frame, width=input_width, height=input_height)
        amp_entry.insert(0, "0.1")
        amp_entry.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        y += self.height * 0.06

        # Frequency
        freq_label = ctk.CTkLabel(small_frame, text="Frequency (Hz)", font=label_font)
        freq_label.place(x=x_spacing, y=y, anchor="center")
        freq_entry = ctk.CTkEntry(small_frame, width=input_width, height=input_height)
        freq_entry.insert(0, "1000")
        freq_entry.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        y += self.height * 0.06

        # Channel #
        channel_label = ctk.CTkLabel(small_frame, text="Channel #", font=label_font)
        channel_label.place(x=x_spacing, y=y, anchor="center")
        channel_option = ctk.CTkOptionMenu(small_frame, values=["1", "2"], width=input_width, height=input_height)
        channel_option.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        y += self.height * 0.06

        # DC offset
        dc_label = ctk.CTkLabel(small_frame, text="DC offset \"z\"", font=label_font)
        dc_label.place(x=x_spacing, y=y, anchor="center")
        dc_entry = ctk.CTkEntry(small_frame, width=input_width, height=input_height)
        dc_entry.insert(0, "0")
        dc_entry.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        y += self.height * 0.06

        # Odd harmonics?
        odd_label = ctk.CTkLabel(small_frame, text="Only Odd Harmonics?", font=label_font)
        odd_label.place(x=x_spacing, y=y, anchor="center")
        yes_radio = ctk.CTkRadioButton(small_frame, text="Yes", fg_color='blue', hover_color="white", font=label_font)
        yes_radio.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        no_radio = ctk.CTkRadioButton(small_frame, text="No", fg_color='blue', hover_color="white", font=label_font,
                                      command=yes_radio.deselect)
        no_radio.place(x=x_spacing + input_width + self.width * 0.1, y=y, anchor="center")
        y += self.height * 0.06

        # Triggering (Yes/No)
        trig_label = ctk.CTkLabel(small_frame, text="Triggering (Yes/No)", font=label_font)
        trig_label.place(x=x_spacing, y=y, anchor="center")
        trig_yes_radio = ctk.CTkRadioButton(small_frame, text="Yes", fg_color='blue', hover_color="white",
                                            font=label_font)
        trig_yes_radio.place(x=x_spacing + input_width + self.width * 0.02, y=y, anchor="center")
        trig_no_radio = ctk.CTkRadioButton(small_frame, text="No", fg_color='blue', hover_color="white",
                                           font=label_font,
                                           command=trig_yes_radio.deselect)
        trig_no_radio.place(x=x_spacing + input_width + self.width * 0.1, y=y, anchor="center")
        y += self.height * 0.06

        def deselect_no():
            no_radio.deselect()

        yes_radio.configure(command=deselect_no)

        def deselect_trig_no():
            trig_no_radio.deselect()

        trig_yes_radio.configure(command=deselect_trig_no)

        def deselect_no():
            no_radio.deselect()

        yes_radio.configure(command=deselect_no)

        # DAQ Card Inputs Section
        daq_frame_width = int(self.width * 0.45)
        daq_frame_height = int(self.height * 0.5)

        daq_frame = ctk.CTkFrame(setup_window, bg_color="gray", fg_color="gray", width=daq_frame_width,
                                 height=daq_frame_height)
        daq_frame.place(x=self.width * 0.75, y=self.height * 0.3, anchor="center")

        daq_x_spacing = self.width * 0.1
        daq_y = y_start  # Start y from the top of the DAQ frame

        # DAQ Frame Title
        daq_title_label = ctk.CTkLabel(daq_frame, text="DAQ Card Input Channels", text_color="black",
                                       font=("Arial", int(self.height * 0.03)))
        daq_title_label.place(x=1.1 * daq_x_spacing, y=daq_y, anchor="center")
        daq_y += self.height * 0.07

        # DAQ Signal Channel
        daq_signal_label = ctk.CTkLabel(daq_frame, text="Signal Channel", font=label_font)
        daq_signal_label.place(x=daq_x_spacing, y=daq_y, anchor="center")
        daq_signal_option = ctk.CTkOptionMenu(daq_frame, values=["Dev3/ai0", "Dev2/ai0", "Dev1/ai0"], width=input_width,
                                              height=input_height)
        daq_signal_option.set(self.daq_signal_channel)
        daq_signal_option.place(x=daq_x_spacing + input_width + self.width * 0.02, y=daq_y, anchor="center")
        daq_y += self.height * 0.06

        # DAQ Current Channel
        daq_current_label = ctk.CTkLabel(daq_frame, text="Current Channel", font=label_font)
        daq_current_label.place(x=daq_x_spacing, y=daq_y, anchor="center")
        daq_current_option = ctk.CTkOptionMenu(daq_frame, values=["Dev3/ai1", "Dev2/ai1", "Dev1/ai1"],
                                               width=input_width, height=input_height)
        daq_current_option.set(self.daq_current_channel)
        daq_current_option.place(x=daq_x_spacing + input_width + self.width * 0.02, y=daq_y, anchor="center")
        daq_y += self.height * 0.06

        # DAQ Trigger Channel
        daq_trigger_label = ctk.CTkLabel(daq_frame, text="Trigger Channel", font=label_font)
        daq_trigger_label.place(x=daq_x_spacing, y=daq_y, anchor="center")
        daq_trigger_option = ctk.CTkOptionMenu(daq_frame, values=["/Dev3/pfi0", "/Dev2/pfi0", "/Dev1/pfi0"],
                                               width=input_width, height=input_height)
        daq_trigger_option.set(self.daq_trigger_channel)
        daq_trigger_option.place(x=daq_x_spacing + input_width + self.width * 0.02, y=daq_y, anchor="center")
        daq_y += self.height * 0.06

        # Sample Rate and Num Periods
        sample_rate_label = ctk.CTkLabel(daq_frame, text="Sample Rate (Hz):", font=label_font)
        sample_rate_label.place(x=daq_x_spacing, y=daq_y, anchor="center")
        sample_rate_entry = ctk.CTkEntry(daq_frame, width=input_width, height=input_height)
        sample_rate_entry.insert(0, str(self.sample_rate))
        sample_rate_entry.place(x=daq_x_spacing + input_width + self.width * 0.02, y=daq_y, anchor="center")
        daq_y += self.height * 0.06

        num_periods_label = ctk.CTkLabel(daq_frame, text="Num Periods:", font=label_font)
        num_periods_label.place(x=daq_x_spacing, y=daq_y, anchor="center")
        num_periods_entry = ctk.CTkEntry(daq_frame, width=input_width, height=input_height)
        num_periods_entry.insert(0, str(self.num_periods))
        num_periods_entry.place(x=daq_x_spacing + input_width + self.width * 0.02, y=daq_y, anchor="center")

        # Save Button to save all values
        def save_values():
            # Save waveform parameters
            self.ac_amplitude = float(amp_entry.get())
            self.frequency = float(freq_entry.get())
            self.channel = int(channel_option.get())
            self.dc_offset = float(dc_entry.get())

            # Save harmonic preference and triggering using your _check_state method
            self.only_odd_harmonics = True if yes_radio._check_state else False
            self.triggering_enabled = True if trig_yes_radio._check_state else False

            # Save DAQ parameters
            self.daq_signal_channel = daq_signal_option.get()
            self.daq_current_channel = daq_current_option.get()
            self.daq_trigger_channel = daq_trigger_option.get()
            self.sample_rate = int(sample_rate_entry.get())
            self.num_periods = int(num_periods_entry.get())

            result_text = (
                f"Saved Values:\n"
                f"AC Amplitude: {self.ac_amplitude}\n"
                f"Frequency: {self.frequency}\n"
                f"Channel #: {self.channel}\n"
                f"DC Offset: {self.dc_offset}\n"
                f"Only Odd Harmonics: {self.only_odd_harmonics}\n"
                f"Triggering Enabled: {self.triggering_enabled}\n"
                f"DAQ Signal Channel: {self.daq_signal_channel}\n"
                f"DAQ Current Channel: {self.daq_current_channel}\n"
                f"DAQ Trigger Channel: {self.daq_trigger_channel}\n"
                f"Sample Rate: {self.sample_rate}\n"
                f"Num Periods: {self.num_periods}"
            )
            self.parameter_textbox.configure(state="normal")
            self.parameter_textbox.delete("0.0", "end")
            self.parameter_textbox.insert("0.0", result_text)
            self.parameter_textbox.configure(state="disabled")

            #setup_window.destroy()

        #textbox to show updated parameters
        box_width = int(self.width * 0.3)
        box_height = int(self.height * 0.25)  # 25% of window height

        self.parameter_textbox = ctk.CTkTextbox(setup_window, width=box_width, height=box_height, state='disabled', font=label_font)
        self.parameter_textbox.place(x=self.width * 0.5, y=self.height * 0.7, anchor="center")

        #Save button
        save_button = ctk.CTkButton(setup_window, text="Save Settings", command=save_values)
        save_button.place(x=self.width * 0.5, y=self.height * 0.85, anchor="center")

    def open_plot_settings_window(self):
        plot_settings_window = ctk.CTkToplevel(self)
        plot_settings_window.title("Plot Settings")
        plot_settings_window.geometry("300x150")
        plot_settings_window.attributes("-topmost", True)

        def toggle_zoom():
            self.zoom_to_11_enabled = zoom_checkbox.get()
        zoom_checkbox = ctk.CTkCheckBox(
            plot_settings_window,
            text="Zoom to 11 Harmonics",
            command=toggle_zoom
        )
        zoom_checkbox.pack(pady=20)

        # Restore previous state (if user reopens settings)
        if self.zoom_to_11_enabled:
            zoom_checkbox.select()

    def open_auto_mode_dropdown(self):
        dropdown_window = ctk.CTkToplevel(self)
        dropdown_window.title("Auto Mode")
        dropdown_window.geometry("200x150")

        dropdown_window.attributes("-topmost", True)
        frame = ctk.CTkFrame(dropdown_window)
        frame.pack(fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        listbox = Listbox(frame, height=6, yscrollcommand=scrollbar.set)
        options = ['Run with static AC', 'Run with static DC']
        for option in options:
            listbox.insert("end", option)
        listbox.pack(fill="both", expand=True)
        scrollbar.configure(command=listbox.yview)

        def on_select(event):
            selected = listbox.get(listbox.curselection())
            if selected == "Run with static AC":
                threading.Thread(target=self.auto_mode_static_ac).start()
            elif selected == "Run with static DC":
                threading.Thread(target=self.auto_mode_static_dc).start()

        listbox.bind("<<ListboxSelect>>", on_select)
    #####################functions to run data#####################
    def calibrate_H_V(self):
        self.H_cal = np.zeros(50)               #array to store the calibrated field
        self.V_cal = np.zeros(50)

        v_amplitude = 0 #start at 0
        sample_rate = 100000  # no need for more than that for the 11th harmonic
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        current_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        frequency = float(self.frequency)

        channel = int(self.channel)

        # Connect to the waveform generator and send current voltage:
        waveform_gen = wave_gen.connect_waveform_generator(gpib_address)

        for l in range(50):

            wave_gen.send_voltage(waveform_gen, v_amplitude, frequency, channel)

            if v_amplitude > 3:
                v_amplitude = 0


            # get the sample's data:
            i_rms = analyze.get_rms_current(current_source, sample_rate, num_periods, daq_trigger)


            # get the magnetization from the detected rms current:
            H_magnitude = 5.0093 * i_rms * np.sqrt(2)

            self.H_cal[l] = H_magnitude
            self.V_cal[l] = v_amplitude

            v_amplitude += 0.05
            time.sleep(0.05)

        wave_gen.turn_off(waveform_gen, channel)
        self.ax1.clear()
        self.ax1.set_title("H_V Calibrated", fontsize=11)
        self.ax1.set_xlabel("V", fontsize=10)
        self.ax1.set_ylabel("H", fontsize=10)

        self.ax1.plot(self.V_cal, self.H_cal)

        self.canvas1.draw()

        self.slope, _ = np.polyfit(self.V_cal, self.H_cal, 1)
        print(self.slope)

    def run_background_subtraction(self):
        # Turn the live_frequency display off if if it's on by switching state to 0:
        self.on_off = 0

        # Retrieve necessary parameters from the GUI
        sample_rate = int(self.sample_rate)
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        daq_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        V_amplitude = (1/self.slope) * float(self.ac_amplitude)

        frequency = float(self.frequency)

        channel = int(self.channel)

        # Get the dc current you want to run through the helmoholtz coils:
        dc_current = float(self.dc_offset)  # Amps

        # Call the background_subtraction function with appropriate arguments
        num_samples, background_magnitude, background_frequency, background_phase, daq_readout, background_complex = analyze.get_background(
            daq_signal, daq_source,daq_trigger, sample_rate, num_periods, gpib_address, V_amplitude, frequency, channel,
            dc_current)

        recon, integral = analyze.reconstruct_and_integrate(num_samples, background_frequency, background_magnitude,
                                                            frequency)

        # Store the values in the self object to later have the option of saving them as .mat files
        self.background_frequency_array_magnitude = background_magnitude
        self.background_frequency_array_frequency = background_frequency
        self.background_frequency_array_phase = background_phase
        self.background_frequency_array_complex = background_complex
        self.frequency_back = background_frequency
        self.phase = background_phase
        self.recon = recon
        self.magnetization = integral
        self.background = daq_readout

        # Update Plots:
        self.ax1.clear()
        self.ax1.set_title("Daq Readout", fontsize=11)
        self.ax1.set_xlabel("Number Of Samples", fontsize=10)
        self.ax1.set_ylabel("Magnitude", fontsize=10)
        # self.ax1.set_facecolor('#505050')

        self.ax1.plot(daq_readout)

        self.canvas1.draw()

        self.ax2.clear()
        self.ax2.set_title("Background Frequency Spectrum (Magnitude)", fontsize=11)
        self.ax2.set_xlabel("Frequency, kHz", fontsize=10)
        self.ax2.set_ylabel("Magnitude", fontsize=10)
        if self.zoom_to_11_enabled:
            self.ax2.set_xlim(left=0, right=11)  # Zoom in to 11 harmonics
            self.ax2.set_xticks(range(1, 12))  # Tick from 1 to 11
        else:
            if sample_rate == 100000:
                self.ax2.set_xticks([1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49])
            elif sample_rate == 1000000:
                self.ax2.set_xticks([25, 75, 125, 175, 225, 275, 325, 375, 425, 475])

        self.ax2.plot(background_frequency / 1000, background_magnitude)

        self.canvas2.draw()

        self.ax3.clear()
        self.ax3.set_title("Reconstructed Waveform", fontsize=11)
        self.ax3.set_xlabel("One Period", fontsize=10)
        self.ax3.set_ylabel("Magnitude", fontsize=10)
        # self.ax3.set_facecolor('#505050')

        self.ax3.plot(recon)

        self.canvas3.draw()

        self.ax4.clear()
        self.ax4.set_title("Magnetization", fontsize=11)
        self.ax4.set_xlabel("One Period", fontsize=10)
        self.ax4.set_ylabel("Magnitude", fontsize=10)
        # self.ax3.set_facecolor('#505050')

        self.ax4.plot(integral)

        self.canvas4.draw()

    def run_with_sample(self):
        # Turn the live_frequency display off if if it's on by switching state to 0:
        self.on_off = 0

        self.run += 1

        # Retrieve necessary parameters from the GUI
        sample_rate = int(self.sample_rate)
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        daq_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        V_amplitude = (1/self.slope) * float(self.ac_amplitude)

        frequency = float(self.frequency)

        channel = int(self.channel)

        # Get the dc current you want to run through the helmoholtz coils:
        dc_current = float(self.dc_offset)  # Amps

        background_complex = self.background_frequency_array_complex

        # get the sample's data:
        (num_samples, sample_magnitude, signal_frequency, signal_with_background, sample_phase, i_rms,
         signal_with_background_complex, sample_complex) = analyze.get_sample_signal(
            daq_signal, daq_source, daq_trigger, sample_rate, num_periods, gpib_address, V_amplitude,
            frequency, channel, dc_current, background_complex, self.only_odd_harmonics)

        sample_phase = np.abs(sample_magnitude)
        self.signal_with_background = signal_with_background
        self.signal_frequency_array_amplitude = signal_with_background_complex #this is the sample with its background (raw fourrier transform)
        self.sample_frequency_array_magnitude = sample_magnitude
        self.sample_frequency_array_amplitude = sample_complex
        self.sample_frequency_array_frequency = signal_frequency #frequency array of the frequencies (considers sampling rate)

        # reconstruct the waveform over one period and get the magnetization (integral)
        recon, integral = analyze.reconstruct_and_integrate(num_samples, signal_frequency, sample_magnitude,
                                                            frequency)

        self.magnetization = integral  # to save to .mat file

        # get the magnetic field from the detected rms current:
        H_magnitude = 5.0093 * i_rms * np.sqrt(2)
        H = analyze.general_reconstruction(H_magnitude, frequency)

        self.H_field = H  # to be saved to .mat file

        # Update Plots:
        self.ax1.clear()
        self.ax1.set_title("Daq Readout", fontsize=11)
        self.ax1.set_xlabel("Number Of Samples", fontsize=10)
        self.ax1.set_ylabel("Magnitude", fontsize=10)
        self.fig1.tight_layout()
        # self.ax1.set_facecolor('#505050')

        self.ax1.plot(signal_with_background)

        self.canvas1.draw()

        self.ax2.clear()
        self.ax2.set_title("Sample's Frequency Spectrum (Backsubtracted)", fontsize=11)
        self.ax2.set_xlabel("Frequency, kHz", fontsize=10)
        self.ax2.set_ylabel("Magnitude", fontsize=10)
        if self.zoom_to_11_enabled:
            self.ax2.set_xlim(left=0, right=11)  # Zoom in to 11 harmonics
            self.ax2.set_xticks(range(1, 12))  # Tick from 1 to 11
        else:
            if sample_rate == 100000:
                self.ax2.set_xticks([1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49])
            elif sample_rate == 1000000:
                self.ax2.set_xticks([25, 75, 125, 175, 225, 275, 325, 375, 425, 475])

        self.ax2.plot(signal_frequency / 1000, sample_magnitude)

        self.canvas2.draw()

        self.ax3.clear()
        self.ax3.set_title("Reconstructed Waveform", fontsize=11)
        self.ax3.set_xlabel("One Period", fontsize=10)
        self.ax3.set_ylabel("Magnitude", fontsize=10)
        # self.ax3.set_facecolor('#505050')

        self.ax3.plot(recon)

        self.canvas3.draw()

        self.ax4.clear()
        self.ax4.set_title("Magnetization", fontsize=11)
        self.ax4.set_xlabel("One Period", fontsize=10)
        self.ax4.set_ylabel("Magnitude", fontsize=10)
        # self.ax3.set_facecolor('#505050')

        self.ax4.plot(integral)

        self.canvas4.draw()

        self.ax5.clear()
        self.ax5.set_title("dM/dH Curve", fontsize=11)
        self.ax5.set_xlabel("H", fontsize=10)
        self.ax5.set_ylabel("dM/dH", fontsize=10)
        # Need half of a period for MH and dM/dH:
        #integral = integral[:len(integral) // 2]
        #H = H[:len(H) // 2]
        dMdH = analyze.dMdH(integral, H)

        self.ax5.plot(H, dMdH)

        self.canvas5.draw()

        self.ax6.set_title("MH Curve comparison", fontsize=11)
        self.ax6.set_xlabel("H", fontsize=10)
        self.ax6.set_ylabel("M", fontsize=10)
        self.ax6.plot(H, integral, label='Run#' + str(self.run))

        self.ax6.legend(loc='upper left')
        self.canvas6.draw()

    def run_live_frequency_array(self):
        self.on_off = 1  # set the state to on
        # Retrieve necessary parameters from the GUI
        # Retrieve necessary parameters from the GUI
        sample_rate = int(self.sample_rate)
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        daq_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        V_amplitude = (1/self.slope) * float(self.ac_amplitude)

        frequency = float(self.frequency)

        channel = int(self.channel)

        num_pts_per_period = sample_rate / frequency  # Fs/F_drive
        num_samples = int((num_periods * num_pts_per_period) + 1)

        if V_amplitude > 3:
            amplitude = 0

        waveform_generator = wave_gen.connect_waveform_generator(gpib_address=gpib_address)
        self.waveform_generator = waveform_generator  # will be used in the stop function
        wave_gen.send_voltage(waveform_generator, V_amplitude, frequency, channel)

        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(daq_signal)
            task.timing.cfg_samp_clk_timing(sample_rate, samps_per_chan=num_samples)

            while self.on_off == 1:
                voltage_raw = task.read(number_of_samples_per_channel=num_samples)  # read pure daq readout

                # Get the fourier data
                fourier_magnitude, fourier_frequency, phase, fourier_amplitude = analyze.fourier(voltage_raw, sample_rate, num_samples)
                fourier_magnitude = np.abs(fourier_magnitude)

                self.update_plot(fourier_frequency, fourier_magnitude, sample_rate)
                self.canvas1.draw()
                self.update()

    def update_plot(self, frequency, magnitude, f_s):
        # Update the plot
        self.ax1.clear()
        self.ax1.set_title("Frequency Spectrum", fontsize=11)
        self.ax1.set_xlabel("Frequency, kHz", fontsize=10)
        self.ax1.set_ylabel("Magnitude", fontsize=10)
        if self.zoom_to_11_enabled:
            self.ax1.set_xlim(left=0, right=11)  # Zoom in to 11 harmonics
            self.ax1.set_xticks(range(1, 12))  # Tick from 1 to 11
        else:
            if f_s == 100000:
                self.ax1.set_xticks([1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49])
            elif f_s == 1000000:
                self.ax1.set_xticks([25, 75, 125, 175, 225, 275, 325, 375, 425, 475])
        self.ax1.plot(frequency / 1000, magnitude)
        self.fig1.tight_layout()

    def stop_acquisition(self):
        channel = int(self.channel)
        self.waveform_generator.write(f"OUTPUT{channel} OFF")
        self.on_off = 0  # set the state to off
        self.waveform_generator.close()

    def auto_mode_static_dc(self): #To record harmonics and compare them
        self.mode = "Static DC with varying ac."
        num_steps = 50 #arrays will be of size 50
        harmonic_orders = list(range(1, 12))  #2nd to 11th
        harmonic_indices = [100, 200, 300,400, 500, 600, 700, 800, 900, 1000, 1100]

        self.max_H_field = np.zeros(num_steps)
        self.harmonics = {order: np.zeros(num_steps) for order in harmonic_orders}
        v_amplitude = 0 #start at 0...

        sample_rate = 100000  # no need for more than that for the 11th harmonic
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        daq_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        frequency = float(self.frequency)

        channel = int(self.channel)

        # Get the dc current you want to run through the helmoholtz coils:
        dc_current = float(self.dc_offset)  # Amps

        #check which supply remains static:
        power_supply = wave_gen.DC_offset(dc_current)
        for l in range(num_steps):
            if v_amplitude > 4.5:
                v_amplitude = 0

            background_complex = self.background_frequency_array_complex

            # get the sample's data:
            num_samples, sample_magnitude, signal_frequency, signal_with_background, sample_phase, i_rms,\
                signal_with_background_complex, sample_complex = analyze.get_sample_signal(
                daq_signal, daq_source, daq_trigger, sample_rate, num_periods, gpib_address, v_amplitude,
                frequency, channel, dc_current=None, background_complex=background_complex, isClean=False)

            self.frequency_array_magnitude = sample_magnitude

            # get the magnetization from the detected rms current:
            H_magnitude = 5.0093 * i_rms * np.sqrt(2)
            self.max_H_field[l] = H_magnitude

            # Store all harmonics
            for i, order in enumerate(harmonic_orders):
                self.harmonics[order][l] = sample_magnitude[harmonic_indices[i]]

            v_amplitude += 0.05
            time.sleep(0.01)
        if power_supply:
            wave_gen.turn_off_dc_output(power_supply)
            power_supply.close()
        self.plot_harmonics(field=self.max_H_field,dc_static=True)

    def auto_mode_static_ac(self):
        self.mode = "Static ac with varying DC."
        num_steps = 200 # arrays will be of size 200
        harmonic_orders = list(range(1, 12))  # 2nd to 11th
        harmonic_indices = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100]

        self.i_dc = np.zeros(num_steps)
        self.harmonics = {order: np.zeros(num_steps) for order in harmonic_orders}
        v_amplitude = 0  # start at 0...

        sample_rate = 100000  # no need for more than that for the 11th harmonic
        num_periods = int(self.num_periods)

        daq_signal = self.daq_signal_channel
        daq_source = self.daq_current_channel
        daq_trigger = self.daq_trigger_channel
        gpib_address = 10

        frequency = float(self.frequency)

        channel = int(self.channel)
        v_amplitude = (1 / self.slope) * float(self.ac_amplitude)
        if v_amplitude > 4.5:
            v_amplitude = 0

        # Connect the waveform generator and send a signal for background measurement
        waveform_generator = wave_gen.connect_waveform_generator(gpib_address)
        wave_gen.send_voltage(waveform_generator, v_amplitude, frequency, channel)

        # dc current starting at 0:
        dc_current = 0
        power_supply = wave_gen.DC_offset(dc_current)
        for l in range(num_steps):
            wave_gen.send_dc_voltage(power_supply, voltage=12, current=dc_current)
            background_complex = self.background_frequency_array_complex

            # get the sample's data:
            (num_samples, sample_magnitude, signal_frequency, signal_with_background, sample_phase, i_rms,
             signal_with_background_complex, sample_complex) = analyze.get_sample_signal(
                daq_signal, daq_source, daq_trigger, sample_rate, num_periods, gpib_address, amplitude=None,
                frequency=frequency, channel=channel, dc_current=None, background_complex=background_complex,
                isClean=False)

            self.frequency_array_magnitude = sample_magnitude

            self.i_dc[l] = dc_current

            # Store all harmonics
            for i, order in enumerate(harmonic_orders):
                self.harmonics[order][l] = sample_magnitude[harmonic_indices[i]]

            dc_current += 0.05
            time.sleep(0.01)
        wave_gen.turn_off_dc_output(power_supply)
        power_supply.close()
        wave_gen.turn_off(waveform_generator, channel)
        self.plot_harmonics(field = self.i_dc ,dc_static=False)

    def plot_harmonics(self, field, dc_static=False):
        self.ax1.clear()
        self.ax2.clear()
        if dc_static:
            field_txt = "μo H (mT)"
        else:
            field_txt = "I_DC (A)"

        self.ax1.set_title("Odd Harmonics vs Field", fontsize=11)
        self.ax1.set_xlabel(field_txt, fontsize=10)
        self.ax1.set_ylabel("Harmonics", fontsize=10)

        self.ax2.set_title("Even Harmonics vs Field", fontsize=11)
        self.ax2.set_xlabel(field_txt, fontsize=10)
        self.ax2.set_ylabel("Harmonics", fontsize=10)

        for order in [3, 5, 7, 9, 11]: #odd harmonics
            self.ax1.plot(field, self.harmonics[order],
                          label=f'{order}rd Harmonic' if order == 3 else f'{order}th Harmonic')

        for order in [2, 4, 6, 8, 10]: #Even Harmonics
            self.ax2.plot(field, self.harmonics[order],
                          label=f'{order}nd Harmonic' if order == 2 else f'{order}th Harmonic')
        self.ax1.legend()
        self.ax2.legend()
        self.canvas1.draw()
        self.canvas2.draw()

    def run_stepped(self):
        return

    ####################### function to save results #########################
    def save_results(self):
        filename = filedialog.asksaveasfilename(defaultextension=".mat",
                                                filetypes=[("MATLAB files", "*.mat"), ("All files", "*.*")])
        if filename:

            data = {} #empty dictionary to hold the data

            instructions = (
                'Here is the naming convention used for the variables:'
                'background = background\n'
                'signal = sample with background\n'
                'sample = signal - background\n'
                'xxxx_frequency_array_amplitude = complex coefficients an and bn\n'
                'xxxx_frequency_array_magnitude = magnitude Cn = sqrt(an^2 + bn^2)\n'
                'xxxx_frequency_array_phase = phase θn = arctan(bn/an)\n'
                'xxxx_frequency_array_frequency = frequency array for specific "xxxx" component'
            )
            data['instructions'] = instructions

            parameters = {
                'mode': getattr(self, 'mode', None),
                'ac_amplitude': getattr(self, 'ac_amplitude', None),
                'frequency': getattr(self, 'frequency', None),
                'channel': getattr(self, 'channel', None),
                'dc_offset': getattr(self, 'dc_offset', None),
                'only_odd_harmonics': getattr(self, 'only_odd_harmonics', None),
                'triggering_enabled': getattr(self, 'triggering_enabled', None),
                'daq_signal_channel': getattr(self, 'daq_signal_channel', None),
                'daq_current_channel': getattr(self, 'daq_current_channel', None),
                'daq_trigger_channel': getattr(self, 'daq_trigger_channel', None),
                'sample_rate': getattr(self, 'sample_rate', None),
                'num_periods': getattr(self, 'num_periods', None)
            }
            clean_parameters = {k: v for k, v in parameters.items() if v is not None}
            data['parameters'] = clean_parameters

            # Check and add each attribute if it exists
            if hasattr(self, 'magnetization') and self.magnetization is not None:
                data['magnetization'] = self.magnetization
            if hasattr(self, 'H_field') and self.H_field is not None:
                data['magnetic_field'] = self.H_field
            if hasattr(self, 'sample_frequency_array_frequency') and self.sample_frequency_array_frequency is not None:
                data['sample_frequency_array_frequency'] = self.sample_frequency_array_frequency
            if hasattr(self, 'background_frequency_array_magnitude') and self.background_frequency_array_magnitude is not None:
                data['background_frequency_array_magnitude'] = self.background_frequency_array_magnitude
            if hasattr(self, 'background_frequency_array_phase') and self.background_frequency_array_phase is not None:
                data['background_frequency_array_phase'] = self.background_frequency_array_phase
            if hasattr(self, 'background_frequency_array_complex') and self.background_frequency_array_complex is not None:
                data['background_frequency_array_amplitude'] = self.background_frequency_array_complex
            if hasattr(self, 'signal_frequency_array_amplitude') and self.signal_frequency_array_amplitude is not None:
                data['signal_frequency_array_amplitude'] = self.signal_frequency_array_amplitude
            if hasattr(self, 'sample_frequency_array_magnitude') and self.sample_frequency_array_magnitude is not None:
                data['sample_frequency_array_magnitude'] = self.sample_frequency_array_magnitude
            if hasattr(self, 'sample_frequency_array_amplitude') and self.sample_frequency_array_amplitude is not None:
                data['sample_frequency_array_amplitude'] = self.sample_frequency_array_amplitude
            if hasattr(self, 'max_H_field') and self.max_H_field is not None:
                data['H_field_harmonic'] = self.max_H_field
            if hasattr(self, 'H_field_total') and self.H_field_total:
                data['H_field_stepped'] = self.H_field_total
            if hasattr(self, 'background') and self.background is not None:
                data['background'] = self.background
            if hasattr(self, 'signal_with_background') and self.signal_with_background is not None:
                data['signal_with_background'] = self.signal_with_background
            if hasattr(self, 'i_dc') and self.i_dc is not None:
                data['i_dc'] = self.i_dc

            if hasattr(self, 'harmonics') and self.harmonics is not None:
                odd_harmonics = {order: self.harmonics[order] for order in [1, 3, 5, 7, 9, 11] if
                                 self.harmonics[order] is not None}
                even_harmonics = {order: self.harmonics[order] for order in [2, 4, 6, 8, 10] if
                                  self.harmonics[order] is not None}

                if odd_harmonics:
                    for i in [1, 3, 5, 7, 9, 11]:
                        i_str = "harmonic_"+str(i)
                        data[i_str] = odd_harmonics[i]
                if even_harmonics:
                    for i in [2, 4, 6, 8, 10]:
                        i_str = "harmonic_" + str(i)
                        data[i_str] = even_harmonics[i]

            # Save the dictionary to a MATLAB file
            savemat(filename, data)

if __name__ == "__main__":
    app = App()
    app.mainloop()
