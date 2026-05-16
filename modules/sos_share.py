"""
RoadSoS — SOS Share Module
Creates shareable emergency links with GPS location.
"""
import sqlite3, json, os, secrets, time
from config import Config

DB = Config.DB_PATH

def _conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS sos_links(
        token TEXT PRIMARY KEY, lat REAL, lon REAL,
        message TEXT, contact TEXT, created_at INTEGER)""")
    c.commit()
    return c

def create_sos_link(lat, lon, message="", contact=""):
    token = secrets.token_urlsafe(8)
    c = _conn()
    c.execute("INSERT INTO sos_links VALUES(?,?,?,?,?,?)",
              (token, lat, lon, message, contact, int(time.time())))
    c.commit(); c.close()
    return token

def get_sos_data(token):
    c = _conn()
    row = c.execute("SELECT * FROM sos_links WHERE token=?", (token,)).fetchone()
    c.close()
    if not row: return None
    return {"token":row[0],"lat":row[1],"lon":row[2],
            "message":row[3],"contact":row[4],"created_at":row[5]}
