# Map records for UI display.
# Find the lowest complexity record for each player (collect multiple records in case of ties) from leaderboard.csv
# Map the rows from the leaderboard to a JSON structure in an output file to export to the UI

import csv
import json
from collections import defaultdict
import pandas as pd

print("Collecting player metadata...")

# collect list of all players from playermetadata.csv

all_players = {}
player_metadata_df = pd.read_csv("playermetadata.csv", encoding="utf-8")
for _, row in player_metadata_df.iterrows():
    all_players[row["player_id"]] = {
        "player_id": row["player_id"],
        "player_name": row["player_name"],
        "player_team": row["player_team"] if str(row["player_team"]) != "nan" else "",
        "photo_link": row["photo_link"]
    }

print(f"Collected metadata for {len(all_players)} players.")
print("Processing leaderboard records...")

# leaderboard.csv is in order of increasing complexity, so scan from top to bottom, finding the first (or multiple in ties) lowest complexity record for each player.

last_output = None
player_records = defaultdict(list)
leaderboard_df = pd.read_csv("leaderboard.csv", encoding="utf-8")
for _, row in leaderboard_df.iterrows():
    if len(player_records) % 50 == 0 and len(player_records) != last_output:
        last_output = len(player_records)
        print(f"Collected records for {len(player_records)} of {len(all_players)} players...")

    player_id = row["player_id"]
    if not player_records[player_id]:
        player_records[player_id].append(row.to_dict())
    elif row["complexity"] == player_records[player_id][0]["complexity"]:
        player_records[player_id].append(row.to_dict())
    else:
        continue

print(f"Collected lowest complexity records for {len(player_records)} players.")
print("Mapping records to JSON structure for the UI...")

# Map the records to a JSON structure for the UI
output_data = {}
for player_id, records in player_records.items():
    output_data[player_id] = {
        "player_info": all_players.get(player_id, {}),
        "records": records
    }

with open("playerrecords.json", "w") as f:
    json.dump(output_data, f, indent=4)

print("Finished writing player records to playerrecords.json.")
