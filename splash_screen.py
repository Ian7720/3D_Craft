import os
import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk  # Import PIL for image resizing
from PyQt5.QtWidgets import QApplication
from Assignment1 import MainWindow

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()

        # Resize the image with PIL
        original_image = Image.open(r"D:/UMS/SEM7/SDV/Assignment1/icon/new.png")
        resized_image = original_image.resize((500, 300), Image.LANCZOS)  # Adjust size as needed
        self.image = ImageTk.PhotoImage(resized_image)

        self.height = 430
        self.width = 530
        x = (self.root.winfo_screenwidth() // 2) - (self.width // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(self.width, self.height, x, y))
        self.root.overrideredirect(True)

        self.root.config(background='#FFEDED')

        # Title Header
        self.title_header = tk.Label(self.root, text="Craft3D", 
                                     font=("Trebuchent Ms", 20, "bold"), fg="#FF6F6F", bg="#FFEDED")
        self.title_header.pack(pady=(15, 0))  # Add padding to position it at the top

        self.welcome_label = tk.Label(self.root, text="< 3d object editor >", bg="#FFEDED", font=("Trebuchent Ms", 15, "bold"), fg="#FFBFBF")
        self.welcome_label.place(x=170, y=50)  # Adjusted position to accommodate the title header

        # Center the resized image
        image_width = self.image.width()
        image_height = self.image.height()
        image_x = (self.width - image_width) // 2
        image_y = (self.height - image_height) // 2 + 30  # Offset image lower to make room for title

        self.bg_label = tk.Label(self.root, image=self.image, bg="#FFEDED")
        self.bg_label.place(x=image_x, y=image_y-20)

        self.citation_label = tk.Label(self.root, text="Cited to: <a href=https://lovepik.com/images/png-computer.html>Computer Png vectors by Lovepik.com</a>",
                                       bg="#FFEDED", font=("Trebuchent Ms", 5, "bold"), fg="#FFBFBF")
        self.citation_label.place(x=85, y=310)

        self.progress_label = tk.Label(self.root, text="Loading...", font=("Trebuchent Ms", 15, "bold"), fg="#FFFFFF", bg="#FFEDED")
        self.progress_label.place(x=190, y=330)

        self.progress = ttk.Style()
        self.progress.theme_use('clam')
        self.progress.configure("red.Horizontal.TProgressbar", background="#108CFF")

        self.progress = Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate', style="red.Horizontal.TProgressbar")
        self.progress.place(x=60, y=370)

        self.i = 0

    def top(self):
        self.root.withdraw()
        self.app = QApplication([])  # Create a QApplication instance
        self.main_window = MainWindow()  # Create an instance of MainWindow
        self.main_window.show()  # Show the MainWindow
        self.app.exec_()  # Execute the QApplication
        self.root.destroy()

    def load(self):
        if self.i <= 10:
            txt = "Loading... " + (str(10 * self.i) + "%")
            self.progress_label.config(text=txt)
            self.progress_label.after(600, self.load)
            self.progress['value'] = 10 * self.i
            self.i += 1
        else:
            self.top()

    def show(self):
        self.load()
        self.root.resizable(False, False)
        self.root.mainloop()

splash = SplashScreen()
splash.show()
