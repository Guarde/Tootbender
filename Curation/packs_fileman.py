import json, shutil
import os
from Helpers import globals
from Curation import packs_static

# File Functions
def reload_packs_file():
    global threads
    with open(os.path.join(packs_static.cur_path, "packs.json"), mode="r") as f:
        packs_json = json.load(f)
    for key in list(packs_json["threads"].keys()):
        packs_static.threads[int(key)] = packs_json["threads"][key]
    for p in list(packs_json["packs"].values()):
        packs_static.packs[p["name"]] = packs_static.pack().from_json(p)        
    globals.botLog("Info", "packs.json (re-)loaded successfully.")
        
def save_packs_file():
    packs_json = {}
    for p in list(packs_static.packs.values()):
        packs_json[p.name] = p.to_json()
    with open(os.path.join(packs_static.cur_path, "packs.json"), mode="w") as f:
        json.dump({"packs": packs_json, "threads": packs_static.threads}, f, indent = 5)
        globals.botLog("Info", "packs.json updated successfully.")

def create_folder(packname:str):
    p = os.path.join(packs_static.cur_path, "packs", packname)
    if not os.path.exists(p):
        os.mkdir(p)
    if not os.path.exists(os.path.join(p, "temp")):
        os.mkdir(os.path.join(p, "temp"))
    if not os.path.exists(os.path.join(p, "charts")):
        os.mkdir(os.path.join(p, "charts"))
    return p

def delete_folder(packname:str):
    p = os.path.join(packs_static.cur_path, "packs", packname)
    if not os.path.exists(p):
        return
    shutil.rmtree(p)

def download_extract_chart(packname:str, chart:packs_static.pack_chart):
    dl = chart.download
    name = chart.name
    p = create_folder(packname)

def download_extract_charts(packname:str):
    p = create_folder(packname)