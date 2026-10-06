# read from each ../fetchgamedata/gamedata/:gameid_awaybatting.csv and ../fetchgamedata/gamedata/:gameid_homebatting.csv
# compile into a single CSV file for each player, named after their player id, in ../computeplayerdata/playerdata/:playerid.csv
# if no CSV file exists for a player, create one with the header row (each row in per play per game):
# game_id,away_team,home_team,date,time,attendance,venue,duration,game_type,inning,score,outs,runners_on_base,pitches_seen,count,player_team,pitcher,pa_result
# 
# find player id from "Batting-additional" column in ../fetchgamedata/gamedata/:gameid_awaybatting.csv and ../fetchgamedata/gamedata/:gameid_homebatting.csv.
# find player name from "Batting" column in ../fetchgamedata/gamedata/:gameid_awaybatting.csv and ../fetchgamedata/gamedata/:gameid_homebatting.csv.
# 
# create a map for player name to player id for a given game id from batting files
# for each play in play_by_play, look up the player id and name from the maps
# append a row to the corresponding player CSV file
# away_team,home_team,date,time,attendance,venue,duration,game_type all come from the gameid_meta file
# inning,score,outs,runners_on_base,pitches_seen,count,player_team,pitcher,pa_result all come from the play_by_play file

import os
import pandas as pd
import re
from pathlib import Path

playerdata_path = 'playerdata'

# read from all game files in ../fetchgamedata/gamedata/
def compile_player_data():
    # Define source path
    gamedata_path = '../fetchgamedata/gamedata'

    # Ensure playerdata directory exists
    os.makedirs(playerdata_path, exist_ok=True)

    game_count = sum(1 for entry in os.scandir(gamedata_path) if entry.is_file()) / 4
    games_processed = 0
    last_milestone = 0
    milestone_step = 5

    # Iterate over all game files in the gamedata directory
    for filename in os.listdir(gamedata_path):
        if filename.endswith('_meta.csv'):
            games_processed += 1
            pct = round(games_processed * 1000.0 / (game_count * 1.0)) / 10.0
            if pct - milestone_step > last_milestone:
                last_milestone = pct
                print(f'Processing game {games_processed} of {round(game_count)} ({pct}%)')

            game_id = filename.split('_')[0]
            meta_file = os.path.join(gamedata_path, filename)
            away_batting_file = os.path.join(gamedata_path, f'{game_id}_awaybatting.csv')
            home_batting_file = os.path.join(gamedata_path, f'{game_id}_homebatting.csv')
            play_by_play_file = os.path.join(gamedata_path, f'{game_id}_playbyplay.csv')

            # Read meta data
            # If the string ",Logos via Sports Logos.net / About logos" is present in the file, remove it
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    second_row = lines[1].strip().split(',')
                    if second_row[-1] == "Logos via Sports Logos.net / About logos" \
                        or re.match(r'.*game of doubleheader.*', second_row[-1]) \
                        or second_row[-1].startswith("Game was suspended"):
                        print(f"Removing invalid column text: {second_row[-1]}")
                        second_row = second_row[:-1]
                        lines[1] = ','.join(second_row) + '\n'
                        with open(meta_file, 'w') as f:
                            f.writelines(lines)
                    elif not re.match(r'^(Night|Day)\sGame\son.*', second_row[-1]):
                        print(f"Keeping other column text: {second_row[-1]}")

                    # if attendance column is missing, add an empty column
                    if not second_row[5].startswith("Attendance:"):
                        print(f"Adding missing attendance column. Current value: '{second_row[5]}'")
                        second_row.insert(5, "Attendance: 0")
                        lines[1] = ','.join(second_row) + '\n'
                        print(f"Line will become: {lines[1]}")
                        with open(meta_file, 'w') as f:
                            f.writelines(lines)
                    elif not len(second_row) == 9:
                        print(f"Game file has other incorrect column count: {meta_file}")

            meta_df = pd.read_csv(meta_file, encoding='utf-8')
            away_team = str(meta_df['awayteam'].iloc[0])
            home_team = str(meta_df['hometeam'].iloc[0])
            date = str(meta_df['date'].iloc[0])
            time = str(meta_df['time'].iloc[0])
            attendance = str(meta_df['attendance'].iloc[0])
            venue = str(meta_df['venue'].iloc[0])
            duration = str(meta_df['duration'].iloc[0])
            game_type = str(meta_df['gametype'].iloc[0])

            # Create player maps from batting files
            player_map = {}
            for batting_file in [away_batting_file, home_batting_file]:
                if os.path.exists(batting_file):
                    batting_df = pd.read_csv(batting_file, encoding='utf-8')
                    for _, row in batting_df.iterrows():
                        if str(row['Batting-additional']) == str(-9999):
                            break
                        
                        player_id = str(row['Batting-additional'])
                        batting_string = str(row['Batting'])
                        player_name = batting_string.rsplit(' ', 1)[0]  # Remove the last part (position) to get the player name
                        player_map[player_name] = player_id + ' ' + batting_string.rsplit(' ', 1)[1]  # Store player_id and position(s) together

            # Read play by play data
            if os.path.exists(play_by_play_file):
                play_by_play_df = pd.read_csv(play_by_play_file, encoding='utf-8')
                for _, row in play_by_play_df.iterrows():
                    
                    #if "Inn" doesn't match t1, b1, t2, etc., continue
                    if not re.match(r'^[tb]\d+$', str(row['Inn'])):
                        continue

                    inning = str(row['Inn'])
                    score = str(row['Score'])
                    outs = str(row['Out'])
                    runners_on_base = str(row['RoB'])
                    pitches_seen = str(row['Pit(cnt)']).split('(')[0]  # Extract pitches seen before the '('
                    count = str(row['Pit(cnt)']).split('(')[1].split(')')[0]  # Extract count inside the parentheses
                    runs_outs = str(row['R/O']) if pd.notnull(row['R/O']) else ''
                    player_team = str(row['@Bat'])
                    pitcher = str(row['Pitcher']).replace('\xa0', ' ').strip()  # Replace non-breaking space with regular space and strip whitespace
                    pa_result = str(row['Play Description']).replace('\xa0', ' ').strip()  # Replace non-breaking space with regular space and strip whitespace
                    player_name = str(row['Batter']).replace('\xa0', ' ').strip()  # Replace non-breaking space with regular space and strip whitespace
                    player_id = player_map.get(player_name).split(' ')[0] if player_map.get(player_name) else None
                    defensive_positions = player_map.get(player_name).split(' ')[1] if player_map.get(player_name) else None

                    # custom primary key
                    play_id = game_id + '_' + inning + '_' + player_id + '_' + pitches_seen

                    # append to player CSV file
                    if player_id:
                        player_file = os.path.join(playerdata_path, f'{player_id}.csv')
                        if not os.path.exists(player_file):
                            # Create a new CSV file with header
                            with open(player_file, 'w', encoding='utf-8') as f:
                                f.write('play_id,player_id,player_name,game_id,away_team,home_team,date,time,attendance,venue,duration,game_type,defensive_positions,inning,score,outs,runners_on_base,pitches_seen,count,runs_outs,player_team,pitcher,pa_result,pa_result_code\n')

                        # Append the row to the player's CSV file
                        with open(player_file, 'a', encoding='utf-8') as f:
                            f.write(f'{play_id},{player_id},{player_name},{game_id},{away_team},{home_team},{date},{time},{attendance},{venue},{duration},{game_type},{defensive_positions},{inning},{score},{outs},{runners_on_base},{pitches_seen},{count},{runs_outs},{player_team},{pitcher},{pa_result},\n')
                    else:
                        print(f'Warning: Player name "{player_name}" not found in player map for game {game_id}')


def remove_duplicate_plays():
    """
    Process every CSV in the given directory.
    For duplicate play_id values, keep only the last row.
    Overwrite each CSV with the deduplicated data.
    """
    directory = Path(playerdata_path)
    total_removed = 0

    for csv_file in directory.glob("*.csv"):
        df = pd.read_csv(csv_file)

        if "play_id" not in df.columns:
            continue

        original_count = len(df)

        # Keep the last occurrence of each play_id
        df = df.drop_duplicates(subset="play_id", keep="last")

        # Overwrite the original CSV
        df.to_csv(csv_file, index=False)

        removed_count = original_count - len(df)
        total_removed += removed_count
        if removed_count > 0:
            print(f"{csv_file.name}: removed {removed_count} duplicate rows")

    print(f"Removed {total_removed} total duplicate plays")


def main():
    compile_player_data()
    remove_duplicate_plays()

if __name__ == '__main__':
    main()