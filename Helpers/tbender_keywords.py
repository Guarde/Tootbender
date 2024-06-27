import json, os
from Helpers.globals import main_dir

def load_keywords():
    with open(os.path.join(main_dir, "keywords.json"), "r") as f:
        return json.load(f)

def check_keyword(user_message:str):
    for key in keywords["keys"]:
        keyword, header, response_message = (key["keyword"], key["header"], key["message"])
        if keyword in user_message:
            return (header, response_message)

keywords = load_keywords()
