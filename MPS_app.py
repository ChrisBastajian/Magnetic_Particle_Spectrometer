import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import receive_and_analyze as analyze
from tkinter import filedialog, Toplevel, StringVar
from scipy.io import savemat
from matplotlib.figure import Figure
from tkinter import filedialog, Toplevel, StringVar, Scrollbar, Listbox

#For the live frequency array:
import wave_gen
import nidaqmx
import time

ctk.set_appearance_mode("light_gray")

#Color Theme:
ctk.set_default_color_theme("dark-blue")

#create App class:
class App(ctk.CTk):
    # Layout of the GUI will be written in the init itself
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sets the title of our window to "MPS App"
        self.title("MPS App")
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.geometry(str(width) + "x" + str(height))
        self.configure(fg="#333333")
########################################################################################################################
        #Setting up elements in places:
        #Title Bar:
        self.title_bar = ctk.CTkFrame(self, height=height//36, width=width, corner_radius=0, fg_color='gray') #height about 30 px
        self.title_bar.place(x= width//2, y=height//72, anchor="center")

        self.title_bar.file = ctk.CTkButton(self.title_bar, text="File", command=self.open_dropdown)
        self.title_bar.file.place(x= 0.03*width, y= height//72, anchor='center')
        self.title_bar.file.configure(width=0.06*width)


    def open_dropdown(self):
        # Create a new Toplevel window for the dropdown
        dropdown_window = ctk.CTkToplevel(self)
        dropdown_window.title("Select Option")
        dropdown_window.geometry("200x300")

        # Create a frame for scrollable content
        frame = ctk.CTkFrame(dropdown_window)
        frame.pack(fill="both", expand=True)

        # Create a scrollbar
        scrollbar = ctk.CTkScrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        # Create a listbox with options (using standard Tkinter Listbox)
        listbox = Listbox(frame, height=6, yscrollcommand=scrollbar.set)
        options = ['File', 'Save Results', 'Plot']
        for option in options:
            listbox.insert("end", option)
        listbox.pack(fill="both", expand=True)

        # Configure the scrollbar
        scrollbar.configure(command=listbox.yview)

if __name__ == "__main__":
    app = App()
    # Used to run the application
    app.mainloop()