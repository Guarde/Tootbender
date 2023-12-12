import aiohttp, os, json, math, random, disnake
from fuzzywuzzy import fuzz
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


path = os.path.dirname(__file__)

class AllSongs:
    def load_file(self):
        with open(helpers_dir + "/songs.json", "r", encoding="utf-8") as f:
            self.songs = json.load(f)

    def save_file(self, encoding="utf-8"):
        with open(helpers_dir + "/songs.json", "w") as f:
            json.dump(self.songs, f)

    def __init__(self):
        self.songs = []
        self.fields = ["name",  "song_length", "difficulty", "download", "id", "mirror", "author", "charter", "is_rated"]
        self.data_time = datetime.now()
        self.data = dict()
        self.pages = int()
        self.completed = 0
        self.time_passed = 0
        self.eta = 0
    
    def search(self, query=str, is_rated=None):
        results = []
        for song in self.songs:
            if is_rated != None and song["is_rated"] != is_rated:
                continue
            if query.lower() in song["name"].lower():
                results.append(song)
                continue
                
            if song["name"] == None:
                song["name"] = ""
            if song["author"] == None:
                song["author"] = ""
            if song["charter"] == None:
                song["charter"] = ""
            name_ratio = fuzz.token_set_ratio(query.lower(), song["name"].lower())
            author_ratio = fuzz.token_set_ratio(query.lower(), song["author"].lower())
            charter_ratio = fuzz.token_set_ratio(query.lower(), song["charter"].lower())            
            if max(name_ratio, author_ratio, charter_ratio) >= 80:
                results.append(song)
        return(results)
    
    def get_random(self, is_rated=None):
        choices = self.songs
        if is_rated in [True, False]:
            choices = [song for song in self.songs if song["is_rated"] == is_rated]
        return(random.choice(choices))

    def add_song(self, song, song_length:float, download:str, charter:str, author:str):
        added_song = dict()
        added_song["Rated"] = False
        added_song["song_length"] = song_length
        added_song["download"] = download
        added_song["charter"] = charter
        added_song["author"] = author
        for f in self.fields:
            added_song[f] = song[f]
        self.songs.insert(0, added_song)
        self.save_file()
        self.data_time = datetime.now()

    async def get_songs(self, inter:disnake.ApplicationCommandInteraction):
        emb = disnake.Embed(title="Retrieving Song List from TootTally...", description="Preparing...", color=disnake.Color.orange())
        await inter.send(embed=emb)
        start_time = datetime.timestamp(datetime.now())
        self.completed = 0

        def progress_bar():
            progress = math.floor((self.completed/self.pages) * 100)
            bar = "I" * progress + "." * (100 - progress)
            return bar
        
        def progress_message():
            line_1 = f"Operation is estimated to take {round(self.eta, ndigits=1)} seconds"
            line_2 = progress_bar()
            line_3 = f"**{round((self.completed/self.pages) * 100)}%** (Page {self.completed} of {self.pages}) \n **Time Elapsed:** {round(self.time_passed, ndigits=1)} seconds \n **Time Remaining:** {round(self.eta-self.time_passed, ndigits=1)} seconds"
            return f"{line_1}\n{line_2}\n{line_3}"

        async def get_req(self, first=False):
            if first:
                r = await session.get("https://toottally.com/api/search?page_size=300&fields=" + ",".join(self.fields))
            else:
                r = await session.get(self.data["next"])

            if not r.ok:
                print("Error: ", r.status, r.reason)
                return()
            self.data = json.loads(await r.read())

            if first:
                self.songs = []
                self.pages = math.ceil(self.data["count"]/len(self.data["results"]))
                print("Total pages:", self.pages)
            self.songs = self.songs + self.data["results"]
            self.completed += 1
            self.time_passed = datetime.timestamp(datetime.now()) - start_time
            self.eta = self.time_passed * (self.pages/self.completed)
            emb = disnake.Embed(title="Retrieving Song List from TootTally...", description=progress_message(), color=disnake.Color.orange())
            await inter.edit_original_message(embed=emb)
            print("Page", self.completed, "of", self.pages, "completed in", round(self.time_passed, ndigits=1), "seconds (ETA:", round(self.eta, ndigits=1), "seconds; Remaining:", round(self.eta-self.time_passed, ndigits=1), "seconds)")
        await get_req(self, True)
        while "next" in list(self.data.keys()) and self.data["next"] is not None:
            await get_req(self)
        self.save_file()
        self.data_time = datetime.now()
        print("Operation completed in", round(self.time_passed, ndigits=1), "seconds (ETA:", round(self.eta, ndigits=1), "seconds; Remaining:", round(self.eta-self.time_passed, ndigits=1), "seconds)")
        emb = disnake.Embed(title="Retrieved Song List from TootTally!", description=f"Retrieved {len(self.songs)} charts in {round(self.time_passed, ndigits=1)} seconds", color=disnake.Color.green())
        await inter.edit_original_message(embed=emb)
        
    def to_discord(self, chart:dict):
        if chart["charter"] == None or chart["charter"].strip() == "":
            chart["charter"] = "*Unknown*" 
        if chart["download"] == None:
            chart["download"] = "*No Download*"
        else:
            chart["download"] = f"[Download]({chart['download']})"
        if chart["mirror"] == None:
            chart["mirror"] = "*No Mirror*"
        else:
            chart["mirror"] = f"[TootTally Mirror]({chart['mirror']})"
        if chart["is_rated"]:
            chart["is_rated"] = "✅"
        else:
            chart["is_rated"] = "❌"
         
        
        text = f"***by {chart['author']}***\n\n**Charter:** {chart['charter']}\n**Difficulty:** {round(chart['difficulty'],ndigits=1)}\n**Rated:** {chart['is_rated']}\n[Leaderboard](https://toottally.com/song/{chart['id']})\n{chart['download']} | {chart['mirror']}"
        
        return text
        

all_charts = AllSongs()
all_charts.load_file()