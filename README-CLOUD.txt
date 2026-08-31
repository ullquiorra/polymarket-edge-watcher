POLYMARKET EDGE WATCHER - FREE CLOUD VERSION (GitHub Actions)
=============================================================
Goal: the watcher runs on GitHub's computers instead of yours, about
23 hours a day, for $0. Your PC can be switched off.

WHY THIS WORKS
- watcher.py needs only plain Python and internet - nothing to install.
- GitHub lets any PUBLIC repository run its free "Actions" computers for
  unlimited minutes. The schedule in watch.yml starts a fresh watcher
  4 times a day (00:00, 06:00, 12:00, 18:00 UTC). Each one watches for
  about 5h45m, then saves the new CSV rows back into the repo before
  the next one takes over. Short handover gaps (a few minutes) are normal.
- The data is just public Polymarket price snapshots - nothing private,
  no accounts, no orders - so a public repo is safe. Public is also
  required: a private repo would burn through the free minutes fast.
- The CSV's local_time column is set to your clock (UTC+1) via the
  workflow's TZ setting, so your dashboard and analyzer read it as usual.

ONE-TIME SETUP (about 15 minutes, all in the browser)
1. Make a free account at github.com (or sign in).
2. Click the + at the top right -> New repository.
     Name: polymarket-edge-watcher
     Visibility: Public  (this is what makes it free)
     Leave every checkbox unticked, click Create repository.
3. On the repo page click "uploading an existing file".
     Drag in: watcher.py  and  your current watch_data.csv (from this
     folder - that seeds the cloud with the data you already collected).
     Click Commit changes. (Skip the CSV if you want a fresh start.)
4. Add the schedule file: click "Add file" -> "Create new file".
     Name it exactly:  .github/workflows/watch.yml
     (typing the slash creates the folders automatically)
     Open your local cloud\watch.yml in Notepad, copy everything,
     paste it in, click Commit changes.
5. Turn Actions on: open the "Actions" tab. If GitHub shows a green
     button "I understand my workflows, go ahead and enable them",
     click it.

QUICK TEST (10 minutes)
6. In the Actions tab click "edge-watcher" in the left list ->
     "Run workflow" -> leave minutes as 10 -> green "Run workflow".
7. Refresh in a minute: a run called "edge-watcher" appears with a
     yellow dot (working). After ~12 min it turns green (done).
8. Go back to the repo home page: watch_data.csv should now show a
     newer update time, and watch_log.txt should exist. That is the
     cloud watcher talking to Polymarket. It now runs 4 shifts a day
     by itself - nothing more to do.

GETTING THE DATA BACK HOME
9. On the repo page click watch_data.csv -> the raw download icon
     (or Raw button, then Ctrl+S) -> save it over
     C:\Users\HP\Desktop\polymarket-edge-watcher\watch_data.csv
   Then run your dashboard and analyzer exactly as before.
   Tip: once the cloud watcher is confirmed working, stop your local
   watcher (close its black window) so the two data files don't drift.

GOOD TO KNOW
- Check on it any time: the Actions tab lists every shift with its
  start/stop time and a green/yellow/red dot. A red X means that shift
  had a problem; open it and read the last lines to see why.
- GitHub sometimes starts a scheduled run a few minutes late. That just
  shortens the blind gap - nothing to fix.
- Total usage is about 23 h/day of a free runner. This is a common,
  tolerated hobby use; if GitHub ever objects, the same script moves to
  Hugging Face's free tier instead.
- The watcher is still read-only: public data in, CSV rows out. It can
  never place an order or touch money.
