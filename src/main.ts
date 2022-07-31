import { print, visitUrl } from "kolmafia";

type Run = {
  id: number;
  player: string;
  class: string;
  path: string;
  days: number;
  turns: number;
};
export function main(): void {
  const page = visitUrl("museum.php?floor=1&place=leaderboards&whichboard=999&showhist=500");
  const runs: Run[] = [];

  const run_regex = new RegExp(
    /<tr><td>.*?<\/td><td><a href=showplayer.php\?who=(\d+) class=nounder><b>(.*?)<\/b><\/a>&nbsp;<\/td><td>(.*?)<\/td><td>(.*?)<\/td><td>(.*?)<\/td><td align=right>(.*?)<\/td><\/tr>/g
  );
  let match;
  do {
    match = run_regex.exec(page);
    if (match) {
      runs.push({
        id: parseInt(match[1]),
        player: match[2],
        class: match[3],
        path: match[4],
        days: parseInt(match[5].replace(",", "")),
        turns: parseInt(match[6].replace(",", "")),
      });
    }
  } while (match);

  runs.forEach((run) => print(JSON.stringify(run)));
}
