WITH source AS (
SELECT
    *,
    CASE 
        WHEN pa_result_code NOT LIKE '%(BR)' 
        THEN 1 ELSE 0 
    END AS is_pa,
    CASE 
        WHEN pa_result_code NOT LIKE '%(BR)' 
        AND pa_result_code NOT IN ('BB','IBB','HBP','SH','SF','CI') 
        THEN 1 ELSE 0 
    END AS is_ab,
    COALESCE(LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'R','')), 0) AS num_rbi,
    COALESCE(LENGTH(runs_outs) - LENGTH(REPLACE(runs_outs, 'O','')), 0) AS num_outs,
    CASE WHEN pa_result_code IN ('1B','1B BA','2B','3B','HR','BB','IBB','HBP') THEN 1 ELSE 0 END AS is_on_base,
    CASE WHEN pa_result_code IN ('1B','1B BA','2B','3B','HR') THEN 1 ELSE 0 END AS is_hit,
    CASE pa_result_code
        WHEN '1B' OR '1B BA' THEN 1
        WHEN '2B' THEN 2
        WHEN '3B' THEN 3
        WHEN 'HR' THEN 4
        ELSE 0
    END AS total_hit_bases
FROM play
)
SELECT
    player_id,
    player_name,
    SUM(is_pa) AS PA,
    SUM(is_ab) AS AB,
    SUM(is_hit) AS H,
    SUM(is_hit) * 1.0 / SUM(is_ab) AS AVG,
    SUM(is_on_base) * 1.0 / SUM(is_pa) AS OBP,
    SUM(total_hit_bases) * 1.0 / SUM(is_ab) AS SLG,
    SUM(is_on_base) * 1.0 / SUM(is_pa)
        + SUM(total_hit_bases) * 1.0 / SUM(is_ab) AS OPS,
    SUM(num_rbi) AS Num_RBI,
    SUM(num_rbi) * 1.0 / SUM(is_pa) AS RBI_Rate,
    SUM(num_outs) AS Num_OutsGenerated,
    SUM(num_outs) * 1.0 / SUM(is_pa) AS OutsGenerated_Rate,
    SUM(CASE WHEN pa_result_code LIKE '1B%' THEN 1 ELSE 0 END) AS Num_Singles,
    SUM(CASE WHEN pa_result_code LIKE '1B%' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Single_Rate,
    SUM(CASE WHEN pa_result_code = '2B' THEN 1 ELSE 0 END) AS Num_Doubles,
    SUM(CASE WHEN pa_result_code = '2B' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Double_Rate,
    SUM(CASE WHEN pa_result_code = '3B' THEN 1 ELSE 0 END) AS Num_Triples,
    SUM(CASE WHEN pa_result_code = '3B' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Triple_Rate,
    SUM(CASE WHEN pa_result_code = 'HR' THEN 1 ELSE 0 END) AS Num_HomeRuns,
    SUM(CASE WHEN pa_result_code = 'HR' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS HomeRun_Rate,
    SUM(CASE WHEN pa_result_code IN ('2B','3B','HR') THEN 1 ELSE 0 END) AS Num_XHB,
    SUM(CASE WHEN pa_result_code IN ('2B','3B','HR') THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS XBH_Rate,
    SUM(CASE WHEN pa_result_code IN ('BB','IBB') THEN 1 ELSE 0 END) AS Num_Walks,
    SUM(CASE WHEN pa_result_code IN ('BB','IBB') THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS Walk_Rate,
    SUM(CASE WHEN pa_result_code = 'IBB' THEN 1 ELSE 0 END) AS Num_IntentionalWalks,
    SUM(CASE WHEN pa_result_code = 'IBB' THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS IntentionalWalk_Rate,
    SUM(CASE WHEN pa_result_code IN ('Ku','Ks','Ki','Ks BA') THEN 1 ELSE 0 END) AS Num_Strikeouts,
    SUM(CASE WHEN pa_result_code IN ('Ku','Ks','Ki','Ks BA') THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Strikeout_Rate,
    SUM(CASE WHEN pa_result_code = 'Ki' THEN 1 ELSE 0 END) AS Num_StrikeoutsLooking,
    SUM(CASE WHEN pa_result_code = 'Ki' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS StrikeoutsLooking_Rate,
    SUM(CASE WHEN pa_result_code LIKE 'Ks%' THEN 1 ELSE 0 END) AS Num_StrikeoutSwinging,
    SUM(CASE WHEN pa_result_code LIKE 'Ks%' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS StrikeoutsSwinging_Rate,
    SUM(CASE WHEN pa_result_code IN ('FO','SF') THEN 1 ELSE 0 END) AS Num_Flyouts,
    SUM(CASE WHEN pa_result_code IN ('FO','SF') THEN 1 ELSE 0 END) * 1.0 / SUM(CASE WHEN is_ab = 1 OR pa_result_code = 'SF' THEN 1 ELSE 0 END) AS Flyout_Rate, -- Add SF to num and denom
    SUM(CASE WHEN pa_result_code IN ('GO','GO GiDP') THEN 1 ELSE 0 END) AS Num_Groundouts,
    SUM(CASE WHEN pa_result_code IN ('GO','GO GiDP') THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Groundout_Rate,
    SUM(CASE WHEN pa_result_code IN ('PO','PO PiDP','PO BA') THEN 1 ELSE 0 END) AS Num_Popouts,
    SUM(CASE WHEN pa_result_code IN ('PO','PO PiDP','PO BA') THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Popout_Rate,
    SUM(CASE WHEN pa_result_code = 'LO' THEN 1 ELSE 0 END) AS Num_Lineouts,
    SUM(CASE WHEN pa_result_code = 'LO' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS Lineout_Rate,
    SUM(CASE WHEN pa_result_code IN ('E','CI') THEN 1 ELSE 0 END) AS Num_ErrorsReached,
    SUM(CASE WHEN pa_result_code IN ('E','CI') THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS ErrorsReached_Rate,
    SUM(CASE WHEN num_outs = 1 THEN 1 ELSE 0 END) AS Num_SinglePlays,
    SUM(CASE WHEN num_outs = 1 THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS SinglePlay_Rate,
    SUM(CASE WHEN num_outs = 2 THEN 1 ELSE 0 END) AS Num_DoublePlays,
    SUM(CASE WHEN num_outs = 2 THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS DoublePlay_Rate,
    SUM(CASE WHEN num_outs = 3 THEN 1 ELSE 0 END) AS Num_TriplePlays,
    SUM(CASE WHEN num_outs = 3 THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS TriplePlay_Rate,
    SUM(CASE WHEN num_outs > 0 THEN 1 ELSE 0 END) AS Num_OutResults,
    SUM(CASE WHEN num_outs > 0 THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS OutResult_Rate,
    SUM(CASE WHEN pa_result_code = 'HBP' THEN 1 ELSE 0 END) AS Num_HBP,
    SUM(CASE WHEN pa_result_code = 'HBP' THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS HBP_Rate,
    SUM(CASE WHEN pa_result_code LIKE '%BA' OR pa_result_code = 'SH' THEN 1 ELSE 0 END) AS Num_BuntAttempts,
    SUM(CASE WHEN pa_result_code LIKE '%BA' OR pa_result_code = 'SH' THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS BuntAttempt_Rate,
    SUM(CASE WHEN pa_result_code = '1B BA' THEN 1 ELSE 0 END) AS Num_BuntsReached,
    SUM(CASE WHEN pa_result_code = '1B BA' THEN 1 ELSE 0 END) * 1.0 / SUM(is_ab) AS BuntsReached_Rate,
    SUM(CASE WHEN pa_result_code IN ('SF','SH') THEN 1 ELSE 0 END) AS Num_Sacrifices,
    SUM(CASE WHEN pa_result_code IN ('SF','SH') THEN 1 ELSE 0 END) * 1.0 / SUM(is_pa) AS Sacrifice_Rate,
    SUM(pitches_seen) AS Num_PitchesSeen,
    SUM(pitches_seen) * 1.0 / SUM(is_pa) AS Avg_PitchesSeen
FROM source
GROUP BY player_id, player_name