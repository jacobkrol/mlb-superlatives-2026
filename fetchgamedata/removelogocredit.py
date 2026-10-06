#for each _meta file in gamedata, remove the last column (data row only, not header row) if it contains "Logos via Sports Logos.net / About logos"
import os

def remove_logo_credit():
    gamedata_path = 'gamedata'

    for filename in os.listdir(gamedata_path)[0:1]:  # Process only the first file
        print(f'Checking file: {filename}')
        if filename.endswith('_meta.csv'):
            file_path = os.path.join(gamedata_path, filename)
            # read file as text. In second row, if last column contains "Logos via Sports Logos.net / About logos", remove it
            with open(file_path, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    second_row = lines[1].strip().split(',')
                    if second_row[-1] == "Logos via Sports Logos.net / About logos":
                        # remove last column
                        second_row = second_row[:-1]
                        lines[1] = ','.join(second_row) + '\n'
                        with open(file_path, 'w') as f:
                            f.writelines(lines)