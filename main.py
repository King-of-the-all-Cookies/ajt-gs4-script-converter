import tkinter as tk
from tkinter import filedialog
from dearpygui import dearpygui as dpg
import os
from fpdf import FPDF
import re

# Функция для удаления тегов и создания PDF
def remove_tags_and_create_pdf(text, input_file_path):
    text = text.replace(r'\linebreak|', '~linebreak~')
    # Удаление всех тегов \...| (например, \cmd109|\14|, \speed|\7|, \cmd095|\L729|\0|\0|)
    cleaned_text = re.sub(r'\\[^|]+\|[^|]*\|', '', text)

    # Разбиение текста на реплики по \linebreak| (каждая реплика - отдельный диалог)
    dialogues = cleaned_text.split(r'~linebreak~')

    # Создание PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Настройка шрифта для таблицы
    pdf.set_font("Arial", size=12)

    # Добавление заголовка таблицы
    pdf.cell(30, 10, txt="Page", border=1, align='C')
    pdf.cell(160, 10, txt="Dialogue", border=1, ln=True, align='L')

    # Переменная для отслеживания номера реплики
    page_number = 1

    for dialogue in dialogues:
        if dialogue.strip():  # Игнорируем пустые строки
            # Добавление строки в таблицу
            pdf.cell(30, 10, txt=str(page_number), border=1, align='C')
            pdf.cell(160, 10, txt=dialogue.strip(), border=1, ln=True, align='L')
            page_number += 1

    # Сохранение PDF с тем же именем, что и исходный файл, но с расширением .pdf
    pdf_output_path = os.path.splitext(input_file_path)[0] + ".pdf"
    pdf.output(pdf_output_path)
    print(f"PDF saved as {pdf_output_path}")

def on_txt_file_upload(sender, app_data):
    # Чтение файла
    file_path = app_data['file_path']
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Создание PDF
    remove_tags_and_create_pdf(text, file_path)

def open_file_dialog():
    # Используем Tkinter для открытия диалога выбора файла
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно Tkinter
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    return file_path

def update_file_path(sender, app_data):
    # Получаем путь к выбранному файлу и вставляем в текстовое поле
    file_path = open_file_dialog()
    if file_path:
        dpg.set_value("manual_file_path", file_path)

def show_txt_to_pdf_window():
    # Обновленная версия с extensions
    with dpg.window(label="TXT-to-PDF", width=500, height=300):
        dpg.add_text("Convert TXT to PDF:")

        # Ручной ввод пути исходного TXT файла
        dpg.add_text("Source TXT File:")
        dpg.add_input_text(label="File Path", tag="manual_file_path", width=350)
        dpg.add_button(label="Browse...", callback=update_file_path)

        # Кнопка для запуска конвертации
        dpg.add_button(label="Convert", callback=manual_file_conversion)

def manual_file_conversion(sender, app_data):
    # Получение пути из текстового поля
    input_file_path = dpg.get_value("manual_file_path")

    if os.path.exists(input_file_path) and input_file_path.endswith(".txt"):
        with open(input_file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Создание PDF
        remove_tags_and_create_pdf(text, input_file_path)
    else:
        # Пропускаем ошибку, если путь не существует, и не останавливаем выполнение
        print("Error: Invalid file path, skipping PDF conversion.")

def run_script(sender, app_data, user_data):
    mode = dpg.get_value("mode")
    file_path = dpg.get_value("file_path")

    if not mode or not file_path:
        dpg.show_item("error_window")
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
        dpg.show_item("error_window")
        return

    commands.extend([
        'color f',
        'cls',
        'echo Done!',
        'pause',
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

    dpg.show_item("success_window")

def select_file_callback(sender, app_data, user_data):
    mode = dpg.get_value("mode")
    if mode == 'Decode':
        dpg.show_item("file_dialog_decode")
    elif mode == 'Encode':
        dpg.show_item("file_dialog_encode")

def file_selected_callback(sender, app_data):
    selected_file = app_data["file_path_name"]
    dpg.set_value("file_path", selected_file)
    dpg.hide_item("file_dialog_decode")
    dpg.hide_item("file_dialog_encode")

dpg.create_context()

# Создаем вьюпорт
dpg.create_viewport(title="GS4CONVERTER", width=1280, height=1024)

# Основное окно
with dpg.handler_registry():
    with dpg.window(label="GS4CONVERTER", tag="main_window", width=640, height=1024):
        with dpg.child_window(label="Converter", width=640, height=1024, border=False):
            dpg.add_text("Select Mode:")
            dpg.add_radio_button(("Decode", "Encode"), tag="mode", default_value="Decode")
            
            dpg.add_text("Select File:")
            dpg.add_input_text(tag="file_path", width=400)
            dpg.add_button(label="Browse...", callback=select_file_callback)

            dpg.add_button(label="Run Script", callback=run_script)

            # Окно выбора файла для Decode (показываются все файлы)
            with dpg.file_dialog(directory_selector=False, show=False, callback=file_selected_callback, tag="file_dialog_decode"):
                dpg.add_file_extension("*")  # Показывать все файлы

            # Окно выбора файла для Encode с расширением *.txt
            with dpg.file_dialog(directory_selector=False, show=False, callback=file_selected_callback, tag="file_dialog_encode"):
                dpg.add_file_extension("*.txt")

            # Окна сообщений об ошибке и успехе
            with dpg.window(label="Error", tag="error_window", modal=True, show=False):
                dpg.add_text("Please select a mode and a file.")
                dpg.add_button(label="Close", callback=lambda: dpg.hide_item("error_window"))
            
            with dpg.window(label="Success", tag="success_window", modal=True, show=False):
                dpg.add_text("Script executed successfully!")
                dpg.add_button(label="Close", callback=lambda: dpg.hide_item("success_window"))

    # Окно TXT-to-PDF
    with dpg.window(label="TXT-to-PDF", width=640, height=1024):
        dpg.add_text("Convert TXT to PDF:")
        dpg.add_text("Source TXT File:")
        dpg.add_input_text(label="File Path", tag="manual_file_path", width=350)
        dpg.add_button(label="Browse...", callback=update_file_path)

        dpg.add_button(label="Convert", callback=manual_file_conversion)

# Разделяем окна и их размещаем
dpg.show_viewport()

# Настроим окно и покажем его
dpg.setup_dearpygui()
dpg.start_dearpygui()
dpg.destroy_context()
