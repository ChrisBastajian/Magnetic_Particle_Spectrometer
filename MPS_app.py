import customtkinter as ctk
from tkinter import Listbox
import matplotlib.pyplot as plt
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("light_gray")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("MPS App")
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()

        self.geometry(f"{self.width}x{self.height}")
        self.configure(fg="#333333")

        # Initialize parameters with default values
        self.ac_amplitude = 0.1  # Default AC Amplitude (V)
        self.frequency = 1000  # Default Frequency (Hz)
        self.channel = "1"
        self.dc_offset = 0
        self.only_odd_harmonics = False
        self.triggering_enabled = False

        # DAQ Card Parameters
        self.daq_signal_channel = "Dev3/ai0"
        self.daq_current_channel = "Dev3/ai1"
        self.daq_trigger_channel = "Dev3/pfi0"
        self.sample_rate = 1000000  #Hz
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
        num_buttons = 7
        total_spacing_width = self.width * 0.8  # spread buttons across 80% of window
        start_x = (self.width - total_spacing_width) / 2
        btn_spacing = total_spacing_width / (num_buttons - 1)

        # Place each button with consistent spacing
        self.title_bar.file = ctk.CTkButton(self.title_bar, text="File",
                                            font=('Arial', int(self.height * 0.018)),
                                            command=self.open_dropdown,
                                            width=btn_width, height=btn_height)
        self.title_bar.file.place(x=start_x + btn_spacing * 0, y=btn_y, anchor='center')

        self.title_bar.background_sub = ctk.CTkButton(self.title_bar, text="Run Background Scan",
                                                      font=('Arial', int(self.height * 0.018)),
                                                      command=self.run_background_subtraction,
                                                      width=btn_width, height=btn_height)
        self.title_bar.background_sub.place(x=start_x + btn_spacing * 1, y=btn_y, anchor='center')

        self.title_bar.get_results = ctk.CTkButton(self.title_bar, text="Run With Sample",
                                                   font=('Arial', int(self.height * 0.018)),
                                                   command=self.run_with_sample,
                                                   width=btn_width, height=btn_height)
        self.title_bar.get_results.place(x=start_x + btn_spacing * 2, y=btn_y, anchor='center')

        self.title_bar.live_frequency = ctk.CTkButton(self.title_bar, text="Run Live Frequency Array",
                                                      font=('Arial', int(self.height * 0.018)),
                                                      command=self.run_live_frequency_array,
                                                      width=btn_width, height=btn_height)
        self.title_bar.live_frequency.place(x=start_x + btn_spacing * 3, y=btn_y, anchor='center')

        self.title_bar.stop = ctk.CTkButton(self.title_bar, text="Stop Live Acquisition", hover_color="red",
                                            font=('Arial', int(self.height * 0.018)),
                                            command=self.stop_acquisition,
                                            width=btn_width, height=btn_height)
        self.title_bar.stop.place(x=start_x + btn_spacing * 4, y=btn_y, anchor='center')

        self.title_bar.auto_mode = ctk.CTkButton(self.title_bar, text='Automated Mode',
                                                 font=('Arial', int(self.height * 0.018)),
                                                 command=self.auto_mode,
                                                 width=btn_width, height=btn_height)
        self.title_bar.auto_mode.place(x=start_x + btn_spacing * 5, y=btn_y, anchor='center')

        self.title_bar.get_stepped_data = ctk.CTkButton(self.title_bar, text="Run Stepped",
                                                        font=('Arial', int(self.height * 0.018)),
                                                        command=self.run_stepped,
                                                        width=btn_width, height=btn_height)
        self.title_bar.get_stepped_data.place(x=start_x + btn_spacing * 6, y=btn_y, anchor='center')

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

        y_canvas = [int(self.height *0.3), int(self.height * 0.7)]
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

        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

        # For each canvas
        self.toolbar1 = NavigationToolbar2Tk(self.canvas1, self)
        self.toolbar1.update()
        self.toolbar1.place(x=x_canvas[0], y=y_canvas[0] + int(self.height * 0.1), anchor='center')

        self.toolbar2 = NavigationToolbar2Tk(self.canvas2, self)
        self.toolbar2.update()
        self.toolbar2.place(x=x_canvas[1], y=y_canvas[0] + int(self.height * 0.1), anchor='center')

        self.toolbar3 = NavigationToolbar2Tk(self.canvas3, self)
        self.toolbar3.update()
        self.toolbar3.place(x=x_canvas[2], y=y_canvas[0] + int(self.height * 0.1), anchor='center')

        self.toolbar4 = NavigationToolbar2Tk(self.canvas4, self)
        self.toolbar4.update()
        self.toolbar4.place(x=x_canvas[0], y=y_canvas[1] + int(self.height * 0.1), anchor='center')

        self.toolbar5 = NavigationToolbar2Tk(self.canvas5, self)
        self.toolbar5.update()
        self.toolbar5.place(x=x_canvas[1], y=y_canvas[1] + int(self.height * 0.1), anchor='center')

        self.toolbar6 = NavigationToolbar2Tk(self.canvas6, self)
        self.toolbar6.update()
        self.toolbar6.place(x=x_canvas[2], y=y_canvas[1] + int(self.height * 0.1), anchor='center')


    def open_dropdown(self):
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

        listbox.bind("<<ListboxSelect>>", on_select)

    def open_setup_analysis_window(self):
        setup_window = ctk.CTkToplevel(self)
        setup_window.title("Setup Analysis")
        setup_window.geometry(str(self.width) + "x" + str(self.height))
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
        amp_label = ctk.CTkLabel(small_frame, text="AC Amplitude (V)", font=label_font)
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
        daq_trigger_option = ctk.CTkOptionMenu(daq_frame, values=["Dev3/pfi0", "Dev2/pfi0", "Dev1/pfi0"],
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

            print("Saved Values:")
            print(f"AC Amplitude: {self.ac_amplitude}")
            print(f"Frequency: {self.frequency}")
            print(f"Channel #: {self.channel}")
            print(f"DC Offset: {self.dc_offset}")
            print(f"Only Odd Harmonics: {self.only_odd_harmonics}")
            print(f"Triggering Enabled: {self.triggering_enabled}")
            print(f"DAQ Signal Channel: {self.daq_signal_channel}")
            print(f"DAQ Current Channel: {self.daq_current_channel}")
            print(f"DAQ Trigger Channel: {self.daq_trigger_channel}")
            print(f"Sample Rate: {self.sample_rate}")
            print(f"Num Periods: {self.num_periods}")

            setup_window.destroy()

        save_button = ctk.CTkButton(setup_window, text="Save Settings", command=save_values)
        save_button.place(x=self.width * 0.5, y=self.height * 0.9, anchor="center")

    #####################functions to run data#####################
    def run_background_subtraction(self):
        return

    def run_with_sample(self):
        return

    def run_live_frequency_array(self):
        return

    def stop_acquisition(self):
        return

    def auto_mode(self):
        return

    def run_stepped(self):
        return

if __name__ == "__main__":
    app = App()
    app.mainloop()
