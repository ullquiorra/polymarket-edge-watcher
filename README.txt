POLYMARKET BTC 15-MINUTE "UP OR DOWN" EDGE WATCHER
==================================================
(read-only research tool - no account, no money, no orders)

WHAT IT DOES
This script watches Polymarket's free public price data for the current
15-minute "Bitcoin Up or Down" market. Every 4 seconds it reads the real
order book for both sides (Up and Down) and asks one question:

    "If I had a live bot right now, could I buy BOTH sides for under
     $1.00 total?"

It then writes down what it saw. That is all it does. It never logs in,
never trades, and cannot touch any money.

HOW TO START
1. Double-click  Start watcher.bat
2. A black window opens and lines start scrolling. That is the watcher.
3. Leave the computer on and the window open. Hours are fine, days are fine.

HOW TO STOP
Close the black window, or click in it and press Ctrl+C. It writes a
final summary first, then stops. You can start it again any time.

WHERE THE DATA GOES (in this same folder)
- watch_log.txt   The readable log. Records:
                    - every moment with an EDGE (both sides under 100c)
                    - a "NO EDGE (still watching)" heartbeat every 5 minutes
                    - window changes, start/stop, network warnings
                    - a stats summary every 30 minutes
- watch_data.csv  Every single 4-second snapshot in spreadsheet form.
                  Open it with Excel to sort, filter, and analyse.

WHAT A LOG LINE MEANS
16:58:41 - August 30, 4:45PM-5:00PM ET - Up seen at 47c, Down seen at 51c
-> would total 98c -> 2c EDGE (offered: 630 / 1,240 shares)

  47c / 51c        The cheapest price a seller was actually offering
                   ("best ask") for Up and Down at that moment. This is
                   the real buyable price - NOT the midpoint number shown
                   on the website, which flatters the numbers.
  would total 98c  What buying one share of each would have cost.
  2c EDGE          100c minus the total. Positive = the combo cost under
                   $1, so one of the two shares pays out $1 and you keep
                   the difference (gross, before any fees).
  offered: ...     How many shares were available at those exact prices -
                   this answers "could you actually have caught it?"

AFTER A FEW DAYS, LOOK AT:
1. How often do EDGE lines appear?                (rarely? constantly?)
2. How big are the edges?                         (a real 5c, or 0.5c?)
3. How many shares were offered at those prices?  (catchable, or dust?)

The CSV columns up_bid_cents / up_ask_cents etc. also show the bid-ask
spread on each side, so you can see how much of any "edge" would survive
real trading costs.

GOOD TO KNOW
- Needs internet. A network hiccup just logs a warning and keeps going.
- The edge shown is gross: if Polymarket ever charges trading fees on
  these markets, the real net edge is smaller than the logged number.
- The log files only grow. Delete old watch_log.txt / watch_data.csv any
  time (while the watcher is stopped) to start fresh.
