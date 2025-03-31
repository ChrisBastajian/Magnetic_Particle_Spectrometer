import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import receive_and_analyze as analyze
from tkinter import filedialog, Toplevel, StringVar
from scipy.io import savemat
from matplotlib.figure import Figure

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


if __name__ == "__main__":
    app = App()
    # Used to run the application
    app.mainloop()