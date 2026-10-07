document.onreadystatechange = function () {
  if (document.readyState === "complete") {
    document.querySelector("#ft-year").textContent = new Date().getFullYear();

    const recordContainer = document.querySelector("#record-container");
    const recordItemTemplate = document.querySelector("#record-item-template");
    const metricItemTemplate = document.querySelector("#player-metric-template");
    // load all player records from a data source and populate the record container
    fetch("playerrecords.json")
      .then(response => response.json())
      .then(players => {
        Object.entries(players).forEach(([playerId, player]) => {
          const recordItem = recordItemTemplate.cloneNode(true);
          recordItem.id = "";
          recordItem.querySelector(".player-picture").src = player.player_info.photo_link;
          recordItem.querySelector(".player-link").textContent = player.player_info.player_name;
          recordItem.querySelector(".player-link").href = `https://www.baseball-reference.com/players/${playerId.charAt(0)}/${playerId}.shtml`;
          recordItem.querySelector(".player-team").textContent = player.player_info.player_team ?? "Unassigned";

          for(let i = 0; i < player.records.length; i++) {
            const record = player.records[i];
            const metricItem = metricItemTemplate.cloneNode(true);
            metricItem.id = "";
            const description = formatMetricName(record.description);
            metricItem.querySelector(".player-metric-description").textContent = description;
            let value = record.value;
            if (record.metric.startsWith("Avg_") || ["AVG","OBP","SLG","OPS"].includes(record.metric)) {
              value = record.value.toFixed(3);
            } else if (record.metric.endsWith("_Rate")) {
              value = (record.value * 100).toFixed(1) + "%";
            }
            metricItem.querySelector(".player-metric-value").textContent = value;
            metricItem.querySelector(".player-metric-pa").textContent = `(${record.plate_appearances} ${record.is_situational ? "applicable " : ""}PA)`;

            recordItem.querySelector(".player-metric-container").appendChild(metricItem);
          }

          recordContainer.appendChild(recordItem);
        });
      });
  }
};

function refreshSearch(evt) {
  const terms = evt.target.value.toLowerCase().split(/\s+/);
  const recordContainer = document.querySelector("#record-container");
  const recordItems = recordContainer.querySelectorAll(".record-item");
  recordItems.forEach(item => {
    const text = item.textContent.toLowerCase();
    const isVisible = terms.every(term => text.includes(term));
    item.style.display = isVisible ? "" : "none";
  });
  if (recordContainer.querySelectorAll(".record-item:not([style*='display: none'])").length === 0) {
    document.querySelector("#no-results-found").style.display = "block";
  } else {
    document.querySelector("#no-results-found").style.display = "none";
  }
}

function formatMetricName(description) {
  // const metric_name_map = {
  //   "Avg_PitchesSeen": "Avg Pitches Seen per PA",
  //   "Avg_OutsGenerated": "Avg Outs Generated per PA",
  //   "Highest Num_OutResult": "Most PAs Resulting in an Out",
  //   "Lowest Num_OutResult": "Fewest PAs Resulting in an Out",
  //   "OutResult_Rate": "Ratio of PAs Resulting in an Out",
  //   "OutsGenerated_Rate": "Avg Outs Generated per PA",
  //   "StrikeoutsLooking_Rate": "Ratio of Strikeouts that are Looking",
  //   "StrikeoutsSwinging_Rate": "Ratio of Strikeouts that are Swinging",
  //   "BuntAttempt_Rate": "Bunt Attempts per PA"
  // };

  // for (const [key, value] of Object.entries(metric_name_map)) {
  //   description = description.replace(key, value);
  // }
  description = description.match(/Highest\sH($|\s)/)?.length
    ? description.replace("Highest H", "Most Hits")
    : description;
  description = description.replace("Highest Num_", "Most ");
  description = description.replace("Lowest Num_", "Fewest ");

  return description;
}

