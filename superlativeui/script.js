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
            metricItem.querySelector(".player-metric-description").textContent = record.description;
            const value = record.metric.match(/(_Rate|Avg_)/)?.length || ["AVG","OBP","SLG","OPS"].includes(record.metric)
              ? record.value.toFixed(3)
              : record.value;
            metricItem.querySelector(".player-metric-value").textContent = value;
            metricItem.querySelector(".player-metric-pa").textContent = `(${record.plate_appearances} ${record.description.split(" ").length > 2 ? "applicable " : ""}PA)`;

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