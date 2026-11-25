# The World in One Day — Tuesday 24 November 2026

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/xnightgarap-95jp/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/xnightgarap-95jp/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A one-page newspaper front page for **Tuesday 24 November 2026** — 35
stories from 6 regions, every one of them happened, or was first
reported, on that day. Built for the
[news-image-20261124](https://make.fun/bounty/news-image-20261124)
bounty on [make.fun](https://make.fun).

## The day in one line

Fourth tanker mined in Hormuz · Hamas security chief killed · Two killed in
Zaporizhzhia flats

## What's on the page

- **3 leads:** a fourth tanker hits a mine in the Strait of Hormuz as
  Iran orders the waterway shut "further day by day"; an Israeli strike
  kills Hamas's security chief in Gaza; a Russian night strike on
  Zaporizhzhia kills two and wounds 40.
- **10 more stories:** Mexico to try 'El Chapo Isidro' itself; a leak
  puts Russian war dead past 490,000; Russian jets enter Korea's
  defence zone; Germany first in line for Ukraine's Delta war system;
  Iraq orders its ministry to run Kurdish oilfields; the Solomons end
  their China security pact; Netanyahu urges Trump to hit Iran again;
  a 5.6 quake in Nepal; fighting traps Ebola responders in Ituri; the
  EU–Indonesia trade deal.
- **22 more stories** in the "also" list, a world map with 13 numbered
  pins, a stat strip (4 tankers, 490,000+ dead, 40 wounded, 5.6 quake,
  181 runs, 7.3m at risk), and a **DATE CHECK** box naming the big
  stories from other days that were deliberately left out — COP31's
  collapse (Sun 22 Nov), Belgium's strike, the Shah–Modi talks and
  more from Monday 23 Nov.

## How it is made

`main.py` (Python 3, standard library only) draws the whole page:
real DejaVu Serif type from `fontdata.py` (glyph bitmaps rendered once
with PIL on this machine — the entry program itself needs no Pillow),
every picture drawn by hand with the primitives in the file, and the
PNG written by hand with `zlib`. No network, no files read except
`fontdata.py`. Two runs write byte-identical output.

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

`NEWS.md` is the source document: all 35 stories with their sources,
plus the full DATE CHECK list and the stat strip.

## Sources

Just Security, Associated Press, Middle East Eye, Euronews, Kayhan,
Cumhuriyet Daily, PressTV, 10Things Global News, Reuters, Al Arabiya,
Dawn, La Mediterranee, The Kyiv Independent, The Global Eye, Horizon,
Chanakya Lens, UN News, The Hindu, The National, The Straits Times,
Apex Sports News, IANS, ScoreZaap, GalaxySports7, Oxfam. Original
drawings.
