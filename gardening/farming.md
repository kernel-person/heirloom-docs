# 🌱 Farming Guide

Heirloom adds a dynamic **gardening system** with custom crops that grow visually over time. Grow tomatoes on vines, corn in tall stalks, lettuce in garden beds, and rice in water paddies!

***

## Overview

The gardening system features:

- 🌿 **4 plant types** with unique growing behaviors
- 📈 **Visual growth stages** with scaling animations
- 🎲 **Variable harvest drops** with Fortune bonus
- 🔄 **Auto-replanting** for continuous farming
- ✨ **Particle effects** and growth sounds

{% hint style="info" %}
**Custom crops use display entities** to show unique textures. They appear as floating items that scale up as they grow!
{% endhint %}

***

## Available Crops

| Crop | Type | Growth Time | Drops |
|------|------|-------------|-------|
| 🥬 **Lettuce** | Short Plant | 5 min | 1-3 Lettuce |
| 🌽 **Corn** | Tall Plant | 8 min | 1-2 Corn |
| 🍅 **Tomato** | Vine | 7 min | 1-2 Tomato |
| 🍚 **Rice** | Aquatic | 6 min | 2-4 Rice |

***

## Plant Types

### 🌿 Short Plants (Lettuce)

Small, ground-level crops that grow in garden beds.

**Planting requirements:**
- Plant on: Grass Block, Dirt, Coarse Dirt, Podzol, or Rooted Dirt
- No water required
- Needs open sky above (for best growth)

**How to plant:**
1. Hold **Lettuce** in your hand
2. **Right-click** a valid soil block
3. Watch the small plant appear!

![Lettuce Farm](../.gitbook/assets/lettuce-farm.png)

{% hint style="success" %}
**Pro Tip:** Lettuce grows quickly and replants automatically—perfect for beginners!
{% endhint %}

### 🌾 Tall Plants (Corn)

Towering crops that grow into impressive stalks.

**Planting requirements:**
- Plant on: Grass Block, Dirt, Coarse Dirt, Podzol, or Rooted Dirt
- No water required
- Needs 2 blocks of vertical space

**How to plant:**
1. Hold **Corn** in your hand
2. **Right-click** a valid soil block
3. Watch the corn stalk grow tall!

![Corn Farm](../.gitbook/assets/corn-farm.png)

{% hint style="success" %}
**Pro Tip:** Plant corn in rows with 1-block spacing for that authentic farm aesthetic!
{% endhint %}

### 🍇 Vines (Tomato)

Climbing plants that attach to walls and can spread upward.

**Planting requirements:**
- Plant on: Stone, Cobblestone, Stone Bricks, Deepslate, Bricks, or any Plank type
- Must be placed on a **wall face** (vertical surface)
- Can spread upward naturally!

**How to plant:**
1. Hold **Tomato** in your hand
2. **Right-click** a valid wall block (the side of a block)
3. Watch tomatoes grow on the wall!

**Spreading:**
Tomato vines can **spread upward** over time:
- 8% chance per growth check
- Maximum chain length: 4 vines
- Creates a beautiful vertical garden!

![Tomato Vine](../.gitbook/assets/tomato-vine.png)

{% hint style="success" %}
**Pro Tip:** Build a tall stone wall and plant tomatoes at the bottom—they'll spread up and create a living wall!
{% endhint %}

### 💧 Aquatic Plants (Rice)

Water-loving crops that grow in flooded paddies.

**Planting requirements:**
- Plant on: Dirt, Clay, Mud, Gravel, or Sand
- **Requires water directly above** the soil block
- The plant peeks above the water surface

**How to plant:**
1. Create a flooded area (1 block deep water over soil)
2. Hold **Rice** in your hand
3. **Right-click** the soil block underwater
4. Rice will grow up through the water!

![Rice Paddy](../.gitbook/assets/rice-paddy.png)

{% hint style="success" %}
**Pro Tip:** Create terraced rice paddies on a hillside using stairs and slabs to control water flow!
{% endhint %}

***

## Growth System

### Growth Stages

All crops go through **4-5 growth stages**:

```
Stage 1    Stage 2    Stage 3    Stage 4    Mature!
  🌱    →    🌿    →    🌿    →    🌿    →    🥬
 (tiny)    (small)   (medium)   (large)    (ready!)
```

Visual scaling happens automatically:
- **Start scale:** 0.2-0.3 (tiny seedling)
- **End scale:** 0.6-1.0 (full-grown plant)

### Growth Time

Each crop has a **base growth time** with variance:

| Crop | Base Time | Variance | Actual Range |
|------|-----------|----------|--------------|
| Lettuce | 5 min | ±20% | 4-6 minutes |
| Corn | 8 min | ±25% | 6-10 minutes |
| Tomato | 7 min | ±20% | 5.6-8.4 minutes |
| Rice | 6 min | ±15% | 5.1-6.9 minutes |

{% hint style="info" %}
**Growth variance** adds natural randomness—not all crops mature at exactly the same time!
{% endhint %}

***

## Harvesting

### How to Harvest

1. Wait for the crop to fully mature (check the visual size)
2. **Right-click** the mature plant
3. Collect your drops!

### Harvest Drops

| Crop | Base Drops | Fortune Bonus |
|------|------------|---------------|
| Lettuce | 1-3 | +1 (15% chance) |
| Corn | 1-2 | — |
| Tomato | 1-2 | — |
| Rice | 2-4 | — |

{% hint style="success" %}
**Fortune enchantment** increases drop chances on supported crops!
{% endhint %}

### Auto-Replanting

All crops automatically replant after harvest:

```
Harvest → Drops collected → Plant resets to Stage 1 → Grows again
```

This means you only need to plant once for continuous harvests!

***

## Farm Designs

{% tabs %}
{% tab title="Simple Garden" %}

A basic 9x9 garden with all crop types:

```
┌─────────────────────────┐
│  🌿  🌿  🌿 │ Wall      │
│  🌿  🌿  🌿 │ 🍅 🍅 🍅  │
│  🌿  🌿  🌿 │ 🍅 🍅 🍅  │
│─────────────│───────────│
│  🌽  🌽  🌽 │ 💧💧💧    │
│  🌽  🌽  🌽 │ 🍚🍚🍚    │
│  🌽  🌽  🌽 │ 💧💧💧    │
└─────────────────────────┘
  Lettuce/Corn    Tomato/Rice
```

{% endtab %}

{% tab title="Greenhouse" %}

An enclosed glass greenhouse:

1. Build a glass structure (any size)
2. Use **farmland** or dirt inside
3. Add water channels for rice section
4. Include a wall section for tomatoes

Benefits:
- Looks great!
- Protected from mobs
- Easy to navigate

{% endtab %}

{% tab title="Rice Terrace" %}

Terraced rice paddies on a hill:

```
Level 4:  💧💧💧 →
Level 3:  💧💧💧💧 →
Level 2:  💧💧💧💧💧 →
Level 1:  💧💧💧💧💧💧 →
          (water flows down)
```

Use stairs/slabs to control water flow between levels.

{% endtab %}

{% tab title="Vertical Garden" %}

A tomato wall garden:

```
     ┌───────────┐
     │ 🍅 🍅 🍅  │
     │ 🍅 🍅 🍅  │
     │ 🍅 🍅 🍅  │
     │ 🍅 🍅 🍅  │
     └───────────┘
     Stone Wall (4 high)
```

Tomatoes spread upward naturally!

{% endtab %}
{% endtabs %}

***

## Growth Settings

Server admins can configure growth behavior in `crops.json`:

```json
{
  "settings": {
    "growth_check_radius": 32,
    "visual_update_interval_ticks": 40,
    "enable_particles": true,
    "enable_growth_sounds": true
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `growth_check_radius` | 32 | Blocks around player to check for growing crops |
| `visual_update_interval_ticks` | 40 | How often to update visual size (40 = 2 seconds) |
| `enable_particles` | true | Show growth particles |
| `enable_growth_sounds` | true | Play growth sounds |

{% hint style="warning" %}
**Performance Note:** Increasing `growth_check_radius` beyond 64 blocks may impact server performance with many crops.
{% endhint %}

***

## What's Next?

{% content-ref url="custom-crops.md" %}
[custom-crops.md](custom-crops.md)
{% endcontent-ref %}

Learn how to configure and customize crops!

