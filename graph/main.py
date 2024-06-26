import bs4
import collections
import dataclasses
import datetime
import itertools
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import pickle
import requests
from typing import Iterable, Dict, Sequence, Set


GRAPH_END_DATE = '2024-06-06'
RUN_END_DATE = '2024-06-09'
MAX_ID = 10000000


def date(text: str):
    return datetime.datetime.strptime(text, "%Y-%m-%d").date()


def koldb_url(run_type: str, num_to_get: int, id_start: int, id_end: int):
    return f'http://koldb.com/searchresults.php?type={run_type}' +\
           f'&xgoo=on&days1=1&days2=1&sortby=dt&timetype=ralph&event=ns13&lim={num_to_get}' +\
           f'&id1={id_start}&id2={id_end}'


def date(text: str):
    return datetime.datetime.strptime(text, "%Y-%m-%d").date()


@dataclasses.dataclass
class Run:
    player: str
    date: datetime.date
    turns: int
    path: str

    def __init__(self, row):
        columns = row.find_all("td")
        self.player = columns[1].find('a').text
        self.date = date(columns[4].find('a').text)
        self.turns = int(columns[6].text)

        self.path = columns[7].find("img")["alt"] if len(columns) == 11 else "No path"

    def __str__(self):
        return f'{self.player}: {self.path} ({self.date} @ {self.turns})'


def get_runs(url):
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.content, 'html.parser')

    table = soup.find('table', {'id': 'result_table'})
    if table is None:
        return []
    rows = table.find_all('tr')
    return [Run(row) for row in rows[1:]]


def pickle_cache(run_type: str):
    if os.path.exists(f'cache/{run_type}'):
        with open(f'cache/{run_type}', 'rb') as input_file:
            return pickle.load(input_file)
    print(f'Loading {run_type} from koldb')

    runs = []
    for i in range(0, MAX_ID, 100000):
        url = koldb_url(run_type, 10000, i, i+100000)
        print(url)
        runs_segment = get_runs(url)
        print(f'   {len(runs_segment)}')
        if len(runs_segment) == 0:
            break
        runs.extend(runs_segment)
    os.makedirs('cache', exist_ok=True)
    with open(f'cache/{run_type}', 'wb') as output_file:
        pickle.dump(runs, output_file)
    return runs


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


class DateFigure:
    def __init__(self):
        self.f, self.ax = plt.subplots(1, 1)
        self.ax.set_title('The Rise of the KoL Looper')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=365))
        self.ax.set_xlim(left=date('2018-01-01'), right=date(GRAPH_END_DATE))
        self.ax.set_xticks([
            date('2018-01-01'),
            date('2019-01-01'),
            date('2020-01-01'),
            date('2021-01-01'),
            date('2022-01-01'),
            date('2023-01-01'),
            date('2024-01-01'),
            date(GRAPH_END_DATE)
        ])
        self.ax.set_ylim(bottom=0, top=140)
        self.f.autofmt_xdate()
        self.ax.set_xlabel('Week Date')
        self.ax.set_ylabel('Number of Loopers')
        plt.figtext(0.143, 0.83, 'A looper is a player that completes', horizontalalignment='left')
        plt.figtext(0.143, 0.785, 'at least four 1-day runs per week of:', horizontalalignment='left')
        plt.figtext(0.01, 0.01, 'Crawled from KoLDB', horizontalalignment='left', color='gray')
        plt.figtext(0.99, 0.01, 'Plotted by Kasekopf', horizontalalignment='right', color='gray')

    def plot_count(self, values: Dict[datetime.date, Sequence], **kwargs):
        counts = {key: len(values[key]) for key in values}
        self.plot(counts, **kwargs)

    def plot(self, values: Dict[datetime.date, float], **kwargs):
        x = sorted(values.keys())
        y = [values[x_val] for x_val in x]
        self.ax.plot(x, y, **kwargs)

    def show(self):
        legend = self.ax.legend(
            loc=(0.01, 0.51),
            frameon=False,
        )
        for handle in legend.legendHandles:
            handle.set_linewidth(2.0)
        self.f.show()
        self.f.savefig('output.png')


def find_loopers(runs: Iterable[Run], time_window: int, threshold: int):
    runs = sorted(runs, key=lambda run: run.date)
    runs_by_date = itertools.groupby(runs, key=lambda run: run.date)
    players_by_date = collections.defaultdict(list)
    for day, runs_in_day in runs_by_date:
        players_by_date[day] = [run.player for run in runs_in_day]

    loopers_by_date = {}
    for day in daterange(date('2007-07-01'), date(RUN_END_DATE)):
        players = []
        for i in range(-time_window, time_window+1):
            offset_players = players_by_date[day + datetime.timedelta(days=i)]
            players.extend(offset_players)

        run_counts = collections.Counter(players)
        loopers_by_date[day] = set(p for p in run_counts if run_counts[p] >= threshold)
    return loopers_by_date


def overlap_loopers(a: Dict[datetime.date, Set], b: Dict[datetime.date, Set]):
    return {key: a[key].intersection(b[key]) for key in a}


def remove_loopers(a: Dict[datetime.date, Set], b: Dict[datetime.date, Set]):
    return {key: a[key].difference(b[key]) for key in a }


def do():
    noncasual = pickle_cache('normal') + pickle_cache('hardcore')
    casual = pickle_cache('casual')

    casual_loopers = find_loopers(casual, 3, 4)
    gyou_loopers = find_loopers(filter(lambda r: r.path == "Grey You", noncasual), 3, 4)
    cs_loopers = find_loopers(filter(lambda r: r.path == "Community Service", noncasual), 3, 4)
    smol_loopers = find_loopers(filter(lambda r: r.path == "A Shrunken Adventurer am I", noncasual), 3, 4)
    robot_loopers = find_loopers(filter(lambda r: r.path == "You, Robot", noncasual), 3, 4)

    cs_fullloopers = overlap_loopers(casual_loopers, cs_loopers)
    gyou_fullloopers = overlap_loopers(casual_loopers, gyou_loopers)
    casual_only = remove_loopers(remove_loopers(casual_loopers, gyou_loopers), cs_loopers)

    f = DateFigure()
    f.plot_count(casual_only, linewidth=1, color='black', label='Casual (Only)')
    f.plot_count(cs_loopers, linewidth=1, color='blue', label='Community Service')
    # f.plot_count(cs_fullloopers, linewidth=1, color='blue', linestyle=':', label='Community Service & Casual')
    f.plot_count(gyou_loopers, linewidth=1, color='green', label='Grey You')
    # f.plot_count(gyou_fullloopers, linewidth=1, color='green', linestyle=':', label='Grey You & Casual')
    f.plot_count(smol_loopers, linewidth=1, color='orange', label='Shrunken Adventurer')
    f.plot_count(robot_loopers, linewidth=1.5, color='black')
    f.plot_count(robot_loopers, linewidth=1, color='purple', label='You, Robot')

    f.show()


if __name__ == '__main__':
    do()
