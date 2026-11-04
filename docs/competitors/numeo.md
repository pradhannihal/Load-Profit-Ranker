# Numeo Spot: how it scores loads

Checked 2026-11-03. Sources: the logged-in app at agent.numeo.ai (read-only), Numeo's help docs and its blog.
Numeo Spot is an AI dispatcher for fleet dispatchers. It sits on top of DAT and other load boards (mainly
through a Chrome extension inside DAT) and also emails brokers and negotiates rates.

## Their profit calculator (documented)

```
total miles = loaded miles + deadhead miles   (deadhead counts only if "include deadhead" is on; miles come from Google Maps)
fuel        = total miles / MPG × diesel $/gal       (Load Hub default: 7 MPG)
driver pay  = driver $/mi × miles  OR  % of rate
tolls       = route toll estimate (Pro plan) or typed in by hand
profit      = rate − fuel − driver pay − tolls
also shown: RPM (rate / loaded miles) and RPM including deadhead
```

- **Good vs. bad:** the profit number turns green or a warning color when it crosses a profit threshold you set.
  That's the only "is this load good" signal on the load card.
- **Their blog example:** Load A pays $1,500 for 500 loaded + 180 deadhead miles and nets $739 ($1.09/mi).
  Load B pays $1,460 for 520 + 30 miles and nets $806 ($1.47/mi). The load with the higher rate per mile earns less profit.

## "AI ranking" (marketing only)

Numeo says its AI weighs RPM, deadhead, lane history, broker reliability (days to pay, disputes) and backhaul
potential, and it adds a factoring/credit check on the broker. It doesn't publish the formula or the weights.

## What we couldn't see

Load Hub showed no loads, because no load boards are connected on our account, and the extension only runs inside
DAT. We never watched it score a real load. Everything above comes from Numeo's docs and blog.

## Compared to Haul Math

| | Numeo | Haul Math ([formula](../formula.md)) |
|---|---|---|
| Ranks by | profit per load (and $/mi) | **profit per day** |
| Days the truck is tied up | ignored | hours-of-service days, 70-hr cycle, 34-hr restart, appointment dates |
| Fixed costs (truck payment, insurance) | ignored | spread per day |
| Maintenance / tires | ignored | per mile |
| Driver pay | $/mi or % of rate (fleet-oriented) | `payoutPercent` (owner-op / leased-on) |
| Tolls | auto estimate on Pro | typed in |
| Broker credit, lane history, backhaul | yes (paid data) | no |
| Good/bad signal | color vs. profit threshold | target $/day + warnings |

**Takeaway:** Numeo's profit is a per-load margin for fleet dispatchers, and it never asks how many days the load
ties up the truck. That's the case Haul Math is built for: a shorter load that pays less but frees the truck sooner
can win on profit per day. Our formula already covers everything in their calculator except automatic tolls and
broker credit.

## Sources
- [Numeo Spot: truck cost settings](https://numeo.ai/docs/numeo-spot/truck-cost-settings)
- [Load Hub: profitability calculator](https://numeo.ai/docs/load-hub/profitability-calculator)
- [How does the profit calculator work in Numeo Spot](https://intercom.help/numeo-help/en/articles/15508187-how-does-the-profit-calculator-work-in-numeo-spot)
- [Beyond RPM (blog)](https://numeo.ai/blog/beyond-rpm-how-numeo-spot-s-profitability-tools-are-changing-the-dispatch-game)
- [Is RPM enough? (blog)](https://numeo.ai/blog/is-rpm-enough-how-to-evaluate-a-load-beyond-rate-per-mile)
