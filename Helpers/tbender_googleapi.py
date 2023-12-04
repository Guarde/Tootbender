import gspread, os, time, json
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials
from Helpers import globals

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]


class GoogleAPI():
    def __init__(self):
        self.sheet_client = None
        self.sheet = None
        self.pack_sheet = None
        self.template = None
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(globals.main_dir, "credentials.json"), scope)
        self.drive_client = None

    def connect(self):
        global sheet
        try:
            self.sheet_client = gspread.authorize(self.creds)
            self.sheet = self.sheet_client.open_by_key(globals.settings.general.spreadsheet_id).get_worksheet(int(globals.settings.general.spreadsheet_songlist_index))  # Open the spreadhseet
            self.drive_client = build('drive', 'v3', credentials=self.creds, static_discovery=False)
            self.pack_sheet = self.sheet_client.open_by_key(globals.settings.curation.pack_spreadsheet_id)  # Open the spreadhseet
            self.template = self.pack_sheet.worksheet("template")
        except gspread.exceptions.SpreadsheetNotFound:
            return ["warning", "Invalid spreadsheet ID"]
        except gspread.exceptions:
            return ["warning", "Unable to process google credentials.json"]
        except Exception:
            return ["warning", "Unable to process google credentials.json"]
        return["info", "Google API connection established"]

    async def download_file(self, url, maxsize):
        file_id = url.split("/view")[0].replace("https://drive.google.com/file/d/", "")
        maxsize = max(int(globals.settings.upload.max_file_size), maxsize)
        try:
            request = self.drive_client.files().get_media(fileId=file_id)
            with open(os.path.join(globals.temp_dir, "song.zip"), 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status.total_size/1000000 > maxsize:
                        return "toobig"
            return True
        except Exception as e:
            error = json.loads(e.args[1])["error"]
            return (error["code"], error["message"])

    def post_spreadsheet(self, song):
        title = song.name
        artist = song.tmb["author"]
        creator = song.creator
        difficulty = song.tmb["difficulty"]
        length = song.duration_string
        bpm = song.tmb["tempo"]
        genre = song.tmb["genre"]
        download = song.download
        download = f"=HYPERLINK(\"{download}\", \"Download\")"
        self.sheet.append_row([title, artist, creator, length, difficulty, bpm, genre, download.strip()], value_input_option="USER_ENTERED")

    def add_pack_charts(self, packname, charts, count:int):        
        page = self.pack_sheet.worksheet(packname)
        page.update_cell(3, 2, f"{count} Charts")
        rows = []
        for c in charts:
            rows.append([c.chart_id, c.title, c.author, c.charter, c.difficulty, f"=HYPERLINK(\"{c.download}\", \"Download\")"])
        page.append_rows(rows, value_input_option="USER_ENTERED")

    def remove_pack_charts(self, packname:str, chart_ids:list):
        for chart_id in chart_ids:
            chart_id = str(chart_id)
            page = self.pack_sheet.worksheet(packname)
            cell = page.find(in_column=2, query=chart_id)
            page.delete_rows(cell.row)

    def create_pack_page(self, packname:str, title:str):
        page: gspread.Worksheet = self.template.duplicate(new_sheet_name=packname)
        page.update_cell(2, 2, title)

    def delete_pack_page(self, packname:str):
        page = self.pack_sheet.worksheet(packname)
        self.pack_sheet.del_worksheet(page)
 
    def get_pack_url(self, packname:str):
        page = self.pack_sheet.worksheet(packname)
        return page.url