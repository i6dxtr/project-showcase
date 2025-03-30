import tkinter as tk
from tkinter import messagebox, font

def on_key_press(event):
    # Check if the pressed key is 'c' (or uppercase 'C')
    if event.char.lower() == 'c':
        messagebox.showinfo("Input Detected", "You pressed 'c'!")

def exit_fullscreen(event):
    # Allow exiting fullscreen by pressing the Escape key
    root.attributes('-fullscreen', False)

# Create the main window and set it to fullscreen
root = tk.Tk()
root.attributes('-fullscreen', True)
root.configure(bg="#1e1e1e")  # Dark background color

# Define custom fonts for the title and instructions
title_font = font.Font(family="Helvetica", size=48, weight="bold")
instruction_font = font.Font(family="Helvetica", size=24)

# Create and pack the title label
title_label = tk.Label(root, 
                       text="Welcome to Future Vision", 
                       font=title_font, 
                       fg="white", 
                       bg="#1e1e1e")
title_label.pack(pady=100)

# Create and pack the instruction label
instruction_label = tk.Label(root, 
                             text="Please pick up an item and show it to the camera", 
                             font=instruction_font, 
                             fg="white", 
                             bg="#1e1e1e")
instruction_label.pack(pady=20)

# Bind key press events for 'c' and for exiting fullscreen (Escape key)
root.bind("<Key>", on_key_press)
root.bind("<Escape>", exit_fullscreen)

# Run the GUI event loop
root.mainloop()
