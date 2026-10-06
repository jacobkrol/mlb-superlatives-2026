# upsert each player file content to sqlite db

import os
import pandas as pd
import sqlite3
from pathlib import Path

conn = sqlite3.connect('mlb.db')

# create table if not exists play
sql_script = Path("play.sql").read_text()
conn.executescript(sql_script)

# upsert play data
playerdata_path = 'playerdata'
file_count = sum(1 for entry in os.scandir(playerdata_path) if entry.is_file())
files_processed = 0
last_milestone = 0
milestone_step = 5

for player_file in os.listdir(playerdata_path):
    if player_file.endswith('.csv'):
        files_processed += 1
        player_file_path = os.path.join(playerdata_path, player_file)
        pct = round(files_processed * 1000.0 / (file_count * 1.0)) / 10.0
        if pct - milestone_step > last_milestone:
            last_milestone = pct
            print(f'Upserting file {files_processed} of {file_count} ({pct}%)')
        
        # Read the player data CSV into a DataFrame
        df = pd.read_csv(player_file_path, encoding='utf-8')

        df.to_sql('temp_play', conn, if_exists='replace', index=False)
        
        upsert_script = '''
            INSERT INTO play (play_id, player_id, player_name, game_id, away_team, home_team, date, time, attendance, venue, duration, game_type, defensive_positions, inning, score, outs, runners_on_base, pitches_seen, count, runs_outs, player_team, pitcher, pa_result, pa_result_code)
            SELECT play_id, player_id, player_name, game_id, away_team, home_team, date, time, attendance, venue, duration, game_type, defensive_positions, inning, score, outs, runners_on_base, pitches_seen, count, runs_outs, player_team, pitcher, pa_result, pa_result_code FROM temp_play WHERE true
            ON CONFLICT(play_id) DO UPDATE SET
                player_id = excluded.player_id,
                player_name = excluded.player_name,
                game_id = excluded.game_id,
                away_team = excluded.away_team,
                home_team = excluded.home_team,
                date = excluded.date,
                time = excluded.time,
                attendance = excluded.attendance,
                venue = excluded.venue,
                duration = excluded.duration,
                game_type = excluded.game_type,
                defensive_positions = excluded.defensive_positions,
                inning = excluded.inning,
                score = excluded.score,
                outs = excluded.outs,
                runners_on_base = excluded.runners_on_base,
                pitches_seen = excluded.pitches_seen,
                count = excluded.count,
                runs_outs = excluded.runs_outs,
                player_team = excluded.player_team,
                pitcher = excluded.pitcher,
                pa_result = excluded.pa_result,
                pa_result_code = excluded.pa_result_code
        '''

        cursor = conn.cursor()
        cursor.execute(upsert_script)

        cursor.execute("DROP TABLE temp_play;")

        conn.commit()

# Remove players (and their plays) from the DB if they do not have a qualified number of PA
# Remove baserunning plays from the DB (until we decide to start using them by parsing the runner names from the play description)
reduce_script = '''
DELETE FROM play
WHERE player_id IN (
    WITH x AS (
    SELECT 
        player_id,
        COUNT(*) AS PA
    FROM play
    WHERE pa_result_code NOT LIKE '%(BR)'
    GROUP BY player_id
    ) SELECT player_id FROM x WHERE PA < 25
) OR pa_result_code LIKE '%(BR)'
RETURNING player_id
'''

cursor = conn.cursor()
cursor.execute(reduce_script)
deleted_plays = cursor.fetchall()

print(f"Deleted {len(deleted_plays)} plays (batter with <25 PAs or baserunning-related)")

conn.commit()

conn.close()