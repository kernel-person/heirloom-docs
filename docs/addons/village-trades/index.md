# Village Trades

Village Trades is a Heirloom addon for making equipment, remedies and arrows at
workstations. MMOItems supplies the finished items, their stats, sockets and
abilities. MythicLib supplies the native skills and mana integration.

!!! warning "Unpublished candidate"
    These pages describe **1.0.0-rc.1**, prepared for local review. A publicly
    supported minimum Core version is **pending**. Use the exact paired Core and
    addon builds in the candidate manifest. This page does not announce a release.

## The workshop

- **Smithery:** craft a cold equipment blank, heat it in the Oven, work it on an
  anvil, reheat as needed and quench it. Workmanship determines the finished grade.
- **Woodworking:** place logs and fittings on a Fletching Table, shape the wood
  with a hatchet, then finish it with Honeycomb. Fittings stay beside the work
  until finishing.
- **Apothecary:** cultivate herbs and use the Boiling Pot and Mixing Bowl for
  health, mana and damage-bonus preparations.
- **Fletching:** combine a head, shaft and fletching on the bench. An optional
  Lingering Potion adds its native tipped-arrow effects.

The collection includes equipment for Steel and Mithral progression, native
socket runes, an upgrade compound and a Repair Kit. The [reference](reference.md)
lists the current products and counts directly from the candidate catalogue.
Workmanship variants and internal tongs appearances are not extra products.

## Start here

Server owners should follow [Setup](setup.md), including mana and resource-pack
configuration. Players can follow [Survival progression](survival.md) from the
bootstrap tools to their first equipment and herbs. Mithral deposits must first
be placed by an operator; this candidate has no natural ore generation.

The target is Paper 26.2 with Java 25. Heirloom, MMOItems and MythicLib are
required; other Heirloom addons are optional. The included pack is optional for
joining, but players must accept it for woodworking. Optional PacketEvents 2.13.0
also enables custom nocked/flying arrow views and private tutorial scenes.

Automated checks and player confirmation are recorded separately in the
candidate's `docs/RELEASE-CANDIDATE.md`. Inspect its exact build hashes before
applying those results to an installation.
