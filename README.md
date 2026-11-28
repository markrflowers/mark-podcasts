# Mark's Weekly Briefings — private podcast feed

Feed URL: https://markrflowers.github.io/mark-podcasts/feed.xml

Each weekly podcast task adds its MP3 like this:

```bash
git clone --depth 1 https://github.com/markrflowers/mark-podcasts.git
cd mark-podcasts
python3 tools/publish.py --mp3 /path/Show_YYYY-MM-DD.mp3 --show "Show name" \
  --title "Headline topics" --description "Two-sentence summary"
GH_TOKEN=... tools/push.sh
```

`push.sh` replaces the history with a single commit so old MP3s don't pile up.
The newest 6 episodes of each show are kept. The token lives in Google Drive
(`github-token.txt`, "The Saturday Signal" folder) and expires Feb 21, 2027.
