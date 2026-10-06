const fs = require("fs");
const puppeteer = require("puppeteer");
const path = require("path");

// get unique boxscore links from each team schedule
// concat together unique:
// [...document.querySelectorAll("#team_schedule a[href^='/boxes/'][href$='.shtml']")].map(x => x.href)
//
// find gameid from each boxscore link
// gameid = link.split("/")[5].split(".")[0]
//
// on each boxscore page, save
// meta file:
// - [...document.querySelectorAll(".scorebox_team a[href^='/teams/']")].map(x => x.href.split("/")[4]) as away and home teams, respectively
// - [...document.querySelectorAll(".scorebox_meta div")].map(x => x.innerText) as date, time, attendance, venue, duration, game type
// as csv with headers: gameid,awayteam,hometeam,date,time,attendance,venue,duration,gametype
// table2csv(document.querySelectorAll("table[id$='batting']")[0].id) as gameid_awaybatting.csv
// table2csv(document.querySelectorAll("table[id$='batting']")[1].id) as gameid_homebatting.csv
// table2csv("play_by_play") as gameid_playbyplay.csv

async function createBrowser() {
    return await puppeteer.launch({
        headless: false,
        protocolTimeout: 0,
    });
}

(async () => {
  const teamAbbreviations = {
    diamondbacks: "ARI",
    braves: "ATL",
    orioles: "BAL",
    redsox: "BOS",
    cubs: "CHC",
    whitesox: "CHW",
    reds: "CIN",
    guardians: "CLE",
    rockies: "COL",
    tigers: "DET",
    astros: "HOU",
    royals: "KCR",
    angels: "LAA",
    dodgers: "LAD",
    marlins: "MIA",
    brewers: "MIL",
    twins: "MIN",
    mets: "NYM",
    yankees: "NYY",
    athletics: "ATH",
    phillies: "PHI",
    pirates: "PIT",
    padres: "SDP",
    giants: "SFG",
    mariners: "SEA",
    cardinals: "STL",
    rays: "TBR",
    rangers: "TEX",
    bluejays: "TOR",
    nationals: "WSN",
  };

  // Directory where CSV files will be saved
  const outputDir = "gamedata";

  // Check if the directory exists; if not, create it
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
    console.log(`Created directory: ${outputDir}`);
  }

  // Launch a browser window
  const browser = await createBrowser();
  const page = await browser.newPage();

  const pageCurtesyDelay = 3000; // 3 seconds delay between page loads to be courteous to the server

  let allGameLinks = new Set();

  for (const [teamName, teamAbbr] of Object.entries(teamAbbreviations)) {
    try {
      // Construct the URL
      const url = `https://www.baseball-reference.com/teams/${teamAbbr}/2026-schedule-scores.shtml`;

      // Navigate to the specified URL
      await page.goto(url, { timeout: 60000, waitUntil: 'domcontentloaded' });

      // Wait for your specific element to appear
      await page.waitForSelector('#team_schedule', { timeout: 60000 });

      const gameLinks = await page.evaluate(() => {
        return [...document.querySelectorAll("#team_schedule a[href^='/boxes/'][href$='.shtml']")].map(x => x.href);
      });
      allGameLinks = new Set([...allGameLinks, ...gameLinks]);

      console.log(`Captured links for ${teamName} games`);

      // Wait for next page load to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, pageCurtesyDelay));

    } catch (error) {
      console.error(`Failed to process ${teamName}:`, error.message);
    }
  }

  console.log(`Total unique game links found: ${allGameLinks.size}`);

  let gameCounter = 0;

  for (const gameLink of allGameLinks) {
    try {
      gameCounter++;

      // if file exists for this game, skip it
      const gameId = gameLink.split("/")[5].split(".")[0];
      const metaFilePath = path.join(outputDir, `${gameId}_meta.csv`);
      if (fs.existsSync(metaFilePath)) {
        console.log(`Skipping game ${gameId}: already saved`);
        continue;
      }

      console.log(`Processing game ${gameCounter} of ${allGameLinks.size} (${Math.round(gameCounter / allGameLinks.size * 1000) / 10}%)`);

      // Navigate to the game link
      await page.goto(gameLink, { timeout: 60000, waitUntil: 'domcontentloaded' });

      // Wait for your scorebox data to appear
      await page.waitForSelector('.scorebox_team', { timeout: 60000 });
      await page.waitForSelector('.scorebox_meta', { timeout: 60000 });

      // Extract meta information
      const metaInfo = await page.evaluate(() => {
        const teams = [...document.querySelectorAll(".scorebox_team a[href^='/teams/']")].map(x => x.href.split("/")[4]);
        const meta = [...document.querySelectorAll(".scorebox_meta div")].map(x => x.innerText.replaceAll(",", "")).filter(x => !x.startsWith("Logos")); // Remove commas to avoid CSV issues
        return { teams, meta };
      }, { timout: 60000 });

      // Write the extracted meta information to a CSV file
      const metaContent = `gameid,awayteam,hometeam,date,time,attendance,venue,duration,gametype\n${gameId},${metaInfo.teams[0]},${metaInfo.teams[1]},${metaInfo.meta.join(",")}`;
      fs.writeFileSync(metaFilePath, metaContent);

      // Wait for batting tables to appear
      await page.waitForSelector("table[id$='batting']", { timeout: 60000 });

      // Extract first batting table to gameid_awaybatting.csv
      const awayBattingTableId = await page.evaluate(() => {
        const tables = [...document.querySelectorAll("table[id$='batting']")];
        return tables[0].id;
      }, { timeout: 60000 });

      // Run `table2csv` for the away batting table
      await page.evaluate((tableId) => {
        table2csv(tableId);
      }, awayBattingTableId);

      // Wait for the element to be added to the DOM
      await page.waitForSelector(`#csv_${awayBattingTableId}`);

      // Extract the away batting content
      const awayBattingContent = await page.evaluate((tableId) => {
        const elem = document.getElementById(`csv_${tableId}`);
        return elem.innerText.match(/Batting(.|\n)*/)[0];
      }, awayBattingTableId);

      // Write the extracted content to a CSV file
      const awayBattingFilePath = path.join(outputDir, `${gameId}_awaybatting.csv`);
      fs.writeFileSync(awayBattingFilePath, awayBattingContent);

      // Extract second batting table to gameid_homebatting.csv
      const homeBattingTableId = await page.evaluate(() => {
        const tables = [...document.querySelectorAll("table[id$='batting']")];
        return tables[0].id; // second table, but first table has been converted to csv, so now it is the only batting table remaining
      });

      // Run `table2csv` for the home batting table
      await page.evaluate((tableId) => {
        table2csv(tableId);
      }, homeBattingTableId);

      // Wait for the element to be added to the DOM
      await page.waitForSelector(`#csv_${homeBattingTableId}`);

      // Extract the home batting content
      const homeBattingContent = await page.evaluate((tableId) => {
        const elem = document.getElementById(`csv_${tableId}`);
        return elem.innerText.match(/Batting(.|\n)*/)[0];
      }, homeBattingTableId);

      // Write the extracted content to a CSV file
      const homeBattingFilePath = path.join(outputDir, `${gameId}_homebatting.csv`);
      fs.writeFileSync(homeBattingFilePath, homeBattingContent);

      // Run `table2csv("play_by_play")` in the page context
      await page.evaluate(() => {
        table2csv("play_by_play");
      });

      // Wait for the element to be added to the DOM
      await page.waitForSelector("#csv_play_by_play");

      // Extract the play-by-play content
      const playByPlayContent = await page.evaluate(() => {
        const elem = document.getElementById("csv_play_by_play");
        return elem.innerText.match(/Inn(.|\n)*/)[0];
      });

      // Write the extracted content to a CSV file
      const playByPlayFilePath = path.join(outputDir, `${gameId}_playbyplay.csv`);
      fs.writeFileSync(playByPlayFilePath, playByPlayContent);

      console.log(`Saved data for game ${gameId}`);

      // Wait for the specified delay
      await new Promise(resolve => setTimeout(resolve, pageCurtesyDelay));

    } catch (error) {
      console.error(`Failed to process game link ${gameLink}:`, error.message);
    }
  }

  // Close the browser
  await browser.close();
})();
