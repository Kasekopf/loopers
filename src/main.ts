import { print, visitUrl } from "kolmafia";

type Run = {
  id: number;
  player: string;
  class: string;
  path: string;
  core: "softcore" | "hardcore" | "casual";
  days: number;
  turns: number;
};

export function main(): void {
  const page = visitUrl(
    "museum.php?floor=1&place=leaderboards&whichboard=999&showhist=500"
  ).replace(/&nbsp;/g, " ");
  const runs: Run[] = [];

  // Note this does not include OCRS runs, since they look different in the table. But that is fine.
  const run_regex = new RegExp(
    /<tr><td>[^<]*?<\/td><td><a href=showplayer.php\?who=(\d+) class=nounder><b>([^<]*?)<\/b><\/a> <\/td><td>([^<]*?)<\/td><td>([^<]*?)<\/td><td>([\d,]*?)<\/td><td align=right>([\d,]*?)<\/td><\/tr>/g
  );
  let match;
  do {
    match = run_regex.exec(page);
    if (match) {
      runs.push({
        id: parseInt(match[1]),
        player: match[2].trim(),
        class: match[3].trim(),
        path: match[4].trim().replace("(Hardcore)", "").replace("(Casual)", "").trim(),
        core: match[4].includes("(Hardcore)")
          ? "hardcore"
          : match[4].includes("(Casual)")
          ? "casual"
          : "softcore",
        days: parseInt(match[5].replace(/,/g, "")),
        turns: parseInt(match[6].replace(/,/g, "")),
      });
    }
  } while (match);

  const gyouers = new Set<string>(
    runs.filter((run) => run.days === 1 && run.path === "Grey You").map((run) => run.player)
  );
  const csers = new Set<string>(
    runs
      .filter((run) => run.days === 1 && run.path === "Community Service")
      .map((run) => run.player)
  );
  const casual = new Set<string>(
    runs.filter((run) => run.days === 1 && run.core === "casual").map((run) => run.player)
  );
  print("In the last 500 ascensions:");
  print(
    `* ${gyouers.size} players did a 1-day Grey You run. Of those, ${
      [...casual].filter((p) => gyouers.has(p)).length
    } players also did a 1-day casual run.`
  );
  print(
    `* ${csers.size} players did a 1-day Community Service run. Of those, ${
      [...casual].filter((p) => csers.has(p)).length
    } players also did a 1-day casual run.`
  );
  print(`* ${casual.size} players did a 1-day casual run in total.`);
}
