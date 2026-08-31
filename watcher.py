#!/usr/bin/env python3
"""
Polymarket "Bitcoin Up or Down" 15-minute window EDGE WATCHER
-------------------------------------------------------------
Read-only research tool. It uses only Polymarket's free, public price
data. It never logs in, never places orders, and needs no account.

Every few seconds it:
  1. Works out which 15-minute BTC window is live right now.
  2. Reads the real order book for the Up token and the Down token.
  3. Asks: "could I have bought BOTH sides right now for under $1.00
     combined?"  (best ask = the cheapest price a seller is offering)
  4. Writes every snapshot to watch_data.csv, and notable moments to
     watch_log.txt (both files appear in this same folder).

Log style (matches the plan):
  16:58:41 - August 30, 4:45PM-5:00PM ET - Up seen at 47c, Down seen at 51c -> would total 98c -> 2c EDGE (offered: 630 / 1,240 shares)
  17:03:10 - August 30, 5:00PM-5:15PM ET - Up seen at 41c, Down seen at 60c -> would total 101c -> NO EDGE (still watching)

Stop it with Ctrl+C or by closing the window; a final summary is
written either way. Start it again any time - the log and CSV just
keep growing.

(The WATCHER_* environment variables only exist so the timing can be
tuned for testing; you never need to touch them.)
"""

import csv
import datetime as dt
import json
import os
import time
import urllib.request

SERIES_PREFIX = "btc-updown-15m-"  # Polymarket's slug pattern for these markets
WINDOW_SECONDS = 900               # 15 minutes

POLL_SECONDS = float(os.environ.get("WATCHER_POLL", "4"))
HEARTBEAT_SECONDS = float(os.environ.get("WATCHER_HEARTBEAT", "300"))
SUMMARY_SECONDS = float(os.environ.get("WATCHER_SUMMARY", "1800"))
MAX_SECONDS = float(os.environ.get("WATCHER_MAX_SECONDS", "0"))  # 0 = run until stopped
HTTP_TIMEOUT = 15

HERE = os.path.dirname(os.path.abspath(__file__))
TXT_PATH = os.path.join(HERE, "watch_log.txt")
CSV_PATH = os.path.join(HERE, "watch_data.csv")

GAMMA_MARKET_URL = "https://gamma-api.polymarket.com/markets?slug={slug}"
CLOB_BOOK_URL = "https://clob.polymarket.com/book?token_id={token_id}"
HEADERS = {"User-Agent": "edge-watcher/1.0 (read-only, public data)"}

CSV_FIELDS = [
    "local_time", "utc_time", "window_slug", "window_label",
    "up_bid_cents", "up_ask_cents", "up_ask_shares",
    "down_bid_cents", "down_ask_cents", "down_ask_shares",
    "total_ask_cents", "edge_cents",
]


# ---------------------------------------------------------------- helpers

def http_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def now_local():
    return dt.datetime.now().strftime("%H:%M:%S")


def console(line):
    print(line, flush=True)


def log(line):
    """Print to the window AND append to the text log."""
    console(line)
    with open(TXT_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fmt_c(cents):
    """95.0 -> '95', 94.5 -> '94.5'."""
    s = f"{cents:.1f}"
    return s[:-2] if s.endswith(".0") else s


def fmt_shares(n):
    return f"{n:,.0f}"


def parse_maybe_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


# ---------------------------------------------------------------- data

_market_cache = {}
_warned_slugs = set()


def get_market(slug):
    """Return the Gamma market dict for a window slug, or None if not listed yet."""
    if slug in _market_cache:
        return _market_cache[slug]
    rows = http_json(GAMMA_MARKET_URL.format(slug=slug))
    market = rows[0] if rows else None
    if market and market.get("clobTokenIds") and market.get("outcomes"):
        outcomes = parse_maybe_json(market["outcomes"])
        tokens = parse_maybe_json(market["clobTokenIds"])
        if len(outcomes) == 2 and len(tokens) == 2:
            market["_outcomes"] = list(zip(outcomes, tokens))
            _market_cache[slug] = market
            return market
    if slug not in _warned_slugs:
        _warned_slugs.add(slug)
        console(f"{now_local()} -- {slug} exists but has no tradeable tokens yet; waiting...")
    return None


def window_label(market, slug):
    question = market.get("question") or slug
    return question.split(" - ", 1)[1] if " - " in question else question


def read_book(token_id):
    """Return (best_bid, best_ask, shares_offered_at_best_ask) as floats, or Nones."""
    book = http_json(CLOB_BOOK_URL.format(token_id=token_id))
    bids = [(float(b["price"]), float(b["size"])) for b in (book.get("bids") or [])]
    asks = [(float(a["price"]), float(a["size"])) for a in (book.get("asks") or [])]
    best_bid = max(p for p, _ in bids) if bids else None
    best_ask = min(p for p, _ in asks) if asks else None
    ask_shares = sum(s for p, s in asks if p == best_ask) if asks else None
    return best_bid, best_ask, ask_shares


def cents_or_blank(price):
    return "" if price is None else round(price * 100, 1)


def csv_append(row):
    is_new = not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------- reporting

def write_summary(stats, started_dt):
    if stats["obs"] == 0:
        log(f"{now_local()} == SUMMARY: no complete snapshots this period ==")
        return
    pct = 100.0 * stats["edges"] / stats["obs"]
    avg = stats["edge_cents_total"] / stats["obs"]
    best = stats["best"]
    if best:
        best_line = (
            f"{fmt_c(best['edge'])}c at {best['time']} "
            f"(Up {fmt_c(best['up'])}c + Down {fmt_c(best['down'])}c = {fmt_c(best['total'])}c)"
        )
    else:
        best_line = "never - the two sides never summed to under 100c"
    log(f"{now_local()} == SUMMARY ({stats['obs']} snapshots, {len(stats['windows'])} windows) ==")
    log(f"   moments with an edge: {stats['edges']} of {stats['obs']} ({pct:.1f}%)")
    log(f"   average gap (100c minus both-asks total): {avg:.2f}c across all snapshots")
    log(f"   best edge: {best_line}")
    log("== end summary ==")


# ---------------------------------------------------------------- main loop

def run():
    started_dt = dt.datetime.now()
    log("=== Polymarket BTC 15-minute edge watcher ===")
    log(f"started {started_dt.strftime('%Y-%m-%d %H:%M:%S')} (local time)")
    log("read-only: free public data, no account, no orders are ever placed")
    log(f"polling every {fmt_c(POLL_SECONDS)}s; text log: watch_log.txt; every snapshot: watch_data.csv")
    log("stop with Ctrl+C or by closing this window")
    log("===")

    stats = {"obs": 0, "edges": 0, "edge_cents_total": 0.0, "best": None, "windows": set()}
    last_heartbeat = time.time()
    last_summary = time.time()
    current_slug = None

    try:
        while True:
            tick = time.time()
            try:
                now = time.time()
                window_start = int(now // WINDOW_SECONDS) * WINDOW_SECONDS
                slug = f"{SERIES_PREFIX}{window_start}"

                if slug != current_slug:
                    market = get_market(slug)
                    if market is None:
                        current_slug = None
                    else:
                        current_slug = slug
                        stats["windows"].add(slug)
                        minutes_left = max(0, round((window_start + WINDOW_SECONDS - now) / 60))
                        log(f"--- {now_local()} - now watching: {window_label(market, slug)} "
                            f"(ends in {minutes_left} min) ---")

                if current_slug is not None:
                    market = _market_cache[current_slug]
                    label = window_label(market, current_slug)
                    books = {}
                    for name, token_id in market["_outcomes"]:
                        bid, ask, ask_shares = read_book(token_id)
                        books[name] = (bid, ask, ask_shares)

                    # Polymarket names these "Up" and "Down"; fall back to whatever exists
                    up_name = "Up" if "Up" in books else next(iter(books))
                    down_name = "Down" if "Down" in books else list(books)[-1]
                    up_bid, up_ask, up_shares = books[up_name]
                    down_bid, down_ask, down_shares = books[down_name]

                    if up_ask is None or down_ask is None:
                        missing = up_name if up_ask is None else down_name
                        console(f"{now_local()} -- no sellers offering '{missing}' right now; skipping this tick")
                    else:
                        total_c = round((up_ask + down_ask) * 100, 1)
                        edge_c = round(100 - (up_ask + down_ask) * 100, 1)
                        stats["obs"] += 1
                        stats["edge_cents_total"] += edge_c

                        csv_append({
                            "local_time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "utc_time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "window_slug": current_slug,
                            "window_label": label,
                            "up_bid_cents": cents_or_blank(up_bid),
                            "up_ask_cents": cents_or_blank(up_ask),
                            "up_ask_shares": "" if up_shares is None else round(up_shares, 1),
                            "down_bid_cents": cents_or_blank(down_bid),
                            "down_ask_cents": cents_or_blank(down_ask),
                            "down_ask_shares": "" if down_shares is None else round(down_shares, 1),
                            "total_ask_cents": total_c,
                            "edge_cents": edge_c,
                        })

                        minutes_left = max(0, round((window_start + WINDOW_SECONDS - now) / 60))
                        if edge_c > 0:
                            stats["edges"] += 1
                            last_heartbeat = time.time()
                            if stats["best"] is None or edge_c > stats["best"]["edge"]:
                                stats["best"] = {"edge": edge_c, "total": total_c, "up": up_ask * 100,
                                                 "down": down_ask * 100, "time": now_local()}
                            log(f"{now_local()} - {label} - {up_name} seen at {fmt_c(up_ask * 100)}c, "
                                f"{down_name} seen at {fmt_c(down_ask * 100)}c -> would total {fmt_c(total_c)}c "
                                f"-> {fmt_c(edge_c)}c EDGE (offered: {fmt_shares(up_shares or 0)} / "
                                f"{fmt_shares(down_shares or 0)} shares)")
                        elif time.time() - last_heartbeat >= HEARTBEAT_SECONDS:
                            last_heartbeat = time.time()
                            log(f"{now_local()} - {label} - {up_name} seen at {fmt_c(up_ask * 100)}c, "
                                f"{down_name} seen at {fmt_c(down_ask * 100)}c -> would total {fmt_c(total_c)}c "
                                f"-> NO EDGE (still watching)")

                        console(f"{now_local()} ends in {minutes_left}m | {up_name} {fmt_c(up_ask * 100)}c | "
                                f"{down_name} {fmt_c(down_ask * 100)}c | both {fmt_c(total_c)}c | "
                                f"{'EDGE ' + fmt_c(edge_c) + 'c' if edge_c > 0 else 'no edge'}")

                if time.time() - last_summary >= SUMMARY_SECONDS:
                    write_summary(stats, started_dt)
                    last_summary = time.time()

            except Exception as ex:
                log(f"{now_local()} !! problem: {type(ex).__name__}: {ex} (will keep trying)")

            elapsed = time.time() - tick
            time.sleep(max(0.5, POLL_SECONDS - elapsed))
            if MAX_SECONDS and time.time() - started_dt.timestamp() >= MAX_SECONDS:
                break
    except KeyboardInterrupt:
        pass

    write_summary(stats, started_dt)
    log(f"=== watcher stopped at {now_local()} ===")


if __name__ == "__main__":
    run()
