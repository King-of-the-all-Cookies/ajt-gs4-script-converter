import os
import tkinter as tk
from tkinter import filedialog, messagebox

def run_script():
    mode = mode_var.get()
    file_path = file_entry.get()

    if not mode or not file_path:
        messagebox.showerror("Error", "Please select a mode and a file.")
        return

    commands = []
    commands.append("@echo off")
    commands.append("color 2")
    commands.append("cls")

    if mode == 'Decode':
        commands.append('echo Decoding...')
        commands.append(f'python main1.py d {file_path}')
        commands.append(f'python main2.py decode {file_path}.bin')
        
    elif mode == 'Encode':
        commands.append('echo Encoding...')
        f1 = file_path[:-3] + "bin"
        commands.append(f'python main2.py encode {file_path}')
        commands.append(f'python main1.py e {f1}')
        
    else:
        messagebox.showerror("Error", 'Invalid mode selected.')
        return

    commands.append('color f')
    commands.append('cls')
    commands.append('echo Done!')
    commands.append('pause')
    commands.append('cls')

    bat_file_path = 'cache.bat'
    
    with open(bat_file_path, 'w') as bat_file:
        for line in commands:
            bat_file.write(line + '\n')

    os.system(bat_file_path)
    os.remove(bat_file_path)

    if mode == 'Decode':
        os.remove(f"{file_path}.bin")
    
    elif mode == 'Encode':
        os.remove(f1)

    messagebox.showinfo('Done', "Script executed successfully!")

def select_file():
    file_path = filedialog.askopenfilename()
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)


root = tk.Tk()
root.title("AJAAT GS4 Script Converter")


mode_var = tk.StringVar(value='Decode')
tk.Label(root, text="Select Mode:").pack(pady=10)
tk.Radiobutton(root, text="Decode", variable=mode_var, value='Decode').pack(anchor=tk.W)
tk.Radiobutton(root, text="Encode", variable=mode_var, value='Encode').pack(anchor=tk.W)


tk.Label(root, text="Select File:").pack(pady=10)
file_entry = tk.Entry(root, width=50)
file_entry.pack(pady=5)
tk.Button(root, text="Browse...", command=select_file).pack(pady=5)


tk.Button(root, text="Run Script", command=run_script).pack(pady=20)


root.mainloop()
