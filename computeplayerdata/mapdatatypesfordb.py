# for each player file and each play in the file, map the play description to the shorthand code
# also map the dates and times to timestamps and attendance to int

import os
import pandas as pd
import re

play_description_map = {
    # ab (hit)
    r'^Single.+(?!Bunt)': '1B',
    r'^Single\s\((Fly\sBall|Line\sDrive|Ground\sBall).*\)': '1B',
    'Double Play: Single to': '1B HiDP',
    'Double to': '2B',
    r'^Double\s\((Fly\sBall|Line\sDrive|Ground\sBall).*\)': '2B',
    'Triple to': '3B',
    'Home Run': 'HR',
    'Ground-rule Double': '2B',
    r'Single to .+Bunt': '1B BA',

    # ab (not hit)
    'Fielder\'s Choice': 'FC',
    r'.*Strikeout Swinging.*': 'Ks', # strikeout "swinging"
    r'.*Strikeout Looking.*': 'Ki', # strikeout with "eye"
    'Groundout:': 'GO',
    'Ground Ball Double Play:': 'GO GiDP',
    r'Flyball: .+(?!Sacrifice Fly)': 'FO',
    r'Popfly: .+(?!Sacrifice)': 'PO',
    r'Lineout: .+(?!Sacrifice)': 'LO',
    r'Reached on E\d': 'E',
    'Double Play: Popfly:': 'PO PiDP',
    'Strikeout': 'Ku', # strikeout ("unspecified")
    'Bunt Popfly:': 'PO BA', # pop out / bunt attempt
    'Interference by Batter': 'BI',
    'Strikeout (foul bunt)': 'Ks BA', # strikeout swinging, bunt attempt

    # non-ab
    'Walk': 'BB',
    'Intentional Walk': 'IBB',
    r'Flyball: .+Sacrifice Fly': 'SF',
    r'Bunt Groundout:.+Sacrifice': 'SH',
    'Hit By Pitch': 'HBP',
    'Reached on Interference on C': 'CI',

    # non-pa (baserunning)
    r'.+Caught Stealing': 'CS (BR)',
    'Wild Pitch': 'WP (BR)',
    r'\sSteals\s': 'SB (BR)',
    r'\sPicked off\s': 'PK (BR)',
    'Balk': 'BK (BR)',
    'Defensive Indifference': 'DI (BR)',
    'Passed Ball': 'PB (BR)',
    r'E\d+ on Foul Ball': 'E (BR)',
    r'Baserunner Advance;.*Adv\son\sE\d+': 'E (BR)',
    'Baserunner Out Advancing': 'O (BR)',
    r'Baserunner Advance;.*Obstruction': 'OBS (BR)'
}

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
            print(f'Mapping file {files_processed} of {file_count} ({pct}%)')
        
        print(f'Mapping file {files_processed} of {file_count} ({pct}%): {player_file}')
        
        # Read the player data CSV into a DataFrame
        df = pd.read_csv(player_file_path, encoding='utf-8')
        
        # Map play descriptions to shorthand codes
        df['time'] = df['time'].apply(lambda x: x.replace('Start Time: ', '').replace(' Local', ''))
        df['attendance'] = df['attendance'].apply(lambda x: int(str(x).replace('Attendance: ', '')))
        df['venue'] = df['venue'].apply(lambda x: x.replace('Venue: ', ''))
        df['duration'] = df['duration'].apply(lambda x: x.replace('Game Duration: ', ''))
        df['pa_result_code'] = df['pa_result'].apply(lambda x: next((shorthand for desc, shorthand in play_description_map.items() if re.search(desc, str(x))), 'Other'))

        # If no code is found, leave as blank and print a warning
        for index, row in df.iterrows():
            if row['pa_result_code'] == 'Other':
                print(f'Warning: No shorthand code found for play description "{row["pa_result"]}" in player file {player_file_path} and game_id {row["game_id"]}')
        
        # Save the updated DataFrame back to the CSV
        df.to_csv(player_file_path, index=False, encoding='utf-8')