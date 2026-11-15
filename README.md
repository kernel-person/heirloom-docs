# Heirloom Docs

Public user and admin documentation for Heirloom Core, Distillery, Cafe,
Heirloom Mixology and food packs, with additional Pasture reference material.

## Local Preview

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

Open `http://127.0.0.1:8000/`.

## Regenerate Source Reference

The wiki generator reads bundled Core, Cafe, Pasture and Orchard JSON, Distillery's grape definitions and beverage catalog, and every release content
pack under `../foodplugin/packs/*/content/`. It rebuilds the item reference,
recipe pages, content-pack pages, navigation, and icon manifest together.

Set `HEIRLOOM_PLUGIN_ROOT` to the verified plugin release checkout when generating
release documentation. Version fields come from the module POMs; pack versions,
requirements and counts come from their catalogs and content JSON. The canonical
`packs/` directory takes precedence over the legacy explicit American release
fallback. Other worktrees and draft pack directories are not added to discovery,
and provider-preview approval is unchanged.

Wiki-owned tutorial guides and the separately maintained Pasture guide live in
`pages/`. Generation copies them into `docs/` unchanged, preserving their current
instructions when a plugin release checkout contains older prose. Edit those
page sources directly; generated item and recipe references still come from the
selected plugin resources.

```bash
export HEIRLOOM_PLUGIN_ROOT=/path/to/verified/heirloom-release
.venv/bin/python tools/generate_reference_pages.py --use-visual-pack-icons
.venv/bin/python tools/check_content_pack_generation.py
.venv/bin/python tools/check_icon_modes.py
.venv/bin/python tools/check_recipe_slot_badges.py
.venv/bin/python tools/check_orchard_generation.py
.venv/bin/python tools/check_pasture_generation.py
.venv/bin/python tools/check_distillery_generation.py
.venv/bin/mkdocs build --strict
```

Each content pack must use matching `pack` metadata in its item and recipe JSON.
Conflicting metadata stops generation instead of publishing mixed pack data.

Mixology's catalog describes its Cafe/Distillery menu modes. The generator checks
those item and recipe counts against the authoritative source definitions before
writing the mode table, Mixology station page and recipe references. Source recipe
indexes include conditional definitions and label their availability; an index
count is not the number enabled on every server.

Core's JSON directly declares optional Mixology ingredient choices in Jam, Ice
Cream and Taco. The generator reads those options and flavour rules through the
normal recipe reference path. They remain Core recipes, outside addon counts;
unregistered item choices are unavailable in game.

Distillery's Drink Families and Cellar Aging tables come directly from
`heirloom-distillery/src/main/resources/beverage-affinities.json`. Its generation
check changes catalog timings, names, preferred distillation runs and finishing
requirements in memory to verify those references follow the rules rather than
a copied table. The in-game guide uses the server's effective catalog. Grape item
and crop discovery reads `custom_items-distillery.json` and `crops-distillery.json`
from Distillery's resource directory and attributes all five varieties to that addon.

The authoritative local source is this working directory, even when it has no
Git metadata. Local generation and a strict build do not publish the site.

## Unpublished Village Trades candidate pages

The authored candidate guides live in `pages/addons/village-trades/` and remain
separate from released Core item/recipe indexes. Their nav entry is explicitly
marked candidate. Public Core compatibility is pending; these pages are local
preparation and do not announce a release.

The reference table comes from the verified addon's generated catalogue:

```bash
.venv/bin/python tools/generate_village_trades_reference.py --addon-root /path/to/verified/heirloom-village-trades
.venv/bin/python tools/generate_village_trades_reference.py --addon-root /path/to/verified/heirloom-village-trades --check
.venv/bin/python tools/check_village_trades_generation.py --addon-root /path/to/verified/heirloom-village-trades
```

Edit the overview, setup and survival sources in `pages/`. Normal wiki generation
copies these guides into `docs/`; refresh the candidate reference separately when
its catalogue changes. Before any eventual publication, assign the supported Core
version and review the candidate notices against the approved release receipt.

## Publish

The included GitHub Actions workflow builds the MkDocs site and publishes it to
GitHub Pages from the `gh-pages` branch.

Publish by cloning `git@github.com:kernel-person/heirloom-docs.git` into a temporary
directory, synchronizing this verified source into the clone, committing, and
pushing. Exclude `.venv/`, `site/`, caches and local operating-system files.
Every wiki Git network operation must use the repository's deploy key:

```bash
GIT_SSH_COMMAND='ssh -F /dev/null -i /Users/rickardmartensson/.ssh/github_kernel_heirloom_docs -o IdentitiesOnly=yes' git clone git@github.com:kernel-person/heirloom-docs.git /path/to/temporary-clone
```

After pushing, verify the GitHub Actions deployment and the public overview,
source logos, representative icons and recipe links before reporting publication.

After the first successful workflow run, enable Pages in the repository
settings:

- Source: Deploy from branch
- Branch: `gh-pages`
- Folder: `/`

Then use the published URL in public plugin listings and any in-game guide link:

```yml
guide-url: "https://kernel-person.github.io/heirloom-docs/"
```
