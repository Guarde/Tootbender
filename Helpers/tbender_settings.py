import os, re, json, configparser
from datetime import datetime
import numpy as np

#Config keys for comparison
keys_general = ["debug", "bot_token", "submissions_channel", "facts_channel", "charts_channel", "charts_channel2", "spreadsheet_id", "spreadsheet_songlist_index", "owners", "mod_roles", "dm_rejections", "reject_delete_timer", "allow_comment", "allow_links", "do_threads"]
keys_upload = ["youtube", "dropbox", "googledrive", "discord_uploads", "max_file_size", "tt_api_key", "hastebin_api_key"]
keys_curation = ["curator_forum_channel", "public_forum_channel", "pack_spreadsheet_id"]
keys_moderation = ["staff_channel_id", "enable_spam_filter", "passive_filter", "timeout_duration", "rate_limit_time", "rate_limit_channels"]
keys_verification = ["file_structure", "unique_trackref", "song_length", "note_pitch", "note_position", "background", "json", "alphanumeric", "allowed_filenames"]
keys_mysql = ["host", "user", "password", "database", "table"]

home = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
settings_dir = os.path.join(home, "config.ini")
language_dir = os.path.join(home, "language.ini")

class obj(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)

def dict2obj(d):
    return json.loads(json.dumps(d), object_hook=obj)


def compare_keys(confile, list_in:list, config_key:str):
    diff = np.setdiff1d(list_in, list(confile[config_key.lower()].keys()))
    if len(diff) > 0:
        return [config_key + "." + f", {config_key}.".join(diff).upper()]
    else:
        return []

def ini2dict(path:str):
    conf = configparser.ConfigParser()
    conf.read(path)
    dict = {}
    for section in conf.sections():
        dict[section.lower()] = {}
        for option in conf.options(section):
            op = conf.get(section, option)
            #Parse Booleans
            if op == "True":
                dict[section.lower()][option] = True
            elif op == "False":
                dict[section.lower()][option] = False
            #Parse lists
            else:
                search = re.findall("^\[.*\]", op)
                if search and op in search:
                    outlist = []
                    #Strip list whitespaces
                    for item in op[1:len(op)-1].split(','):
                        outlist.append(item.strip())
                    dict[section.lower()][option] = outlist
                else:
                    dict[section.lower()][option] = op.replace("\\n", "\n")
    return dict

class botset():
    general, upload, verification, curation, moderation, mysql, lang = [{}, {}, {}, {}, {}, {}, {}]
    def __init__(self):
        #Exit
        if not os.path.exists(settings_dir):
            botLog("fatal", "Unable to access ./config.ini\n Exiting...")
            quit()
        if not os.path.exists(language_dir):
            botLog("fatal", "Unable to access ./language.ini\n Exiting...")
            quit()

        #Config parser object to clean dictionary
        config = ini2dict(settings_dir)

        #Check for missing config keys
        missing = []
        try:
            missing += (compare_keys(config, keys_general, "GENERAL"))
            missing += (compare_keys(config, keys_upload, "UPLOAD"))
            missing += (compare_keys(config, keys_curation, "CURATION"))
            missing += (compare_keys(config, keys_moderation, "MODERATION"))
            missing += (compare_keys(config, keys_verification, "VERIFICATION"))
            missing += (compare_keys(config, keys_mysql, "MYSQL"))

        except Exception as e:
            botLog("fatal",  f"The following error occured when attempting to load config.ini: [{type(e).__name__}: {e}]")
            botLog("info",  "Exiting...")
            quit()
        if len(missing) > 0:
            botLog("warning",  "Encountered an error with the following config key(s):\n\t" + '\n\t'.join(missing))

        else:
            botLog("info", "config.ini loaded successfully")

        #Dictionary to object
        self.general = dict2obj(config["general"])
        self.upload = dict2obj(config["upload"])
        self.curation = dict2obj(config["curation"])
        self.moderation = dict2obj(config["moderation"])
        self.verification = dict2obj(config["verification"])
        self.mysql = dict2obj(config["mysql"])
        try:
            self.lang = dict2obj(ini2dict(language_dir))
        except Exception as e:
            botLog("fatal",  f"The following error occured when attempting to load language.ini: [{type(e).__name__}: {e}]")
            botLog("info",  "Exiting...")
            quit()
        else:            
            botLog("info", "language.ini loaded successfully")

def botLog(level:str, message:str):
    time = datetime.now().strftime("%b-%d-%Y %H:%M:%S")
    print(f"({time}) [{level.upper()}] {message}")