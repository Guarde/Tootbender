import disnake, os
from datetime import datetime
from Helpers import globals

dirpath = os.path.dirname(os.path.realpath(__file__))
temp_path = os.path.join(os.path.join(dirpath, ".."), "temp")

def filesize():
    size = 0
    for path, dirs, files in os.walk(temp_path):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return round(size / 1000000, 2)

def verify_tmb(tmb:dict):
    compare = ["notes", "name", "shortName", "trackRef", "year", "author", "genre", "description", "difficulty", "savednotespacing", "endpoint", "timesig", "tempo"]
    missing = []

    for l in compare:
        if l in list(tmb.keys()):
            continue
        missing.append(l)

    if len(missing) > 0:
        return missing
    return

def get_duration(tmb:dict):
    tempo = tmb["tempo"]
    beats = tmb["endpoint"]
    return (60/tempo) * beats

def get_duration_string(dur:float):
    secs = round(dur)
    if secs >= 3600:
        hours, mins = divmod(secs, 3600)
        mins, secs = divmod(mins, 60)
        return f"{hours}:{str(mins).rjust(2, '0')}:{str(secs).rjust(2, '0')}"
    elif secs >= 60:
        mins, secs = divmod(secs, 60)
        return f"{mins}:{str(secs).rjust(2, '0')}"
    else:
        return f"{secs} Seconds"


class Song():
    name = str()
    file_hash = str()
    creator = str()
    creator_id = int()
    timestamp = None
    tmb = dict()
    video = str()
    download = str()
    duration = float()
    duration_string = str()
    audio_length = int()
    files = list()
    filesize = float()
    bgpath = str()
    def __init__(self, tmb:dict, message:disnake.Message, video:str, download:str, files:list, hash:str):
        missing_keys = verify_tmb(tmb)
        if missing_keys:
            raise Exception("MissingKeys", missing_keys)
        self.name = tmb["name"]
        if not message == None:
            self.creator = message.author.display_name
            self.creator_id = message.author.id
        self.timestamp = datetime.now()
        self.tmb = tmb
        self.video = video
        self.download = download
        self.file_hash = hash
        self.duration = get_duration(tmb)
        self.duration_string = get_duration_string(self.duration)
        if not files == None:
            self.files = files
            self.filesize = filesize()

    def as_dict(self):
        return {"name" : self.name, 
                "creator" : self.creator, 
                "creator_id" : self.creator_id, 
                "timestamp" : self.timestamp.timestamp(), 
                "tmb" : self.tmb, 
                "video" : self.video, 
                "download" : self.download, 
                "audio_length" : self.audio_length,
                "duration" : self.duration,
                "duration_string" : self.duration_string,
                "files" : self.files,
                "filesize" : self.filesize,
                "file_hash" : self.file_hash
                }

    def to_embed(self, comment:str):
        detailsleft= []
        detailsleft.append("**Artist:** " + self.tmb["author"])
        detailsleft.append("**Genre:** " + self.tmb["genre"])
        detailsleft.append("**Year:** " + str(self.tmb["year"]))
        detailsleft.append("**Difficulty:** " + str(self.tmb["difficulty"]))
        detailsleft.append("**Tempo:** " + str(self.tmb["tempo"]))
        detailsleft.append("**Duration:** " + self.duration_string)

        detailsright = []
        detailsright.append("**trackRef:** " + self.tmb["trackRef"])
        detailsright.append("**Filesize:** " + str(self.filesize) + " MB")
        detailsright.append("**Files:** \n- " + "\n- ".join(self.files))
        
        desc = f"by <@{self.creator_id}>"
        if len(comment.strip()) > 0:
            desc +=  f"\n \"{comment.strip()}\""
        emb = disnake.Embed(title=self.name, description = desc, color=disnake.Colour.dark_teal())

        emb.add_field(name = "Description: ", value = self.tmb["description"].strip(), inline=False)
        emb.add_field(name = "Details:", value = "\n".join(detailsleft), inline=True)
        emb.add_field(name = "\u200B", value = "\n".join(detailsright), inline=True)
        return emb
