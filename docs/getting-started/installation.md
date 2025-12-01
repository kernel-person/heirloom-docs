# 📦 Installation

Getting Heirloom running on your server is quick and painless. Follow this guide to have your players cooking in no time!

***

## Requirements

Before installing Heirloom, make sure your server meets these requirements:

| Requirement | Version |
|-------------|---------|
| Minecraft | 1.21 or higher |
| Server Software | Paper, Spigot, or compatible forks |
| Java | 21 or higher |

{% hint style="warning" %}
**CraftBukkit is not supported.** Please use Paper or Spigot for the best experience.
{% endhint %}

***

## Installation Steps

### Step 1: Download the Plugin

Download the latest `Heirloom-1.0.0.jar` from:
- [GitHub Releases](https://github.com/rickardmartensson/heirloom/releases)
- [SpigotMC](https://www.spigotmc.org/) *(coming soon)*

### Step 2: Install the JAR File

1. Stop your Minecraft server
2. Navigate to your server's `plugins/` folder
3. Place `Heirloom-1.0.0.jar` into the folder
4. Start your server

```bash
# Example for Linux servers
cd /path/to/server
cp ~/Downloads/Heirloom-1.0.0.jar plugins/
./start.sh
```

### Step 3: Verify Installation

Once your server starts, verify Heirloom loaded correctly:

```
/hl help
```

You should see the Heirloom help menu appear!

{% hint style="success" %}
**Pro Tip:** Check your server console for `[Heirloom] Plugin enabled!` to confirm everything loaded correctly.
{% endhint %}

***

## First-Time Setup

Heirloom works out of the box with **zero configuration required!** 

All default configurations are bundled inside the plugin:

| File | Purpose |
|------|---------|
| `custom_items.json` | Defines all custom food items |
| `recipes.json` | Contains all cooking recipes |
| `crops.json` | Configures custom farmable crops |
| `dietary_properties.json` | Sets up dietary labels |

{% hint style="info" %}
**Want to customize?** Configuration files are automatically extracted to `plugins/Heirloom/` on first run. Edit them and use `/hl reload` to apply changes!
{% endhint %}

***

## Troubleshooting

<details>

<summary>🔴 Plugin won't load / "Plugin not found"</summary>

**Possible causes:**

1. **Wrong server version** - Make sure you're running Minecraft 1.21+
2. **Wrong Java version** - Heirloom requires Java 21
3. **Corrupt download** - Re-download the JAR file

**Check your Java version:**

```bash
java -version
```

</details>

<details>

<summary>🔴 Commands not working</summary>

**Possible causes:**

1. **Missing permissions** - Players need `heirloom.use` permission
2. **Plugin conflict** - Check for command conflicts with other plugins
3. **Incomplete load** - Check console for errors during startup

**Quick fix:** Try `/heirloom help` instead of `/hl help`

</details>

<details>

<summary>🔴 Custom textures not showing</summary>

Custom item textures require players to have:
- **Server resource pack** (automatic) OR
- A texture pack that supports custom model data

The plugin uses **player head textures** which work automatically in vanilla Minecraft!

</details>

***

## What's Next?

Now that Heirloom is installed, let's build your first cooking station!

{% content-ref url="quick-start.md" %}
[quick-start.md](quick-start.md)
{% endcontent-ref %}

