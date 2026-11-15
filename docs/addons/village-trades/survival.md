# Village Trades survival progression

!!! warning "Candidate gameplay guide"
    These instructions describe unpublished **1.0.0-rc.1** with its exact paired
    Core build. Public Core compatibility is **pending**. The server owner must
    complete [setup](setup.md), including provider templates and mana.

## First tools and Steel

Craft a Basic Smith's Hammer with two Cobblestone and two Sticks, and Smith's
Tongs with two Iron Ingots and one Iron Nugget. Use these crafting-table layouts;
a dot means an empty slot:

| Tool | Rows, top to bottom |
| --- | --- |
| Basic Smith's Hammer | `CC.` / `.S.` / `.S.` |
| Smith's Tongs | `I.I` / `.N.` / `...` |

Build an [Oven](../../stations/oven.md) from a stone pressure plate on a smoker.
Cook **two Raw Iron and one Coal into three Steel**, taking 240 loaded ticks
(12 seconds at 20 TPS). Charcoal and ordinary Iron Ingots are not substitutes.

Steel is a native MMOItem. Use it to craft equipment blanks at the crafting table.
A first Hatchet Blank uses `BB.` / `BS.` / `...`; a Shortsword Blank uses
`.B.` / `.B.` / `.S.`. Here `B` is Steel and `S` is a Stick. Browse other exact
grids and grade previews through Heirloom's recipe browser.

## Forge the hatchet

1. Put an anvil on a stripped log and activate it with the Basic Smith's Hammer.
2. Place the cold blank in the Oven. Use tongs to take it at the desired heat and
   carry it to an empty smithing anvil.
3. Hammer, watching the heat gauge. The green temperature band gives better strike
   quality. Accepted blows use heat; reheat without losing progress as needed.
4. After 24 accepted blows, heat the shaped piece as needed and quench it with
   tongs in an unheated water cauldron. This consumes one water level.
5. Left-click the cauldron to collect the saved finished item.

The one-second hammer cooldown is shared across hammers and workpieces. Hold tongs
in the offhand and a hammer in the main hand to move and work without switching.
One player can carry one piece, while other pieces rest independently on stations.
The workmanship grade combines accepted strike temperature, quench heat and the
hammer contributions actually used.

## Shape a bow or staff

The Woodworking Bench is a Fletching Table. Accept the server pack so its workpiece
is visible. Deposit exact ingredients in any order, then left-click the wood with
a Village Trades hatchet. The first chop starts the recipe and counts as a stroke.

| Product | Ingredients before shaping |
| --- | --- |
| Village Bow | 3 Oak Logs + 3 String |
| Bramble Bow | 3 Oak Logs + 3 String + Rowan Sprig |
| Carved Staff | 2 Oak Logs + Amethyst Shard |
| Doom Staff | 2 Oak Logs + Amethyst Shard + Mithral + Soul Sand |
| Rainbow Staff | 2 Oak Logs + Amethyst Shard + Mithral + Quartz |

Only the logs become the workpiece. Fittings stay beside the wood until finishing.
Chop the visible side and let the hatchet's native attack recovery finish between
strokes. Broad hits anywhere on the visible wood work; there is no precise-line
aiming test. A better hatchet removes more work and improves workmanship. Pausing
has no penalty, and one bar tracks the complete shaping process.

Right-click the shaped piece with one Honeycomb to finish it, then left-click to
collect. Before waxing, owner sneak-right-click with an empty hand recovers the
paid ingredients. After waxing, recovery returns only the saved finished item.

## Make arrows

On the same bench, deposit one head, one shaft and one fletching. The first hatchet
chop starts a four-stroke batch that produces six arrows. An optional Lingering
Potion adds its native effects. Each batch has a 50% chance to consume that potion;
otherwise the exact potion returns. There is no additional bottle return.

- Heads: Flint, Iron Ingot, TNT or Glowstone Dust.
- Shafts: Stick, Bamboo, Bone, Blaze Rod or Breeze Rod.
- Fletching: Feather, Paper, Phantom Membrane or Amethyst Shard.

Phantom Membrane gives zero gravity. Amethyst fletching locks one visible target
near the aimed direction at launch and steers gently, without switching targets
or turning through walls. Custom nocked/flying appearances need the accepted pack
and PacketEvents; the original native arrow still controls flight and damage.

## Grow herbs and brew

Discover Normal herbs by breaking Short Grass in Survival. Thyme has a 1% chance
in Plains/Meadow; Lemon Balm in Forest/Birch Forest; Comfrey in Swamp/Mangrove
Swamp. Natural Oak/Birch Leaves have a 2% chance to drop Rowan Sprig. Persistent
player-placed leaves are excluded. Normal protection and acquisition settings apply.

Plant Thyme, Lemon Balm or Comfrey directly on Grass Blocks or Farmland. All six
grades can be planted. Base growth is six minutes with 20% variance; harvest
one or two herbs and the plant automatically regrows. A harvest has a 10% chance
to improve one grade, capped at Perfect. Regrowth retains the planted grade;
replant a better herb to improve the plant permanently. Rowan is gathered only.

Start with a Honey Bottle and Thyme in the [Boiling Pot](../../stations/boiling-pot.md)
for a Small Health Potion. A Glass Bottle, Sugar and Lemon Balm make a Small Mana
Potion. Comfrey and Paper in the [Mixing Bowl](../../stations/mixing-bowl.md) make
a poultice. Larger potions and damage tonics build on the same ingredients.
Mana restoration requires the server's configured mana pool.

## Mithral and equipment care

An operator first places a bottom Stone Slab, looks at it within five blocks and
runs `/hl deposits place VT_MITHRAL_DEPOSIT`. `/hl deposits inspect` shows its
state; `/hl deposits remove` unregisters it and leaves the slab. This candidate
has no natural deposit generation.

Mine the registered slab in Survival with an Iron, Diamond or Netherite Pickaxe.
Each completed vanilla mining cycle yields one Raw Mithral and uses normal tool
durability. Five cycles exhaust the deposit; it replenishes after 15 real minutes,
including offline time. Protection denial or unavailable rewards consume nothing.
Cook **one Raw Mithral and one Netherite Scrap into one Mithral** in the Oven,
taking 240 loaded ticks. Use Mithral for the Doom and Angel equipment preparations.

Runes use native uncoloured sockets. Tempering Compound upgrades the ordinary
Iron Shortsword up to three times; special weapons do not accept it. Unbinding Wax
removes and returns one socketed rune. Apply these native consumables to equipment
in your inventory rather than using a workstation to socket or upgrade it.

Make a Repair Kit from Steel, Leather and String in the Mixing Bowl, taking 80
ticks. Apply it from the cursor to damaged equipment to restore up to 60 durability.
It retains the existing item and its sockets/upgrades. Other packs' custom-durability
repair paths can have different cancellation behavior; consult the supplied
integration guide before using a kit on valuable equipment from another pack.
