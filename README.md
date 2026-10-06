# MLB Superlatives

Everybody's a winner! This project seeks to find a statistic in which every player in the MLB leads the league.

## Getting Started

### Prerequisites

- Python 3
- Node.js

### Data Collection

Fetch game data from baseball reference. (~4 hours)

```
cd fetchgamedata
npm install
node index.js
```

> **IMPORTANT: Make a copy of this new "gamedata" directory**. You will mutate this directory during the compile step, so it's important to have a backup in case the mutation fails.

If you would like to generate records based on player demographics, fetch and process player metadata. (~1.5 hours)

```
node players.js
```

### Data Processing

Transpose game data into player data. (~3 minutes)

```
cd computeplayerdata
py compileplayerdata.py
```

Store the shorthand play scores for each play in the new player data source. (< 1 minute)

```
py mapdatatypesfordb.py
```

Iteratively add new play score mappings as necessary by updating and rerunning `mapdatatypesfordb.py`. This file is idempotent, so feel free to adjust and update piece by piece.

For player demographics, migrate player data as well.

```
py migrateplayermeta.py
```

### Data Analysis

Upsert the data into the DB and find leaders of individual records. (~30 min for 30M qualification combinations and 600 players)

```
cd computeplayerdata
py upserttodb.py
py queryforrecords.py
```

Again, feel free to iteratively add or remove QUALIFIERS, update their complexity, or add or remove METRICS, and then rerun `queryforrecords.py`. Only the output of this script is not idempotent, so it's best to delete the outputted `leaderboard.csv` between subsequent runs to avoid duplicate records being saved.

For player demographic records, upsert those values before querying for records again.

```
py upsertplayermetatodb.py
py queryforrecords.py
```

# Visualizing in UI

Map the leaderboard and player metadata into a json file for the UI to consume. (<1 minute)

```
cd computeplayerdata
py maprecordsforui.py
cp playerrecords.json ../superlativeui/playerrecords.json
```

Then run the UI server and navigate to `http://localhost:3000` in your browser.

```
cd superlativeui
npx serve
```