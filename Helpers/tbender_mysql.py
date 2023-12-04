from sqlite3 import Cursor
import mysql.connector
from hashlib import sha256
from Helpers import globals

class DatabaseConnection():
    cursor = None
    cnx = mysql.connector.MySQLConnection()
    def __init__(self):
        self.cnx = mysql.connector.connect(host=globals.settings.mysql.host, user=globals.settings.mysql.user, database=globals.settings.mysql.database, passwd=globals.settings.mysql.password, auth_plugin='caching_sha2_password')
        self.cursor = self.cnx.cursor()

    def post_chart(self, song):
        self.reconn()
        notehash = sha256(str(song.tmb["notes"]).encode()).hexdigest()

        add_song = ("INSERT INTO charts "
                    "(noteHash, trackRef, creator, creatorname, songdata, download, video) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        data_song = (notehash, song.tmb["trackRef"], song.creator_id, song.creator, str(song.tmb), song.download, song.video)

        self.cursor.execute(add_song, data_song)
        self.cnx.commit()

    def check_trackref(self, trackref:str()):
        self.reconn()
        if not globals.settings.verification.unique_trackref:
            return True
        self.cursor.execute(f"SELECT trackRef FROM {globals.settings.mysql.database}.{globals.settings.mysql.table}")
        refs = self.cursor.fetchall()
        for r in refs:
            if trackref.strip() == r[0].strip():
                return
        return True

    def reconn(self):
        if not self.cnx.is_connected():
            self.cnx.reconnect(attempts=1, delay=0)
        return