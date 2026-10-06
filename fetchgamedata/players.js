const fs = require("fs");
const puppeteer = require("puppeteer");
const path = require("path");

async function createBrowser() {
    return await puppeteer.launch({
        headless: false,
        protocolTimeout: 0,
    });
}

(async () => {
  // Directory where CSV files will be saved
  const outputFile = "playermetadata.csv";

  // if file empty or doesn't exist, add headers
  if (!fs.existsSync(outputFile)) {
    fs.writeFileSync(outputFile, "player_id,player_name,player_team,position,handedness,height_weight,dob,debut,contract,jersey_numbers,photo_link\n");
  }

  // Launch a browser window
  const browser = await createBrowser();
  const page = await browser.newPage();

  const pageCurtesyDelay = 1500; // 1.5 seconds delay between page loads to be courteous to the server

  const playerDataDir = "../computeplayerdata/playerdata";
  let playerIds = fs.readdirSync(playerDataDir);
  let savedPlayerCount = 0;

  // see which player ids are already in the file, and skip those
  const existingPlayerIds = new Set();
  if (fs.existsSync(outputFile)) {
    const existingContent = fs.readFileSync(outputFile, "utf8");
    const lines = existingContent.split("\n").slice(1); // Skip header
    for (const line of lines) {
      const [player_id] = line.split(",");
      existingPlayerIds.add(player_id);
    }
  }
  playerIds = playerIds.filter(id => !existingPlayerIds.has(id.replace(".csv","")));

  console.log(`Processing ${playerIds.length} players...`);

  for (const filename of playerIds) {
    try {
      // Construct the URL
      const player_id = filename.split('.')[0];
      const url = `https://www.baseball-reference.com/players/${player_id.charAt(0)}/${player_id}.shtml`;

      // Navigate to the specified URL
      await page.goto(url, { timeout: 60000, waitUntil: 'domcontentloaded' });

      // Wait for your specific element to appear
      await page.waitForSelector('#info', { timeout: 60000 });

      const metafields = await page.evaluate(() => {
        return [...document.querySelectorAll("#meta div~div > p")].map(x => x.innerText);
      });

      const name = await page.evaluate(() => document.querySelector("#info h1").innerText);
      const team = metafields.find(field => field.startsWith("Team:"));
      const position = metafields.find(field => field.startsWith("Position"));
      const handedness = metafields.find(field => field.startsWith("Bats:"));
      const height_weight = metafields.find(field => field.match(/^\d+\-\d+/));
      const dob = metafields.find(field => field.startsWith("Born:"));
      const debut = metafields.find(field => field.startsWith("Debut:"));
      const contract = metafields.find(field => field.startsWith("2026 Contract"));

      const photo_link = await page.evaluate(() => {
        return document.querySelector("#meta .media-item img").src;
      });
      const jersey_numbers = await page.evaluate(() => {
        return [...document.querySelectorAll(".uni_holder .medal text")].map(x => x.textContent).join("-");
      });

      // commit to a file in the output directory
      const playerContent = `${player_id},"${name}","${team}","${position}",${handedness},"${height_weight}","${dob}","${debut}","${contract}",${jersey_numbers},"${photo_link}"\n`;
      fs.appendFileSync(outputFile, playerContent);

      savedPlayerCount++;
      if (savedPlayerCount % 5 === 0) {
        console.log(`Saved metadata for ${savedPlayerCount}/${playerIds.length} players (${Math.round((savedPlayerCount / playerIds.length) * 100)}%)`);
      }

      // Wait for next page load to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, pageCurtesyDelay));

    } catch (error) {
      console.error(`Failed to process ${filename}:`, error.message);
    }
  }

  console.log(`Total players processed: ${savedPlayerCount}`);

  // Close the browser
  await browser.close();
})();