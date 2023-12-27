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

    def check_trackref(self, trackref:str(), user):
        self.reconn()
        if not globals.settings.verification.unique_trackref:
            return True
        self.cursor.execute(f"SELECT SongID, trackRef, creator FROM {globals.settings.mysql.database}.{globals.settings.mysql.table}")
        refs = self.cursor.fetchall()
        for song_id, ref, creator in refs:
            if not trackref == ref:
                continue
            if creator == user:
                return True, song_id
            return False, song_id
        return True, None
    
    def update_row(self, song, song_id):
        self.reconn()
        notehash = sha256(str(song.tmb["notes"]).encode()).hexdigest()
        sql = f"UPDATE tc_charts.charts SET noteHash = %s, trackRef = %s, creator = %s, creatorname = %s, songdata = %s, download = %s, video = %s WHERE SongID = %s"
        data_song = (notehash, song.tmb["trackRef"], song.creator_id, song.creator, str(song.tmb), song.download, song.video, song_id)
        self.cursor.execute(sql, data_song)
        self.cnx.commit()
    
    def set_owner(self, track_ref, username, user_id):
        self.reconn()
        self.cursor.execute(f"SELECT trackRef FROM {globals.settings.mysql.database}.{globals.settings.mysql.table} WHERE trackRef = '{track_ref}'")
        if not self.cursor.fetchone():
            return False
        sql = f"UPDATE {globals.settings.mysql.database}.{globals.settings.mysql.table} SET creator = %s, creatorname = %s WHERE trackRef = %s"
        val = (user_id, username, track_ref)
        self.cursor.execute(sql, val)
        self.cnx.commit()
        return True

    def reconn(self):
        if not self.cnx.is_connected():
            self.cnx.reconnect(attempts=1, delay=0)
        return