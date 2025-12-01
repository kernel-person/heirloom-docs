# 🔐 Permissions

Heirloom uses a simple permission system to control access to features. This guide covers all available permissions and recommended setups.

***

## Permission Overview

| Permission | Default | Description |
|------------|---------|-------------|
| `heirloom.use` | ✅ All | Basic plugin access |
| `heirloom.cookbook` | ✅ All | Get a cookbook item |
| `heirloom.recipes` | ✅ All | Browse recipes GUI |
| `heirloom.give` | ❌ OP | Give custom items |
| `heirloom.reload` | ❌ OP | Reload configuration |
| `heirloom.admin` | ❌ OP | All permissions |

{% hint style="info" %}
**Default: All** means all players have this permission by default.
**Default: OP** means only server operators have this permission.
{% endhint %}

***

## Permission Details

### `heirloom.use`

**Default:** `true` (all players)

Base permission for using Heirloom features:
- Use cooking stations
- Grow and harvest custom crops
- Eat custom food items
- Use `/hl help` command
- Use `/hl list` command

{% hint style="success" %}
**Most servers won't need to change this.** All players can cook and farm by default!
{% endhint %}

---

### `heirloom.cookbook`

**Default:** `true` (all players)

Allows using the `/hl cookbook` command to receive a free cookbook item.

**Use cases for restricting:**
- Make cookbooks a rare or purchasable item
- Require players to craft/find cookbooks instead

---

### `heirloom.recipes`

**Default:** `true` (all players)

Allows using the `/hl recipes` command and the recipe browser GUI.

**Use cases for restricting:**
- Make recipe discovery part of gameplay progression
- Require players to "learn" recipes first

---

### `heirloom.give`

**Default:** `op` (operators only)

Allows using `/hl give` to spawn custom food items.

{% hint style="danger" %}
**Keep this restricted!** Giving items bypasses normal crafting progression.
{% endhint %}

**Use cases for granting:**
- Admin shops or reward systems
- Testing and debugging
- Creative mode servers

---

### `heirloom.reload`

**Default:** `op` (operators only)

Allows using `/hl reload` to reload all configurations.

{% hint style="warning" %}
**Server impact:** Reloading clears caches and re-indexes recipes. Not recommended for frequent use on production servers.
{% endhint %}

---

### `heirloom.admin`

**Default:** `op` (operators only)

Parent permission that grants **all** Heirloom permissions:

```yaml
heirloom.admin:
  children:
    heirloom.use: true
    heirloom.cookbook: true
    heirloom.recipes: true
    heirloom.give: true
    heirloom.reload: true
```

{% hint style="success" %}
**Pro Tip:** Grant `heirloom.admin` to trusted staff members instead of individual permissions!
{% endhint %}

***

## Permission Plugin Setup

{% tabs %}
{% tab title="LuckPerms" %}

**Grant to all players:**

```bash
/lp group default permission set heirloom.use true
/lp group default permission set heirloom.cookbook true
/lp group default permission set heirloom.recipes true
```

**Grant admin to staff:**

```bash
/lp group admin permission set heirloom.admin true
```

**Restrict cookbook command:**

```bash
/lp group default permission set heirloom.cookbook false
```

{% endtab %}

{% tab title="PermissionsEx" %}

Edit `permissions.yml`:

```yaml
groups:
  default:
    permissions:
      - heirloom.use
      - heirloom.cookbook
      - heirloom.recipes
  
  admin:
    permissions:
      - heirloom.admin
```

{% endtab %}

{% tab title="GroupManager" %}

Edit `groups.yml`:

```yaml
groups:
  default:
    permissions:
      - heirloom.use
      - heirloom.cookbook
      - heirloom.recipes
  
  admin:
    permissions:
      - heirloom.admin
```

{% endtab %}

{% tab title="Vanilla (OP)" %}

Without a permission plugin:
- **Non-OP players** can use basic features (cook, farm, browse)
- **OP players** can use admin commands (give, reload)

This is the default behavior!

{% endtab %}
{% endtabs %}

***

## Common Setups

### Default (Recommended)

Keep default permissions—all players can use all cooking features, only ops can admin.

### Progression Server

Restrict recipe browsing to encourage exploration:

```bash
# Remove recipe browser from default
/lp group default permission set heirloom.recipes false

# Grant to players who "unlock" it
/lp user <player> permission set heirloom.recipes true
```

### Economy Server

Restrict item spawning, allow shop owners to use give:

```bash
# Grant give permission to shop rank
/lp group shopowner permission set heirloom.give true
```

### Creative Server

Grant all permissions to everyone:

```bash
/lp group default permission set heirloom.admin true
```

***

## Troubleshooting

<details>

<summary>🔴 Player can't use cooking stations</summary>

**Check:** Does the player have `heirloom.use` permission?

```bash
/lp user <player> permission check heirloom.use
```

**Fix:** Grant the permission:

```bash
/lp group default permission set heirloom.use true
```

</details>

<details>

<summary>🔴 /hl give says "no permission"</summary>

**Expected:** This command requires `heirloom.give` (OP only by default).

**Fix for admins:**

```bash
/lp user <player> permission set heirloom.give true
```

Or grant full admin:

```bash
/lp user <player> permission set heirloom.admin true
```

</details>

<details>

<summary>🔴 Commands not showing in tab completion</summary>

Tab completion respects permissions. If a player can't see a command:
1. They don't have permission for it
2. This is intentional to avoid confusion

</details>

***

## What's Next?

{% content-ref url="configuration.md" %}
[configuration.md](configuration.md)
{% endcontent-ref %}

Learn about all configuration files!

