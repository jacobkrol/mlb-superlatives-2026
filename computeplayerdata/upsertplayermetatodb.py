# upsert player metadata file content to sqlite db

import os
import pandas as pd
import sqlite3
from pathlib import Path

conn = sqlite3.connect('mlb.db')

# create table if not exists player
sql_script = Path("player.sql").read_text()
conn.executescript(sql_script)

# upsert player data
inputfile = "playermetadata.csv"

df = pd.read_csv(inputfile, encoding='utf-8')
df.to_sql('player', conn, if_exists='replace', index=False)

print(f"Upserted player data for {len(df)} players")

conn.commit()

conn.close()