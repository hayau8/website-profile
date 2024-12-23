import os
from datetime import datetime
def create_log(message):
    logs_folder = os.path.join(os.getcwd(), 'logs')
    log_file_path = os.path.join(logs_folder, 'log.txt')
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = [f"[{current_time}] {i}\n" for i in message.split('\n')]
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.writelines(log_entry)


create_log("Ale jazz\nulala")