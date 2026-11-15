# Interactive station tutorials

Use `/hl tutorial` to choose a cooking lesson. A private scene appears in front of you with full-size blocks at your feet level: blocks assemble, ingredients and tools demonstrate the workflow, and glowing targets wait for your clicks. Only you see and interact with your scene.

## Installation

Install PacketEvents alongside Heirloom to enable tutorials, then restart the server. PacketEvents is optional: without it, Heirloom's cooking, crops, recipes and addons continue to work, and tutorial commands explain the missing dependency. A resource pack is not required.

Tutorials target PacketEvents 2.13.0 on Paper 1.21.11 and 26.2. Server-side verification covers serialized scenes and interactions; final client appearance and interaction feel remain user-run checks.

## Commands and controls

- `/hl tutorial` — browse available lessons and completed lessons.
- `/hl tutorial <lesson>` — start a lesson; use a short name such as `/hl tutorial oven`. Tab completion suggests available short names. Qualified IDs remain available when names are ambiguous.
- `/hl tutorial stop` — leave the current demonstration.
- `/hld tutorial` — browse the Distillery course, when Distillery is installed.

The Heirloom main menu also has a Tutorials card. The `heirloom.tutorial` permission is granted by default.

The catalogue uses native Minecraft sprite icons beside lesson names. Follow the short action-bar instruction: **Left-click (punch)** or **Right-click**, then the action. After eight seconds waiting for a click, a small translated prompt appears above the target. It disappears when you act; timed processing does not show a click prompt. Explanations appear in one caption panel above the scene; longer current-step text pages while the demonstration continues, without delaying the next action. Serving counts update to the latest value. The station-styled progress bar stays visible during work, with the same sweep and shimmer formatting as gameplay. Click guidance remains in the caption while the bar occupies the action row. Chat controls let you go to the previous chapter, replay the current chapter or exit. Left-click or right-click the final emerald to mark a lesson complete; the confirmation is simply “Tutorial complete!”

Start in a clear, loaded area with room for the whole station and space to approach its glowing targets. Every lesson uses the same 1:1 block scale; large stations do not shrink to fit. Pots, stomping tubs and fermenters rest at ground level, with their heat or support shown beneath the floor in a cutaway visible only to you. Use ordinary solid, full-block ground for these lessons. The cutaway preserves floor collision and restores your normal view when the scene closes; it does not remove world blocks. No new configuration is needed.

The scene stays where it began. Move closer when a target is outside normal interaction reach; clicks are checked from your current position. Moving more than 16 blocks from the starting position ends the lesson. Teleporting, changing worlds, dying, logging out, a successful reload or disabling the tutorial dependency also closes the scene. You can start again at any time.

## Lessons

Core lessons cover the Cutting Board, Mixing Bowl, Oven, Frying Pan and Boiling Pot. Specialized lessons become available with the corresponding active content: Barista Machine, Juicer, Mixology Table and Farmhouse Press. Aging Rack lessons belong to Distillery; Core does not list an aging course.

Distillery lessons cover building and using the Stomping Tub, fermentation cauldron and still, followed by grain preparation, sparkling wine and cellar aging. They also explain station storage, unloaded processing and recovery.

Lessons use the server's current recipes, ingredient amounts and configured times. If an example recipe is unavailable, the base station lesson still teaches construction and controls. Long waits are labelled as accelerated demonstrations and show the real configured duration.

### Practise aging in the barrel

Use `/hl tutorial aging` or `/hld tutorial aging` with Distillery installed. After building the barrel on scaffolding, right-click it to open a practice barrel with the normal 27-slot layout. Move the supplied bottles and planks from the lower inventory into the barrel, then remove the extra wood when prompted. The lesson demonstrates maturation with an accelerated wait and lets you collect the developed bottle.

The lower inventory and cursor in this lesson contain temporary practice items. Your real belongings are preserved, and practice items cannot be kept. Closing the practice window exits the lesson; replay starts with fresh practice items. Read the instruction item in the practice inventory for the current step.

The lesson also explains cellar climate. Ordinary Forest and Taiga biomes provide cool, humid conditions. Nearby water, ice and walls do not change the biome temperature or humidity. You can brew in any biome; ingredients and processing determine the drink family. Wine still ages in other climates; its preferred climate helps craftsmanship. See [Cellar Aging](../addons/distillery/cellar-aging.md) for the rack report and maturation routes.

## Preview behaviour

Station previews reuse production placement, animation, particle and progress helpers. The Oven course shows the required smoker and stone pressure plate, followed by an optional brick shell built one block at a time and the rear fire used during baking. Each required part is placed by a click, ingredients travel into the station, and collected items jump upward and toward you. The chopping sword and mixing shovel stay close above the actual work surface: the sword moves down toward the board, and the shovel follows a tight stirring motion over the bowl. Forward steps retain the existing station displays; Replay and Previous reconstruct their checkpoint. Items keep their station orientation when you look around.

Tutorial blocks, items, click targets and practice inventories are private displays. They do not build real stations, spend ingredients, grant food, change brewing history or start real timers. Tutorial completion IDs are the only saved gameplay change.

A failed configuration reload retains the prior lesson registrations. A successful reload closes active scenes so the next lesson uses current definitions. Scenes belonging to removed addons close safely.

Tutorial narration has priority over Heirloom's background drunkenness reminders until the lesson ends. Other plugins may still show their own action-bar messages; simultaneous tutorials from different plugins are not coordinated.

Tutorial copy is bundled for all 26 supported server locales. Choose the usual server `locale`; administrator keys in Core or addon `lang/<locale>.yml` override the bundled text. Most existing instructions, controls and progress labels have machine-authored translations, which have not had a full native-speaker review. The new barrel-practice instructions and rack-report text currently use English fallbacks in non-English locales. Custom item names retain their configured names, and dynamic vanilla item names passed into a sentence may also appear in English.

Native sprite components use the Minecraft text API introduced in 1.21.9; no icon resource pack is needed. The supported server baseline remains Paper 1.21.11. See [Adventure's sprite component API](https://jd.advntr.dev/api/4.25.0/net/kyori/adventure/text/object/ObjectContents.html).
