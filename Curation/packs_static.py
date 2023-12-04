import disnake, os
from Helpers import globals
header = "Curation Module"
color = disnake.Color.fuchsia()
cur_path = os.path.join(globals.main_dir, "Curation")
packs = dict()
threads = dict()
    
# Classes
class pack_chart():
    def __init__(self, chart_id:int=None, title:str=None, author:str=None, charter:str=None, difficulty:float=None, download:str=None):
        self.chart_id = chart_id
        self.title = title
        self.author = author
        self.charter = charter
        self.difficulty = difficulty
        self.download = download

    def to_json(self):
        return {
          "chart_id": self.chart_id,
          "title": self.title,
          "author": self.author,
          "charter": self.charter,
          "difficulty": self.difficulty,
          "download": self.download
        }
    
    def from_json(self, json_in:dict()):
        self.chart_id = json_in["chart_id"]
        self.title = json_in["title"]
        self.author = json_in["author"]
        self.charter = json_in["charter"]
        self.difficulty = json_in["difficulty"]
        self.download = json_in["download"]
        return self
    
    def from_toottally(self, json_in:dict()):
        self.chart_id = json_in["results"][0]["id"]
        self.title = json_in["results"][0]["name"]
        self.author = json_in["results"][0]["author"]
        self.charter = json_in["results"][0]["charter"]
        self.difficulty = round(json_in["results"][0]["difficulty"], ndigits=1)
        self.download = json_in["results"][0]["mirror"]
        return self

class pack():
    def __init__(self, name:str()=None, source_thread:int()=None):
        self.name = name
        self.description = str()
        self.source_thread = source_thread
        self.target_thread = int()
        self.curator_id = int()
        self.charts = dict()

    def __repr__(self):
        return f"{self.to_json()}"

    def add_chart(self, chart:pack_chart()):
        self.charts[int(chart.chart_id)] = chart
        return chart
 
    def remove_chart(self,  chart:pack_chart()):
        c: pack_chart = self.charts.pop(int(chart.chart_id))
        return c
 
    def remove_id(self,  chart:int):
        c: pack_chart = self.charts.pop(int(chart))
        return c
 
    def get_chart(self,  chart:pack_chart()):
        if str(chart) in list(self.charts.keys()):
            return self.charts[str(chart)]
        return False

    def has_chart(self,  chart:int):
        allids = []
        for c in list(self.charts.values()):
            allids.append(c.chart_id)
        if int(chart) in allids:
            return True
        return False
 
    async def get_source_thread(self, client:disnake.Client):
        t: disnake.Thread = await client.fetch_channel(self.source_thread)
        return t
    
    async def get_target_thread(self, client:disnake.Client):
        t: disnake.Thread = await client.fetch_channel(self.target_thread)
        return t
 
    async def get_message(self, client:disnake.Client):
        t = await client.fetch_channel(self.target_thread)
        m: disnake.Message = await t.fetch_message(self.target_thread)
        return m
        
    def to_json(self):
        json_out = {
            "title": self.title,
            "name": self.name,
            "description": self.description,
            "source_thread": self.source_thread,
            "target_thread": self.target_thread,
            "curator_id": self.curator_id,
            "charts": dict()
            }
        for chart in list(self.charts.values()):
            json_out["charts"][chart.chart_id] = chart.to_json()
        return json_out   

    def to_request_data(self, api_key):
        chart_list = []
        for c in list(self.charts.values()):
            chart_list.append(c.chart_id)
        if len(chart_list) == 0:
            chart_list = [420]
            
        json_out = {
            "title": self.title,
            "name": self.name,
            "description": self.description,
            "curator_id": self.curator_id,
            "charts": chart_list,
            "api_key": api_key
            }
        return json_out

    def from_json(self, json_in:dict()):
        self.title = json_in["title"]
        self.name = json_in["name"]
        self.description = json_in["description"]
        self.source_thread = json_in["source_thread"]
        self.target_thread = json_in["target_thread"]
        self.curator_id = json_in["curator_id"]
        self.charts = dict()
        for chart in list(json_in["charts"].values()):
            self.charts[chart["chart_id"]] = pack_chart().from_json(chart)
        return self
        
    def add_to_dict(self):
        packs[self.name] = self
        threads[self.source_thread] = self.name