# Save player metadata to playermetadata.csv
# Pull source player metadata from ../fetchgamedata/playermetadata.csv
# Create new file in this directory with the same name playermetadata.csv
# Columns of source file are: player_id,player_name,position,handedness,height_weight,dob,debut,contract,jersey_numbers,photo_link
# Columns of output should be: player_id,player_name,position,bats,throws,height,weight,dob,birthplace,debut_date,jersey_numbers,photo_link

import os
import pandas as pd
import re
from pathlib import Path

sourceFile = "../fetchgamedata/playermetadata.csv"
outputFile = "playermetadata.csv"

# create output file with header if not exists
if not os.path.exists(outputFile):
    pd.DataFrame(columns=['player_id', 'player_name', 'player_team', 'position', 'bats', 'throws', 'height', 'weight', 'dob', 'birthplace', 'debut_date', 'jersey_numbers', 'photo_link']).to_csv(outputFile, index=False, encoding='utf-8')

# read each line, and map values to new columns
df = pd.read_csv(sourceFile, encoding='utf-8')
num_players = len(df)
for _, row in df.iterrows():
    player_id = str(row['player_id'])
    player_name = str(row['player_name']).replace('\xa0', ' ')
    position_raw = str(row['position']).replace('\xa0', ' ')
    handedness = str(row['handedness']).replace('\xa0', ' ')
    height_weight = str(row['height_weight']).replace('\xa0', ' ')
    born = str(row['dob']).replace('\xa0', ' ')
    debut = str(row['debut']).replace('\xa0', ' ')
    jersey_numbers = str(row['jersey_numbers'])
    photo_link = str(row['photo_link'])
    player_team_raw = str(row['player_team']).replace('\xa0', ' ')

    # Extra team from player_team_raw
    if 'Team:' in player_team_raw:
        player_team = re.search(r'(?<=Team:\s).+(?=\s\()', player_team_raw).group(0)
    else:
        player_team = None

    # Extra position(s) from position_raw
    position_raw = position_raw.replace("Positions:", "Position:")
    position_text = re.search(r'(?<=Position:\s)([^.]+)', position_raw)
    position_text = position_text.group(1).replace("and","") if position_text else None
    positions = ";".join([pos.strip() for pos in position_raw.split(',')])

    # Extract bats and throws from handedness
    if 'Bats:' in handedness:
        bats = re.search(r'(?<=Bats:\s)(\w+)', handedness).group(1)
    else:
        bats = None

    if 'Throws:' in handedness:
        throws = re.search(r'(?<=Throws:\s)(\w+)', handedness).group(1)
    else:
        throws = None

    # Extract height and weight from height_weight
    # raw height_weight looks like "5-10, 215lb (178cm, 97kg)"
    height_text = height_weight.split(",")[0].strip()
    height = int(height_text.split("-")[0]) * 12 + int(height_text.split("-")[1])
    weight_text = re.search(r'(?<=,\s)\d+(?=lb)', height_weight)
    weight = int(weight_text.group(0)) if weight_text else None

    # Extract dob and birthplace from born
    # born looks like "Born: September 2, 1995 (Age: 31-031d) in Santiago, Dominican Republic do"
    # or "Born: October 3, 2000 (Age: 26-000d) in Alpharetta, GA us"
    if 'Born:' in born:
        dob_text = re.search(r'(?<=Born:\s)(.+)(?=\s\()', born)
        dob = dob_text.group(1) if dob_text else None
        dob = pd.to_datetime(dob) if dob else None
        birthplace_text = re.search(r'(?<=in\s)([^.]+)', born)
        birthplace = birthplace_text.group(1) if birthplace_text else None

    # Extract debut date from debut
    if 'Debut:' in debut:
        debut_date_match = re.search(r'(?<=Debut:\s)(.+)(?=\s\()', debut)
        debut_date = debut_date_match.group(1) if debut_date_match else None
        debut_date = pd.to_datetime(debut_date) if debut_date else None
    else:
        debut_date = None

    # print intermittent progress to user
    if (df.index.get_loc(_)) % 25 == 0:
        print(f"Processed {df.index.get_loc(_)} of {num_players} players ({(df.index.get_loc(_)/num_players)*100:.1f}%)")

    # append row to output file
    pd.DataFrame([{
        'player_id': player_id,
        'player_name': player_name,
        'player_team': player_team,
        'position': position_text,
        'bats': bats,
        'throws': throws,
        'height': height,
        'weight': weight,
        'dob': dob,
        'birthplace': birthplace,
        'debut_date': debut_date,
        'jersey_numbers': jersey_numbers,
        'photo_link': photo_link
    }]).to_csv(outputFile, mode='a', header=False, index=False, encoding='utf-8')