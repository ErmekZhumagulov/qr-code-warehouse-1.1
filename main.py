from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout
import csv
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket
from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtWidgets import QAbstractItemView
from PyQt6.QtCore import QTimer
import sys

Form, Window = uic.loadUiType("ui.ui")

app = QApplication([])
window = Window()
form = Form()
form.setupUi(window)
window.show()
errorWindow = QMessageBox()

def load_items_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            items = [line.strip() for line in file.readlines()]
        return items
    except Exception as e:
        print("Error loading items from file:", e)
        return []

def load_items_from_file_machine(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            items = [line.strip() for line in file.readlines()]
        return items
    except Exception as e:
        print("Error loading items from file:", e)
        return []

def read_receiver_emails(filename):
    try:
        with open(filename, 'r') as file:
            # Read all lines from the file
            lines = file.readlines()
            # Remove leading and trailing whitespace from each line
            emails = [line.strip() for line in lines if line.strip()]
        return emails
    except FileNotFoundError:
        print("Receiver emails file not found.")
        return []
    except Exception as e:
        print("Error reading receiver emails:", e)
        return []

def update_quantity_field():
    form.quantity_text_field.setText("1")
    form.quantity_text_field.setFocus()
    text = form.qr_text_field.text()

def update_qr_text_field(index):
    form.qr_text_field.setFocus()
    form.quantity_text_field.setText("1")

def write_to_csv(selected_item, selected_machine, qr_text_content, quantity_value):
    filename = "logs.csv"
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(["Дата", "Время", "Сотрудник", "Оборудование", "Запчасть", "Количество"])

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        writer.writerow([current_date, current_time, selected_item, selected_machine, qr_text_content, quantity_value])

def submit_action():
    quantity_value = form.quantity_text_field.text()
    selected_item = form.takers_list.currentText()
    selected_machine = form.machine_list.currentText()
    qr_text_content = form.qr_text_field.text()

    # Check if qr_text_field is empty
    if not qr_text_content:
        QMessageBox.warning(window, "Внимание", "Отсканируйте qr-код на запчасти")
        return
    if not quantity_value:
        QMessageBox.warning(window, "Внимание", "Введите количество")
        return

    # Proceed with submission if qr_text_field is not empty
    write_to_csv(selected_item, selected_machine, qr_text_content, quantity_value)

    form.qr_text_field.clear()
    form.quantity_text_field.clear()

    form.qr_text_field.setFocus()
    form.quantity_text_field.setText("1")

    # Update history table with new data
    load_history_from_csv()

    # Show success message
    success_message = QMessageBox(window)
    success_message.setText("Запись внесена")
    success_message.setWindowTitle("Готово")
    success_message.show()

    # Close success message after 2 seconds
    QTimer.singleShot(2000, success_message.close)


def return_action():
    quantity_value = form.quantity_text_field.text()
    qr_text_content = form.qr_text_field.text()

    # Check if qr_text_field is empty
    if not qr_text_content:
        QMessageBox.warning(window, "Внимание", "Отсканируйте qr-код на запчасти")
        return
    if not quantity_value:
        QMessageBox.warning(window, "Внимание", "Введите количество")
        return

    confirmation = QMessageBox.question(window, "Подтверждение", "Вы уверены, что хотите оформить возврат?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    # Обработка результата
    if confirmation == QMessageBox.StandardButton.Yes:
        # Чтение данных из файла logs.csv
        with open('logs.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            logs = list(reader)

        # Переменная для отслеживания, найдено ли значение qr_text_content в logs
        found = False

        # Проверяем наличие qr_text_content в logs и обновляем строку, если найдено
        for row in logs:
            if qr_text_content in row:
                found = True
                # Обновляем последний элемент строки
                row[-1] = row[-1] + '-' + quantity_value
                break

        # Выводим результат проверки
        if found:
            # Перезаписываем файл logs.csv с обновленными данными
            with open('logs.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(logs)

            # Show success message
            return_success_message = QMessageBox(window)
            return_success_message.setText("Возврат оформлен")
            return_success_message.setWindowTitle("Готово")
            return_success_message.show()

            # Close success message after 2 seconds
            QTimer.singleShot(2000, return_success_message.close)
        else:
            QMessageBox.warning(window, "Внимание", "З/ч отсутсвует в списке")

        form.qr_text_field.clear()
        form.quantity_text_field.clear()

        form.qr_text_field.setFocus()
        form.quantity_text_field.setText("1")

        # Update history table with new data
        load_history_from_csv()
    else:
        form.qr_text_field.clear()
        form.quantity_text_field.clear()

        form.qr_text_field.setFocus()
        form.quantity_text_field.setText("1")
        pass

def load_history_from_csv():
    try:
        filename = "logs.csv"
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the first row (header)
            data = list(reader)  # Read all rows from CSV into a list
            data.reverse()  # Reverse the order of rows

            # Clear existing rows in the table
            form.history_table.setRowCount(0)

            # Populate history_table with reversed data
            for row_idx, row in enumerate(data):
                form.history_table.insertRow(row_idx)
                for col_idx, col in enumerate(row):
                    item = QTableWidgetItem(col)
                    form.history_table.setItem(row_idx, col_idx, item)
    except FileNotFoundError:
        print("History file not found.")
    except Exception as e:
        print("Error loading history from CSV:", e)

def clear_quantity_field():
    form.quantity_text_field.clear()
    form.quantity_text_field.setFocus()

def clear_quantity_field_2():
    form.qr_text_field.clear()
    form.qr_text_field.setFocus()

def add_number_to_quantity(number):
    current_text = form.quantity_text_field.text()
    new_text = current_text + number
    form.quantity_text_field.setText(new_text)

def show_report_popup():
    # Create a popup dialog
    report_dialog = QWidget()
    report_dialog.setWindowTitle("Отчет")

    # Create widgets for the report dialog
    report_label = QLabel("Введите пароль")
    report_text_field = QLineEdit()
    send_button = QPushButton("Отправить")

    # Create number buttons
    number_layout = QVBoxLayout()
    number_row1_layout = QHBoxLayout()
    number_row2_layout = QHBoxLayout()

    for num in range(1, 6):
        button = QPushButton(str(num))
        button.clicked.connect(lambda _, n=num: report_text_field.insert(str(n)))
        number_row1_layout.addWidget(button)

    for num in range(6, 10):
        button = QPushButton(str(num))
        button.clicked.connect(lambda _, n=num: report_text_field.insert(str(n)))
        number_row2_layout.addWidget(button)

    zero_button = QPushButton("0")
    zero_button.clicked.connect(lambda: report_text_field.insert("0"))

    number_row2_layout.addWidget(zero_button)

    number_layout.addLayout(number_row1_layout)
    number_layout.addLayout(number_row2_layout)

    # Читаем содержимое файла и сохраняем его в переменной
    with open("Список получателей.txt", "r") as file:
        recipients = file.read()

    # Create a label for the note
    note_label_1 = QLabel("Отчет будет отправлен на почту:")
    note_label_2 = QLabel(recipients)
    note_label_3 = QLabel("-----------------------------------------------------------------------------------------")
    note_label_4 = QLabel("(Внимание: при отправке отчета на почту отображаемые запчасти переносятся")
    note_label_5 = QLabel("          в архивный файл, и они больше не будут отображаться в истории)")

    # Create a layout for the report dialog
    layout = QVBoxLayout()
    layout.addWidget(report_label)
    layout.addWidget(report_text_field)
    layout.addLayout(number_layout)
    layout.addWidget(send_button)
    layout.addWidget(note_label_1)  # Add the note label
    layout.addWidget(note_label_2)  # Add the note label
    layout.addWidget(note_label_3)  # Add the note label
    layout.addWidget(note_label_4)  # Add the note label
    layout.addWidget(note_label_5)  # Add the note label

    # Set the layout for the report dialog
    report_dialog.setLayout(layout)

    # Create QLabel widgets for displaying messages
    message_label = QLabel()

    def send_report():
        try:
            # Check internet connectivity
            host = "8.8.8.8"
            port = 53
            timeout = 3  # in seconds
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            print("Internet connection is available.")

            with open("Пароль.txt", "r") as password_file:
                correct_password = password_file.read().strip()
        except FileNotFoundError:
            print("Password file not found.")
            return
        except Exception as e:
            message = "Нет подключения к интернету"
            # Show a pop-up message box
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Статус отправки отчета")
            msg_box.setText(message)
            msg_box.exec()

            print("No internet connection. Cannot send the report.")
            return

        report_text = report_text_field.text()
        if report_text == correct_password:
            # Email configuration
            sender_email = "order.notifier@mail.ru"
            # Read recipient emails from the file
            receiver_emails = read_receiver_emails("Список получателей.txt")
            if not receiver_emails:
                print("No recipient emails found.")
                return

            password = "9hcp6nb708MV8sbHVrnd"  # Use your Mail.ru email password

            try:
                # Read the content of the logs.csv file
                with open("logs.csv", "r") as csv_file:
                    reader = csv.reader(csv_file)
                    rows = list(reader)

                    # Close the file after reading
                    csv_file.close()

                    # Create message container
                    message = MIMEMultipart()
                    message['From'] = sender_email
                    message['To'] = ', '.join(receiver_emails)
                    message['Subject'] = "Журнал запчастей"

                    # Create HTML table
                    html_table = "<html><body><h2>Журнал запчастей</h2><table border='1'><tr>"
                    for row in rows[0]:  # Add column headers
                        html_table += "<th>" + row + "</th>"
                    html_table += "</tr>"

                    # Add rows to the HTML table
                    for row in rows[1:]:
                        html_table += "<tr>"
                        for column in row:
                            html_table += "<td>" + column + "</td>"
                        html_table += "</tr>"
                    html_table += "</table></body></html>"

                    # Attach HTML content as email body
                    message.attach(MIMEText(html_table, 'html'))

                    # Connect to the Mail.ru SMTP server
                    smtp_server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
                    smtp_server.login(sender_email, password)

                    # Send the email to all recipients
                    smtp_server.sendmail(sender_email, receiver_emails, message.as_string())

                    # Close the connection to the SMTP server
                    smtp_server.quit()

                    print("All emails sent successfully!")

                    message = "Пароль верный. Отчет отправлен."
                    print("Password is correct. Report sent.")

                    # Create the 'archive' folder if it doesn't exist
                    archive_folder = os.path.join(os.path.dirname(__file__), "archive")
                    if not os.path.exists(archive_folder):
                        os.makedirs(archive_folder)

                    # Move logs.csv to the 'archive' folder and rename it
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    current_time = datetime.now().strftime("%H-%M-%S")
                    new_filename = f"the report was sent at {current_date} {current_time}.csv"
                    os.rename("logs.csv", os.path.join(archive_folder, new_filename))
                    print("logs.csv moved to 'archive' folder and renamed successfully.")

                    # Clear the history table
                    form.history_table.setRowCount(0)

            except Exception as e:
                print("Error:", e)

        else:
            message = "Неверный пароль. Отчет не отправлен."
            print("Password is incorrect. Please try again.")

        # Show a pop-up message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Статус отправки отчета")
        msg_box.setText(message)
        msg_box.exec()

        # Clear the report text field
        report_text_field.clear()
        report_dialog.close()

    # Connect the send button to the send_report function
    send_button.clicked.connect(send_report)

    # Show the report dialog
    report_dialog.show()

# Connect the report button to the show_report_popup function
form.report_button.clicked.connect(show_report_popup)

def main():
    try:
        # Load items from the text file
        items = load_items_from_file("Список сотрудников.txt")

        # Add items to the comboBox
        for item in items:
            form.takers_list.addItem(item)

        # Define the slot function for combo box activation
        def on_combo_box_activated(index):
            selected_item = form.takers_list.itemText(index)
            # print("Selected Item:", selected_item)

        # Connect the activated signal of the comboBox to the slot function
        form.takers_list.activated.connect(on_combo_box_activated)
        # Connect the activated signal of the comboBox to the update_qr_text_field slot function
        form.takers_list.activated.connect(update_qr_text_field)

        # Load items from the text file
        items_machine = load_items_from_file_machine("Список оборудования.txt")

        # Add items to the comboBox
        for item_machine in items_machine:
            form.machine_list.addItem(item_machine)

        # Define the slot function for combo box activation
        def on_combo_box_activated_machine(index_machine):
            selected_item_machine = form.machine_list.itemText(index_machine)
            # print("Selected Item machine:", selected_item_machine)

        # Connect the activated signal of the comboBox to the slot function
        form.machine_list.activated.connect(on_combo_box_activated_machine)
        # Connect the activated signal of the comboBox to the update_qr_text_field slot function
        form.machine_list.activated.connect(update_qr_text_field)

        # Connect the returnPressed signal of the qr_text_field to update_quantity_field
        form.qr_text_field.returnPressed.connect(update_quantity_field)

        # Connect the clicked signal of the submit button to the submit_action and return_action slot function
        form.submit_button.clicked.connect(submit_action)
        form.submit_button_2.clicked.connect(return_action)

        # Connect the clicked signal of the clear button to the clear_quantity_field slot function
        form.clear_button.clicked.connect(clear_quantity_field)
        form.clear_button_2.clicked.connect(clear_quantity_field_2)

        # Connect the number buttons to the add_number_to_quantity function
        form.number_0.clicked.connect(lambda: add_number_to_quantity("0"))
        form.number_1.clicked.connect(lambda: add_number_to_quantity("1"))
        form.number_2.clicked.connect(lambda: add_number_to_quantity("2"))
        form.number_3.clicked.connect(lambda: add_number_to_quantity("3"))
        form.number_4.clicked.connect(lambda: add_number_to_quantity("4"))
        form.number_5.clicked.connect(lambda: add_number_to_quantity("5"))
        form.number_6.clicked.connect(lambda: add_number_to_quantity("6"))
        form.number_7.clicked.connect(lambda: add_number_to_quantity("7"))
        form.number_8.clicked.connect(lambda: add_number_to_quantity("8"))
        form.number_9.clicked.connect(lambda: add_number_to_quantity("9"))

        # Add columns to the history_table
        form.history_table.setColumnCount(6)  # Set the number of columns
        form.history_table.setHorizontalHeaderLabels(["Дата", "Время", "Сотрудник", "Оборудование", "Запчасть", "Количество"])  # Set column headers

        # Set the size of the third and fourth columns
        form.history_table.setColumnWidth(2, form.history_table.columnWidth(2) * 2)  # Fourth column
        form.history_table.setColumnWidth(3, form.history_table.columnWidth(3) * 2)  # Fourth column
        form.history_table.setColumnWidth(4, form.history_table.columnWidth(4) * 5)  # Fifth column

        # Load history from CSV when the application starts
        load_history_from_csv()

        # Set QTableWidget to not editable
        form.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    except KeyboardInterrupt:
        app.quit()  # Exit the application if interrupted by the user
    except Exception as e:
        print(e)

    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
    main()
