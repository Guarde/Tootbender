import aiohttp, os
from datetime import datetime
from Helpers import tbender_settings
from Helpers.tbender_googleapi import GoogleAPI

helpers_dir = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.join(helpers_dir, "..")
temp_dir = os.path.join(main_dir, "temp")
log_dir = os.path.join(main_dir, "Logs")
current_log = os.path.join(log_dir, datetime.now().strftime("%Y-%M-%d_%H-%M-%S") + ".log")
googleapi: GoogleAPI = None

def create_log():
    with open(current_log, "w") as f:
        f.write("")
    with open(os.path.join(log_dir, "latest.log"), "w") as f:
        f.write("")

create_log()

def write_log(message):
    with open(current_log, "a") as f:
        f.write(message + "\n")
    with open(os.path.join(log_dir, "latest.log"), "a") as f:
        f.write(message + "\n")

def botLog(level:str, message:str):
    time = datetime.now().strftime("%b-%d-%Y %H:%M:%S")
    parsed_message = f"({time}) [{level.upper()}] {message}"
    print(parsed_message)
    write_log(parsed_message)

session = aiohttp.ClientSession()
settings = tbender_settings.botset()