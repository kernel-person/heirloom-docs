# Inebriation

Distillery tracks drunkenness separately from ordinary food. Drinks can raise a player's level, affect chat through slurring rules, and trigger blackout or wakeup behavior depending on configuration.

## Dose And The ‰ Scale

Drink lore shows alcohol dose as cl of a 40% spirit: `equivalent cl = actual liquid cl × ABV / 40`. An 8 cl drink at 20% shows 4 cl equivalent. Mocktails show 0 cl; plain juices and Soda Water have no alcohol row. Intake uses the same conversion before player sensitivity. Mixing and splitting preserve the total dose, and stored beverage volume remains actual liquid volume, including for legacy bottles.

Drunkenness readouts use a **0–4‰ gameplay scale**, where 4‰ is the configured meter maximum. This is a game value, not a real blood-alcohol or breath-test estimate. The default meter holds 40 cl equivalent, so a 10 cl dose raises it by 1‰ before sensitivity. `/hld drunk` displays up to two decimals; the action bar has no numeric amount. Fractional amounts survive consumption, recovery and restart. Existing customized intake limits and sensitivity settings remain effective.

## Quality And The Bar

The displayed quality is the alcohol-dose-weighted average of the drinks still contributing to drunkenness, using the Core Poor → Perfect dice and names. Recovery preserves that average until fully sober, then clears it so an old session cannot contaminate the next drink. Quality calculations retain fractions; only the displayed tier is rounded. Perfect has no decorative stars. Valid saved averages survive updates; demonstrably corrupt legacy quality is repaired to Normal without removing drunkenness.

The shared 20-cell bar shows drunkenness and quality without numbers or brackets. Drinking sweeps left-to-right; milk, sobering foods and other reductions sweep all the way left. Each wave travels for 12 ticks, clears its tail over six more ticks, then holds a clean steady bar for 60 ticks. The final four cells grade from warm gold toward muted red, with subdued empty cells. Natural recovery triggers a downward wave when a visible cell changes.

While drunk, a steady reminder becomes eligible **ten seconds after the last bar frame actually displayed**, including the final hold frame. The manager checks once per second, so a reminder can arrive up to a second later. Configure `inebriation.status_reminder_interval_seconds` (default `10`, `0` disables reminders). Reminders never interrupt workstation feedback or an active wave, and blocked attempts do not restart the timer. Logout, reload and disable clear pending presentation work.

Crossing upward into the danger zone at **3.2‰** immediately gives **four seconds of Blindness I**. Further drinks while already above the threshold do not retrigger this warning. It rearms after dropping below the threshold and preserves stronger or longer existing blindness. Administrators can configure the threshold and duration.

## Sobering

These are the default gameplay reductions; the in-game guide shows the effective server settings and applicable player recovery overrides.

| Source | Reduction |
| --- | ---: |
| Milk | 0.2‰ |
| One puking episode | 0.3‰ |
| Bread | 0.16‰ |
| Food with inherited `SOBERING` | 0.6‰ |
| Death | 0.8‰ |
| Natural recovery | 0.08‰ per minute |

Puking drains once when an episode begins, not once per particle or queued extension. Disabled or aborted episodes do not drain. Milk and puking trigger the same downward bar wave as other recovery. Values never take drunkenness below zero.

The Heirloom `SOBERING` food property works through ordinary consumption and placed food while Distillery and inebriation are enabled. Each serving drains once and supports fractional reductions. Use it for server foods such as coffee, meals or custom hangover cures.

Open `/hld guide` or **Distillery Guide** in `/hl`, then choose **Drunkenness & Sobering**. Recovery information is on that same destination. The guide marks disabled sources and reflects configured recovery values. **Distillery Drinks** and `/hld menu` open the drink catalog and editable recipe previews.

## Commands

```text
/hld drunk
/hld setdrunk Alex 1.2‰
/hld adddrunk Alex -0.2‰
/hld wakeup list
```

Administrator commands accept explicit `‰` values. Bare numbers remain equivalent cl for compatibility: `/hld setdrunk Alex 10` sets the same default-meter level as `1‰`. Set/add success messages use ‰. Beverage ABV and cl lore do not change.
