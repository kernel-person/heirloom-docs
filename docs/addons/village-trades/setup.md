# Village Trades setup

!!! warning "Candidate setup only"
    This guide describes unpublished **1.0.0-rc.1**. The public minimum Core
    version is **pending**. Install the candidate's exact paired Core and addon
    jars, verified against `manifest.yml`; an older Core with the same version
    label is not sufficient.

## Requirements

Use Paper 26.2 and Java 25. Obtain MMOItems and MythicLib separately from their
publishers. The inspected provider builds are MMOItems 6.10.1-SNAPSHOT and
MythicLib 1.7.1-SNAPSHOT; their exact hashes are in the archive's `docs/INSTALL.md`.
A matching snapshot label alone does not identify a tested binary.

Other Heirloom addons are optional. The native skills do not require MythicMobs.
Optional PacketEvents 2.13.0 supplies custom nocked/flying arrow views and private
tutorial scenes. Without it, arrow mechanics still work with native visuals.

## Install on a test copy first

1. Stop the server and make a consistent backup of its world, inventories, jars,
   provider settings, resource pack and runtime journals.
2. Install the paired Core and compatible providers. Start them once to create
   their default configuration, then stop before merging Village Trades content.
3. From the extracted candidate folder, preview the merge helper's changes:
   `python3 tools/install.py --server /absolute/server`. The helper needs Python 3
   and PyYAML 6 on macOS/Linux. It does not install jars.
4. Apply with the same command plus `--apply`. It backs up destination files,
   rejects conflicting keys and checks that the server is stopped. On Windows,
   use the manual merge instructions and destination table in the archive.
5. Add the matching Village Trades jar to `plugins/`, configure mana and pack
   delivery below, then restart. Remove a superseded copy of the same addon jar
   so two versions cannot load together.

Never replace a complete MMOItems or MythicLib YAML file with a fragment.
Merge the supplied root definitions into their corresponding files and preserve
unrelated content. Keep the helper, fragments and defaults in their supplied
relative directories. Do not copy a default over `workshop.json`.

The helper's backup is a configuration backup. It does not replace the complete
world/player/journal backup needed to recover gameplay state. Unknown or pending
transactions need investigation, not deletion to force the installer through.

## Mana

Preserve the server's existing configured mana provider. For a standalone setup
without another mana system, edit these keys in the existing MythicLib files:

```yaml
# plugins/MythicLib/config.yml
mana-plugin: MYTHICLIB
```

```yaml
# plugins/MythicLib/stats.yml, inside its existing base-stat-value mapping
base-stat-value:
  MAX_MANA: 100
  MANA_REGENERATION: 1
```

Preserve other base stats. The helper diagnoses this choice without changing it.
After restart, verify an actual staff cast and Mana Potion restoration. A
configured value or present jar is not proof that the provider enabled.

## Resource pack

Serve `resourcepack/Village-Trades-resourcepack.zip` through a direct ZIP URL.
Use its generated SHA-1 from `resourcepack/manifest.json` in
`server.properties`'s `resource-pack-sha1`. Set `resource-pack` to the direct URL.
Do not serve the server directory or reuse an old hash for changed bytes.

Players may join with `require-resource-pack=false`, but woodworking requires
acceptance. Keep `server.properties`'s `resource-pack-id` equal to
`woodworking.resource-pack-id` in `plugins/HeirloomVillageTrades/config.yml`.
The supplied UUID is `c86733c5-53a1-4907-803f-c3bda293d419`; if changing it, update
both settings. An accepted pack with a mismatched UUID will not unlock woodworking.
MMOItems does not build or distribute the pack.

## First checks and later updates

Check startup for missing `VT_` references, open the recipe browser and follow the
[first survival steps](survival.md). Use `/vtrades integrations` to inspect native
integration modes. A favorable diagnostic is not a gameplay acceptance result.

For item-template changes, run `/mi reload` followed by `/hl reload`. Restart for
scripts, workshop settings or jar changes. Never use Bukkit `/reload`. Existing
inventory items retain their saved provider data; a template reload does not
regenerate them.

The tested optional baseline includes mcMMO 2.3.002 and MythicMobs 5.13.0. Current
TNT splash preserves shooter ownership and passes per-target damage cancellation;
it is not disabled merely because those plugins are installed. Validate your own
region, faction and combat plugins. Homing is not a universal party/faction filter,
and unknown mcMMO versions use the conservative native recovery path.

Keep the matched jars, manifest and acceptance receipt together. For rollback or
removal, follow the archive's `docs/ROLLBACK.md`: recover paid work, unregister
resources while definitions are available, and remove only exact owned keys.
Existing equipment may still depend on its MMOItems definitions.
