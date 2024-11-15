import tkinter as tk
from tkinter import filedialog
from dearpygui import dearpygui as dpg
import os
from fpdf import FPDF
import re

def remove_tags_and_create_pdf(text, input_file_path):
    try:

        text = text.replace(r'\linebreak|', '~linebreak~')
        text = text.replace(r'\nextdialogue|', '~nextdialogue~')
        

        cleaned_text = re.sub(r'\\[^|]+\|[^|]*\|', '', text)
        dialogues = cleaned_text.split(r'~nextdialogue~')

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)


        pdf.cell(30, 10, txt="Page", border=1, align='C')
        pdf.cell(160, 10, txt="Dialogue", border=1, ln=True, align='L')

        page_number = 1
        for dialogue in dialogues:
            # Убираем лишние пробелы
            dialogue = ' '.join(dialogue.split())

            if dialogue.strip():
                # Обрабатываем перенос строк в реплике
                dialogue = dialogue.replace(r'~linebreak~', '\n')

                pdf.cell(30, 10, txt=str(page_number), border=1, align='C')
                pdf.multi_cell(160, 10, txt=dialogue.strip(), border=1, align='L')
                page_number += 1
                pdf.ln()

        pdf_output_path = os.path.splitext(input_file_path)[0] + ".pdf"
        pdf.output(pdf_output_path)
        show_popup("Success", f"PDF saved as {pdf_output_path}")
    except Exception as e:
        show_popup("Error", f"Failed to create PDF: {str(e)}")


def show_popup(title, message):
    with dpg.window(label=title, modal=True, no_title_bar=False) as popup_id:
        dpg.add_text(message)
        dpg.add_button(label="Close", callback=lambda: dpg.delete_item(popup_id))

def on_txt_file_upload(sender, app_data):
    file_path = app_data['file_path']
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    remove_tags_and_create_pdf(text, file_path)

def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    return file_path

def update_file_path(sender, app_data):
    file_path = open_file_dialog()
    if file_path:
        dpg.set_value("manual_file_path", file_path)

def show_txt_to_pdf_window():
    with dpg.window(label="TXT-to-PDF", width=800, height=600, pos=(50, 100)):
        dpg.add_text("Convert TXT to PDF:")
        dpg.add_text("Source TXT File:")
        dpg.add_input_text(label="File Path", tag="manual_file_path", width=350)
        dpg.add_button(label="Browse...", callback=update_file_path)
        dpg.add_button(label="Convert", callback=manual_file_conversion)

def manual_file_conversion(sender, app_data):
    input_file_path = dpg.get_value("manual_file_path")
    if os.path.exists(input_file_path) and input_file_path.endswith(".txt"):
        with open(input_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        remove_tags_and_create_pdf(text, input_file_path)
    else:
        show_popup("Error", "Invalid file path, skipping PDF conversion.")

def select_file_tkinter():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*"), ("AJT GS4 english script files", "*.user.2.en"), ("AJT GS4 japanese script files", "*.user.2.jp")])
    return file_path

def select_file_callback(sender, app_data, user_data):
    file_path = select_file_tkinter()
    if file_path:
        dpg.set_value("file_path", file_path)

def run_script(sender, app_data, user_data):
    mode = dpg.get_value("mode")
    file_path = dpg.get_value("file_path")

    if not mode or not file_path:
        show_popup("Error", "Please select a mode and a file.")
        return

    commands = [
        "@echo off",
        "color 2",
        "cls"
    ]

    if mode == 'Decode':
        commands.extend([
            'echo Decoding...',
            f'python main1.py d "{file_path}"',
            f'python main2.py decode "{file_path}.bin"'
        ])
    elif mode == 'Encode':
        f1 = file_path[:-3] + "bin"
        commands.extend([
            'echo Encoding...',
            f'python main2.py encode "{file_path}"',
            f'python main1.py e "{f1}"'
        ])
    else:
        show_popup("Error", "Invalid mode selected.")
        return

    commands.extend([
        'color f',
        'cls',
        'echo Done!',
        'ping -n 3 localhost>nul',
        'cls'
    ])

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

    show_popup("Success", "Script executed successfully!")

def file_selected_callback(sender, app_data):
    selected_file = app_data["file_path_name"]
    dpg.set_value("file_path", selected_file)
    dpg.hide_item("file_dialog_decode")
    dpg.hide_item("file_dialog_encode")

# DearPyGui Interface Setup
dpg.create_context()
dpg.create_viewport(title="GS4CONVERTER", width=1280, height=1024)

with dpg.handler_registry():
    with dpg.window(label="user.2 to txt converter", tag="main_window", width=800, height=600, pos=(300, 100)):
        with dpg.child_window(label="Converter", width=800, height=600, border=False):
            dpg.add_text("Select Mode:")
            dpg.add_radio_button(("Decode", "Encode"), tag="mode", default_value="Decode")
            
            dpg.add_text("Select File:")
            dpg.add_input_text(tag="file_path", width=400)
            dpg.add_button(label="Browse...", callback=select_file_callback)
            dpg.add_button(label="Run Script", callback=run_script)

show_txt_to_pdf_window()

dpg.show_viewport()
dpg.setup_dearpygui()
dpg.start_dearpygui()
dpg.destroy_context()
