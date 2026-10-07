
import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path

# define CTE to map plate appearance result codes to stat groupings
SOURCE_CTE = """
WITH TotalPA as (
    SELECT
        COUNT(*) AS Num_PA,
        player_id,
        player_name
    FROM play
    WHERE pa_result_code NOT LIKE '%(BR)'
    GROUP BY player_id, player_name
), source AS (
    SELECT
        *,
        date(
            substr(date, -4) || '-' ||
            CASE
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'January %' THEN '01'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'February %' THEN '02'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'March %' THEN '03'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'April %' THEN '04'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'May %' THEN '05'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'June %' THEN '06'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'July %' THEN '07'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'August %' THEN '08'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'September %' THEN '09'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'October %' THEN '10'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'November %' THEN '11'
                WHEN substr(date, instr(date, ' ') + 1) LIKE 'December %' THEN '12'
            END || '-' ||
            printf(
                '%02d',
                CAST(
                    substr(
                        substr(date, instr(date, ' ') + 1),
                        instr(substr(date, instr(date, ' ') + 1), ' ') + 1,
                        length(substr(date, instr(date, ' ') + 1))
                        - instr(substr(date, instr(date, ' ') + 1), ' ')
                        - 5
                    ) AS INTEGER
                )
            )
        ) AS timestamp,
        CAST(substr(duration, 1, instr(duration, ':') - 1) AS INTEGER) * 60
         + CAST(substr(duration, instr(duration, ':') + 1) AS INTEGER)
        AS duration_minutes,
        CAST(substr(score, 1, instr(score, '-') - 1) AS INTEGER) AS runs_scored,
        CAST(substr(score, instr(score, '-') + 1) AS INTEGER) AS runs_allowed,

        CASE
            WHEN pa_result_code NOT LIKE '%(BR)'
            THEN 1 ELSE 0
        END AS pa,
        CASE
            WHEN pa_result_code NOT LIKE '%(BR)' AND pa_result_code NOT IN ('BB', 'IBB', 'HBP', 'SH', 'SF', 'CI', 'XI')
            THEN 1 ELSE 0
        END AS ab,
        COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'R', '')), 0
        ) AS num_rbi,
        COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O', '')), 0
        ) AS num_outs,
        CASE
            WHEN pa_result_code IN ('1B', '1B BA', '2B', '3B', 'HR', 'BB', 'IBB', 'HBP')
            THEN 1 ELSE 0
        END AS on_base,
        CASE
            WHEN pa_result_code NOT LIKE '%(BR)' AND pa_result_code NOT IN ('SH', 'CI', 'XI')
            THEN 1 ELSE 0
        END AS on_base_opportunity,
        CASE
            WHEN pa_result_code IN ('1B', '1B BA', '2B', '3B', 'HR')
            THEN 1 ELSE 0
        END AS hits,
        CASE
            WHEN pa_result_code IN ('1B', '1B BA') THEN 1
            WHEN pa_result_code = '2B' THEN 2
            WHEN pa_result_code = '3B' THEN 3
            WHEN pa_result_code = 'HR' THEN 4
            ELSE 0
        END AS total_hit_bases,

        CASE WHEN pa_result_code LIKE '1B%' THEN 1 ELSE 0 END AS singles,
        CASE WHEN pa_result_code = '2B' THEN 1 ELSE 0 END AS doubles,
        CASE WHEN pa_result_code = '3B' THEN 1 ELSE 0 END AS triples,
        CASE WHEN pa_result_code = 'HR' THEN 1 ELSE 0 END AS home_runs,
        CASE WHEN pa_result_code IN ('2B', '3B', 'HR') THEN 1 ELSE 0 END AS xbh,

        CASE WHEN pa_result_code IN ('BB', 'IBB') THEN 1 ELSE 0 END AS walks,
        CASE WHEN pa_result_code = 'IBB' THEN 1 ELSE 0 END AS intentional_walks,
        CASE WHEN pa_result_code IN ('Ku', 'Ks', 'Ki', 'Ks BA') THEN 1 ELSE 0 END AS strikeouts,
        CASE WHEN pa_result_code = 'Ki' THEN 1 ELSE 0 END AS strikeouts_looking,
        CASE WHEN pa_result_code LIKE 'Ks%' THEN 1 ELSE 0 END AS strikeouts_swinging,

        CASE WHEN pa_result_code IN ('FO', 'SF') THEN 1 ELSE 0 END AS flyouts,
        CASE WHEN pa_result_code IN ('GO', 'GO GiDP') THEN 1 ELSE 0 END AS groundouts,
        CASE WHEN pa_result_code IN ('PO', 'PO PiDP', 'PO BA') THEN 1 ELSE 0 END AS popouts,
        CASE WHEN pa_result_code = 'LO' THEN 1 ELSE 0 END AS lineouts,

        CASE WHEN pa_result_code IN ('E', 'CI') THEN 1 ELSE 0 END AS errors_reached,
        CASE WHEN COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O', '')), 0
        ) = 1 THEN 1 ELSE 0 END AS single_plays,
        CASE WHEN COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O', '')), 0
        ) = 2 THEN 1 ELSE 0 END AS double_plays,
        CASE WHEN COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O', '')), 0
        ) = 3 THEN 1 ELSE 0 END AS triple_plays,
        CASE WHEN COALESCE(
            LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O', '')), 0
        ) > 0 THEN 1 ELSE 0 END AS out_results,

        CASE WHEN pa_result_code = 'HBP' THEN 1 ELSE 0 END AS hbp,
        CASE WHEN pa_result_code LIKE '%BA' OR pa_result_code = 'SH' THEN 1 ELSE 0 END AS bunt_attempts,
        CASE WHEN pa_result_code = '1B BA' THEN 1 ELSE 0 END AS bunts_reached,
        CASE WHEN pa_result_code IN ('SF', 'SH') THEN 1 ELSE 0 END AS sacrifices,

        COALESCE(pitches_seen, 0) AS pitches

    FROM play
)
"""


# "Metric Name": ("numerator", "denominator")
METRICS = {
    "PA": ("pa", None),
    "AB": ("ab", None),
    "H": ("hits", None),
    "AVG": ("hits", "ab"),
    "OBP": ("on_base", "on_base_opportunity"),
    "SLG": ("total_hit_bases", "ab"),
    "OPS": ("ops", None),

    "Num_RBI": ("num_rbi", None),
    "RBI_Rate": ("num_rbi", "pa"),
    "Num_OutsGenerated": ("num_outs", None),
    "Avg_OutsGenerated": ("num_outs", "pa"),

    "Num_Singles": ("singles", None),
    "Single_Rate": ("singles", "ab"),
    "Num_Doubles": ("doubles", None),
    "Double_Rate": ("doubles", "ab"),
    "Num_Triples": ("triples", None),
    "Triple_Rate": ("triples", "ab"),
    "Num_HomeRuns": ("home_runs", None),
    "HomeRun_Rate": ("home_runs", "ab"),
    "Num_XBH": ("xbh", None),
    "XBH_Rate": ("xbh", "ab"),

    "Num_Walks": ("walks", None),
    "Walk_Rate": ("walks", "pa"),
    "Num_IntentionalWalks": ("intentional_walks", None),
    "IntentionalWalk_Rate": ("intentional_walks", "pa"),

    "Num_Strikeouts": ("strikeouts", None),
    "Strikeout_Rate": ("strikeouts", "ab"),
    "Num_StrikeoutsLooking": ("strikeouts_looking", None),
    "StrikeoutsLooking_Rate": ("strikeouts_looking", "strikeouts"),
    "Num_StrikeoutSwinging": ("strikeouts_swinging", None),
    "StrikeoutsSwinging_Rate": ("strikeouts_swinging", "strikeouts"),

    "Num_Flyouts": ("flyouts", None),
    "Flyout_Rate": ("flyouts", "pa"),
    "Num_Groundouts": ("groundouts", None),
    "Groundout_Rate": ("groundouts", "ab"),
    "Num_Popouts": ("popouts", None),
    "Popout_Rate": ("popouts", "ab"),
    "Num_Lineouts": ("lineouts", None),
    "Lineout_Rate": ("lineouts", "ab"),

    "Num_ErrorsReached": ("errors_reached", None),
    "ErrorsReached_Rate": ("errors_reached", "ab"),

    "Num_SinglePlays": ("single_plays", None),
    "SinglePlay_Rate": ("single_plays", "ab"),
    "Num_DoublePlays": ("double_plays", None),
    "DoublePlay_Rate": ("double_plays", "ab"),
    "Num_TriplePlays": ("triple_plays", None),
    "TriplePlay_Rate": ("triple_plays", "ab"),
    "Num_OutResults": ("out_results", None),
    "OutResult_Rate": ("out_results", "pa"),

    "Num_HBP": ("hbp", None),
    "HBP_Rate": ("hbp", "pa"),
    "Num_BuntAttempts": ("bunt_attempts", None),
    "BuntAttempt_Rate": ("bunt_attempts", "pa"),
    "Num_BuntsReached": ("bunts_reached", None),
    "BuntsReached_Rate": ("bunts_reached", "ab"),
    "Num_Sacrifices": ("sacrifices", None),
    "Sacrifice_Rate": ("sacrifices", "pa"),

    "Num_PitchesSeen": ("pitches", None),
    "Avg_PitchesSeen": ("pitches", "pa"),
}



# List of qualifier groups
# {
#   "nickname": ("clause", "complexity"),
#   ...
# }
QUALIFIERS = [
    {
        "at all game start times": ("1=1", 0),
        "in day games": ("game_type LIKE 'Day Game%'", 5),
        "in night games": ("game_type LIKE 'Night Game%'", 5)
    },
    {
        "anywhere": ("1=1", 0),
        "at home": ("player_team = home_team", 4),
        "when away": ("player_team = away_team", 4)
    },
    {
        "with any runner situation": ("1=1", 0),
        "with bases empty": ("runners_on_base = '---'", 4),
        "with RISP": ("runners_on_base LIKE '%2' OR runners_on_base LIKE '%3'", 4),
        "with bases loaded": ("runners_on_base = '123'", 4)
    },
    {
        "with any count": ("1=1", 0),
        "on first pitch": ("pitches_seen = 1", 4),
        "on two strikes": ("count LIKE '%-2'", 4),
        "on a full count": ("count = '3-2'", 4)
    },
    {
        "on any surface": ("1=1", 0),
        "on grass": ("game_type LIKE '%me on grass'", 7),
        "on turf": ("game_type LIKE '%me on artificial turf'", 7)
    },
    {
        "with any crowd": ("1=1", 0), # <20k, [20k-30k), >30k make a roughly 3-way split
        "to small crowds (< 20k)": ("attendance > 0 AND attendance < 20000", 11), # "> 0" since 4 games lack attendance data and fallback to 0
        "to median-sized crowds (20k-30k)": ("attendance >= 20000 AND attendance < 30000", 11),
        "to large crowds (> 30k)": ("attendance >= 30000", 11)
    },
    {
        "on any day of the week": ("1=1", 0),
        "on weekdays": ("date NOT LIKE 'Saturday%' AND date NOT LIKE 'Sunday%'", 5),
        "on weekends": ("date LIKE 'Saturday%' OR date LIKE 'Sunday%'", 5)
    },
    {
        "in any inning": ("1=1", 0),
        "in regulation innings": ("CAST(SUBSTR(inning, 2) AS INTEGER) <= 9", 5),
        "in extra innings": ("CAST(SUBSTR(inning, 2) AS INTEGER) > 9", 5)
    },
    {
        "with any outs": ("1=1", 0),
        "with no outs": ("outs = 0", 4),
        "with one out": ("outs = 1", 4),
        "with two outs": ("outs = 2", 4)
    },
    {
        "throughout the year": ("1=1", 0),
        "before the all star break": ("timestamp < '2026-07-12'", 4),
        "after the all star break": ("timestamp > '2026-07-12'", 4)
    },
    {
        "in any game duration": ("1=1", 0), # <160, 160-180, 180+ make a roughly 3-way split
        "in quick games (<2:40)": ("duration_minutes < 160", 11),
        "in average length games (2:40-3:00)": ("duration_minutes >= 160 AND duration_minutes < 180", 11),
        "in long games (3:00+)": ("duration_minutes >= 180", 11)
    },
    {
        "at any position": ("1=1", 0),
        "among infielders": ("position LIKE '%First Baseman%' OR position LIKE '%Second Baseman%' OR position LIKE '%Third Baseman%' OR position LIKE '%Shortstop%'", 5),
        "among outfielders": ("position LIKE '%Leftfielder%' OR position LIKE '%Centerfielder%' OR position LIKE '%Rightfielder%' OR position LIKE '%Outfielder%'", 5),
        "among pitchers": ("position LIKE '%Pitcher%'", 5),
        "among catchers": ("position LIKE '%Catcher%'", 5),
        "among designated hitters": ("position LIKE '%Designated Hitter%'", 5),
        "among pinch hitters": ("position LIKE '%Pinch Hitter%'", 5)
    },
    {
        "with any score": ("1=1", 0),
        "with a lead": ("runs_scored > runs_allowed", 5),
        "in a run deficit": ("runs_scored < runs_allowed", 5),
        "in a tied game": ("runs_scored = runs_allowed", 5),
        "before the opponent has scored": ("runs_allowed = 0", 5),
        "when slaughtering (8+ runs)": ("runs_scored >= runs_allowed + 8", 5)
    },
    {
        "from any side of the plate": ("1=1", 0),
        "among left-handed batters": ("bats = 'Left'", 5),
        "among right-handed batters": ("bats = 'Right'", 5),
        "among switch-hitters": ("bats = 'Both'", 5)
    },
    {
        "when born anywhere": ("1=1", 0),
        "among American-born players": ("birthplace LIKE '% us'", 5),
        "among foreign-born players": ("birthplace NOT LIKE '% us'", 5)
    },
    {
        "among players with any height": ("1=1", 0),
        "among tall players (at least 6')": ("height >= 72", 11),
        "among short kings (under 6')": ("height < 72", 11)
    },
    {
        "among all star signs": ("1=1", 0),
        "among Aries": ("strftime('%m-%d', player.dob) BETWEEN '03-21' AND '04-19'", 7),
        "among Tauruses": ("strftime('%m-%d', player.dob) BETWEEN '04-20' AND '05-20'", 7),
        "among Geminis": ("strftime('%m-%d', player.dob) BETWEEN '05-21' AND '06-20'", 7),
        "among Cancers": ("strftime('%m-%d', player.dob) BETWEEN '06-21' AND '07-22'", 7),
        "among Leos": ("strftime('%m-%d', player.dob) BETWEEN '07-23' AND '08-22'", 7),
        "among Virgos": ("strftime('%m-%d', player.dob) BETWEEN '08-23' AND '09-22'", 7),
        "among Libras": ("strftime('%m-%d', player.dob) BETWEEN '09-23' AND '10-22'", 7),
        "among Scorpios": ("strftime('%m-%d', player.dob) BETWEEN '10-23' AND '11-21'", 7),
        "among Sagittariuses": ("strftime('%m-%d', player.dob) BETWEEN '11-22' AND '12-21'", 7),
        "among Capricorns": ("(strftime('%m-%d', player.dob) >= '12-22' OR strftime('%m-%d', player.dob) <= '01-19')", 7),
        "among Aquariuses": ("strftime('%m-%d', player.dob) BETWEEN '01-20' AND '02-18'", 7),
        "among Pisces": ("strftime('%m-%d', player.dob) BETWEEN '02-19' AND '03-20'", 7)
    }
]

situational_qualifier_groups = [
    "at all game start times",
    "anywhere",
    "with any runner situation",
    "with any count",
    "on any surface",
    "with any crowd",
    "on any day of the week",
    "in any inning",
    "with any outs",
    "throughout the year",
    "in any game duration",
    "with any score",
]

# for each qualifier group, if the first option is present in situational_qualifier_groups, then the entire group is situational. 
# This is used to determine whether a given leaderboard row is situational or not.
# create list of all situational phrases from situational_qualifier_groups
situational_groups = [group for group in QUALIFIERS if list(group.keys())[0] in situational_qualifier_groups]
situational_phrases = [phrase for group in situational_groups for phrase in group.keys()]
# situational_phrases = [phrase for phrase in situational_qualifier_groups if phrase in [option for group in qualifier_groups for option in group]]

#
# Create query
#

MIN_PA = 340 # Baseball Savant defines "Qualified" hitter as 2.1 PA per team game, which is 2.1 * 162 = 340.2 PA in a season.

base_query = SOURCE_CTE + """
SELECT
\tsource.player_id,
\tsource.player_name,
"""

columns = []
for metric_name, (numerator, denominator) in METRICS.items():
    if metric_name == "OPS":
        columns.append("\tSUM(on_base) * 1.0 / SUM(on_base_opportunity) + SUM(total_hit_bases) * 1.0 / SUM(ab) AS OPS")
    elif denominator is None:
        columns.append(f"\tSUM({numerator}) AS {metric_name}")
    else:
        columns.append(f"\tSUM({numerator}) * 1.0 / SUM({denominator}) AS {metric_name}")

base_query += ",\n".join(columns) + f""",
\tMAX(player.bats) AS bats,
\tMAX(player.birthplace) AS birthplace,
\tMAX(player.height) AS height,
\tMAX(player.position) AS position,
\tplayer.dob AS dob
FROM source
LEFT JOIN player ON source.player_id = player.player_id
INNER JOIN TotalPA ON source.player_id = TotalPA.player_id
WHERE 1=1 AND TotalPA.Num_PA >= {MIN_PA}
""" 


interesting_min_metrics = [
    "Avg_OutsGenerated",
    "Strikeout_Rate",
    "StrikeoutsLooking_Rate",
    "StrikeoutsSwinging_Rate",
    "Groundout_Rate",
    "OutResult_Rate",
    "Avg_PitchesSeen"
]

# add WHERE clauses
# build queries out of every combination of qualifiers, always taking exactly 1 from each grouping.
# a query's complexity is equal to the sum of the "complexity" values from each qualifier's tuple.
# iteratively build and run queries with higher and higher complexities, 
# until we find a statistic for each player in the play table in which they are the leader
# add "GROUP BY player_id, player_name" to the end of each query before executing.

# after each query is executed, capture 
# 1. The player id, player name, and player team of the single leader in each metric (if there are multiple leaders tied with the same metric value, then consider none of them leaders; leaders must be on their own for a given metric)
#    The leader is simply the MAX value holder of each metric column. 
#    For "interesting_min_metrics" metrics, also find the MIN value record holder (if there is a single winner: no ties). There may be a separate MAX leader and MIN leader.
# 2. The combined phrase for that query
#    Ignore qualifiers with the clause "1=1" from the combined phrase, and join the remaining complexity 1+ qualifiers phrases with a ", " between each
#    For example, "Highest Num_PitchesSeen in day games, at home" or "Lowest OutsGenerated_Rate on a full count"
# 3. The summed "complexity" value of the query
# 4. The combined SQL query that found that result

# capture these values into a CSV in this directory named "leaderboard.csv"


# Group qualifiers by their complexity within each qualifier dictionary.
qualifiers_by_complexity = []

for group in QUALIFIERS:
    grouped = defaultdict(list)

    for phrase, (clause, complexity) in group.items():
        grouped[complexity].append(
            (phrase, clause, complexity)
        )

    qualifiers_by_complexity.append(grouped)

def generate_combinations_at_complexity(target_complexity):
    combination = [None] * len(QUALIFIERS)

    def recurse(group_index, current_complexity):
        if group_index == len(QUALIFIERS):
            if current_complexity == target_complexity:
                phrases = []
                clauses = []

                for phrase, clause, complexity in combination:
                    clauses.append(clause)

                    if clause != "1=1":
                        phrases.append(phrase)

                yield {
                    "phrases": phrases,
                    "clauses": clauses,
                    "complexity": current_complexity,
                }
            return

        for phrase, (clause, complexity) in QUALIFIERS[group_index].items():
            new_complexity = current_complexity + complexity

            if new_complexity > target_complexity:
                continue

            combination[group_index] = (phrase, clause, complexity)

            yield from recurse(
                group_index + 1,
                new_complexity
            )

    yield from recurse(0, 0)

# ------------------------------------------------------------

import csv
import itertools

DB_PATH = "mlb.db"


# 
# Determine the complete list of players.
#

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    cursor.execute(f"""
        WITH TotalPA AS (
            SELECT
                player_id,
                COUNT(*) AS num_pa
            FROM play
            WHERE pa_result_code NOT LIKE '%(BR)'
            GROUP BY player_id
        )
        SELECT
            player.player_id,
            player.player_name
        FROM player
        INNER JOIN TotalPA ON player.player_id = TotalPA.player_id
        WHERE TotalPA.num_pa >= {MIN_PA}
        ORDER BY player.player_id
    """)

    all_players = {
        row[0]: {
            "player_id": row[0],
            "player_name": row[1]
        }
        for row in cursor.fetchall()
    }


print(f"Found {len(all_players)} players. Starting query execution...")
print()


# ------------------------------------------------------------
# Init values for iterative search
# ------------------------------------------------------------

# For search
players_found = set()
leaderboard_rows = []
recorded_results = set()
metric_names = list(METRICS.keys())

# For progress updates
last_player_milestone = 0
player_milestone_step = 5 # 5% more players
last_combination_milestone = 0
combination_milestone_step = 500 # 500 combinations

# ------------------------------------------------------------
# Execute combinations in increasing complexity order.
# ------------------------------------------------------------

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row

    combination_number = 0

    for complexity in range(
        sum(max(grouped.keys()) for grouped in qualifiers_by_complexity) + 1
    ):
        if len(players_found) == len(all_players):
            print("All players have been found as a unique leader. Stopping search.")
            break
            
        print(f"Starting complexity {complexity}. {len(players_found)} of {len(all_players)} players found.")

        for combination in generate_combinations_at_complexity(complexity):
            combination_number += 1

            # Stop as soon as every player has been found.
            if len(players_found) == len(all_players):
                print()
                print(
                    "All players have been found as a unique leader. "
                    "Stopping search."
                )
                break

            # Build the WHERE clause.
            query = base_query

            for clause in combination["clauses"]:
                if clause != "1=1":
                    query += f"AND ({clause})\n"

            # GROUP BY player
            query += """
    GROUP BY
        source.player_id,
        source.player_name,
        player.dob
    """

            # Execute query.
            try:
                cursor = conn.execute(query)
                rows = cursor.fetchall()

            except sqlite3.Error as error:
                print(
                    f"SQL error at combination "
                    f"{combination_number}: {error}"
                )
                print(query)
                print()
                continue

            # No players met this combination's qualifiers.
            if not rows:
                continue

            results = [dict(row) for row in rows]

            # Create the human-readable qualifier phrase.
            if combination["phrases"]:
                qualifier_phrase = ", ".join(
                    combination["phrases"]
                )
                is_situational = any(
                    phrase in situational_phrases
                    for phrase in combination["phrases"]
                )
            else:
                qualifier_phrase = ""
                is_situational = False

            # ------------------------------------------------------------
            # Find leaders for all metrics in a single pass through results
            # ------------------------------------------------------------

            # For each metric, track:
            #   - max value
            #   - rows tied for max
            #   - min value (only for interesting_min_metrics)
            #   - rows tied for min
            #
            # This avoids scanning `results` once for every metric.

            metric_stats = {
                metric_name: {
                    "max_value": None,
                    "max_leaders": [],
                    "min_value": None,
                    "min_leaders": [],
                }
                for metric_name in metric_names
                if metric_name not in ["PA", "AB"]
            }

            # One pass through every player returned by this query.
            for row in results:

                for metric_name, stats in metric_stats.items():

                    value = row[metric_name]

                    # Ignore NULL metric values.
                    if value is None:
                        continue

                    # ----------------------------------------------------
                    # MAX
                    # ----------------------------------------------------

                    if (
                        stats["max_value"] is None
                        or value > stats["max_value"]
                    ):
                        stats["max_value"] = value
                        stats["max_leaders"] = [row]

                    elif value == stats["max_value"]:
                        stats["max_leaders"].append(row)

                    # ----------------------------------------------------
                    # MIN
                    # Only calculate this for interesting_min_metrics.
                    # ----------------------------------------------------

                    if metric_name in interesting_min_metrics:

                        if (
                            stats["min_value"] is None
                            or value < stats["min_value"]
                        ):
                            stats["min_value"] = value
                            stats["min_leaders"] = [row]

                        elif value == stats["min_value"]:
                            stats["min_leaders"].append(row)

            # ------------------------------------------------------------
            # Process the leaders found above.
            # No additional scan through `results` is necessary.
            # ------------------------------------------------------------

            for metric_name, stats in metric_stats.items():

                # --------------------------------------------------------
                # Unique MAX leader
                # --------------------------------------------------------

                if len(stats["max_leaders"]) == 1:

                    leader = stats["max_leaders"][0]
                    max_value = stats["max_value"]

                    result_key = (
                        leader["player_id"],
                        "MAX",
                        metric_name,
                        combination["complexity"],
                        qualifier_phrase,
                    )

                    if result_key not in recorded_results:

                        recorded_results.add(result_key)

                        if qualifier_phrase:
                            description = (
                                f"Highest {metric_name} "
                                f"{qualifier_phrase}"
                            )
                        else:
                            description = (
                                f"Highest {metric_name}"
                            )

                        leaderboard_rows.append({
                            "player_id": leader["player_id"],
                            "player_name": leader["player_name"],
                            "metric": metric_name,
                            "direction": "Highest",
                            "value": max_value,
                            "description": description,
                            "complexity": combination["complexity"],
                            "plate_appearances": leader.get("PA", 0),
                            "at_bats": leader.get("AB", 0),
                            "is_situational": is_situational
                        })

                        players_found.add(
                            leader["player_id"]
                        )

                # --------------------------------------------------------
                # Unique MIN leader
                # --------------------------------------------------------

                if (
                    metric_name in interesting_min_metrics
                    and len(stats["min_leaders"]) == 1
                ):

                    leader = stats["min_leaders"][0]
                    min_value = stats["min_value"]

                    result_key = (
                        leader["player_id"],
                        "MIN",
                        metric_name,
                        combination["complexity"],
                        qualifier_phrase,
                    )

                    if result_key not in recorded_results:

                        recorded_results.add(result_key)

                        if qualifier_phrase:
                            description = (
                                f"Lowest {metric_name} "
                                f"{qualifier_phrase}"
                            )
                        else:
                            description = (
                                f"Lowest {metric_name}"
                            )

                        leaderboard_rows.append({
                            "player_id": leader["player_id"],
                            "player_name": leader["player_name"],
                            "metric": metric_name,
                            "direction": "Lowest",
                            "value": min_value,
                            "description": description,
                            "complexity": combination["complexity"],
                            "plate_appearances": leader.get("PA", 0),
                            "at_bats": leader.get("AB", 0),
                            "is_situational": is_situational
                        })

                        players_found.add(
                            leader["player_id"]
                        )

# commit records to file
output_path = Path("leaderboard.csv")

with output_path.open(
    "w",
    newline="",
    encoding="utf-8"
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "player_id",
            "player_name",
            "metric",
            "direction",
            "value",
            "description",
            "complexity",
            "plate_appearances",
            "at_bats",
            "is_situational"
        ]
    )

    writer.writeheader()

    # Sort primarily by complexity, then player name,
    # then metric so the CSV is easy to inspect.
    leaderboard_rows.sort(
        key=lambda row: (
            row["complexity"],
            row["player_name"],
            row["metric"],
            row["direction"],
        )
    )

    writer.writerows(leaderboard_rows)


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

missing_players = set(all_players) - players_found

print()
print("=" * 70)
print("Leaderboard search complete")
print("=" * 70)
print(
    f"Players found: "
    f"{len(players_found)}/{len(all_players)}"
)
print(
    f"Unique leadership results: "
    f"{len(leaderboard_rows)}"
)
print(f"CSV: {output_path.resolve()}")


if missing_players:

    print()
    print(
        f"{len(missing_players)} players did not receive "
        f"a unique leadership result:"
    )

    for player_id in sorted(missing_players):

        player = all_players[player_id]

        print(
            f"  {player['player_name']} "
            f"({player_id})"
        )