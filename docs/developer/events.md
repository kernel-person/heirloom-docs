# Bukkit Events

Heirloom fires five Bukkit events under `ke.ric.api.events` so addons and external plugins can react to food consumption, placed feasts, station crafting, crop harvesting, and `/hl give` grants.

## Event Summary

| Event Class | Cancellable | Primary Data |
| --- | --- | --- |
| `HeirloomFoodConsumedEvent` | Yes | `getPlayer()`, `getItem()`, `getCustomItemId()`, `isCustomItem()`, `get/setHungerRestored()`, `get/setSaturationRestored()` |
| `HeirloomPlacedFoodConsumedEvent` | No (`final`) | `getPlayer()`, `getItem()`, `getCustomItemId()` |
| `HeirloomItemCraftedEvent` | Yes | `getPlayer()`, `getStation()`, `getRecipeId()`, `get/setResult()` |
| `HeirloomCropHarvestedEvent` | Yes | `getPlayer()`, `getLocation()`, `getCropDefinition()`, `getCropId()`, `get/setDrops()`, `addDrop()`, `willReplant()`, `setWillReplant()` |
| `HeirloomAdminItemEvent` | Yes (`final`) | `getPlayer()`, `getItemId()`, `getItem()` |

## Consuming Food

### `HeirloomFoodConsumedEvent`

Fired after vanilla `PlayerItemConsumeEvent` when a player eats or drinks a Heirloom food item (or vanilla food handled by Heirloom). Modify hunger/saturation restoration or cancel consumption before Heirloom applies effects.

### `HeirloomPlacedFoodConsumedEvent`

Fired after a player eats one serving from a placed world food or feast (non-cancellable). The attached `getItem()` stack preserves the placed block's original `FoodFactsV2` metadata, making this the right hook for dietary/beliefs tracking on placed servings alongside `HeirloomFoodConsumedEvent` / `PlayerItemConsumeEvent`.

```java
import ke.ric.api.HeirloomAPI;
import ke.ric.api.events.HeirloomFoodConsumedEvent;
import ke.ric.api.events.HeirloomPlacedFoodConsumedEvent;
import ke.ric.api.food.FoodFactsV2;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.inventory.ItemStack;

public final class ConsumptionListener implements Listener {
    @EventHandler(ignoreCancelled = true)
    public void onFoodConsumed(HeirloomFoodConsumedEvent event) {
        if (event.isCustomItem() && "HONEY_CAKE".equals(event.getCustomItemId())) {
            event.setHungerRestored(event.getHungerRestored() + 2);
            event.setSaturationRestored(event.getSaturationRestored() + 1.5f);
        }
    }

    @EventHandler
    public void onPlacedServingConsumed(HeirloomPlacedFoodConsumedEvent event) {
        ItemStack serving = event.getItem();
        FoodFactsV2 facts = HeirloomAPI.getInstance().foodFactsV2(serving);
        // Inspect facts.categories() / facts.dietaryFacts() for this serving
    }
}
```

## Station Crafting

### `HeirloomItemCraftedEvent`

Fired when a player crafts a recipe at one of Heirloom's cooking stations (`ke.ric.cooking.CookingStation`):

`OVEN`, `BOILING_POT`, `MIXING_BOWL`, `CUTTING_BOARD`, `FRYING_PAN`, `BARISTA_MACHINE`, `MIXOLOGY_TABLE`, `JUICER`, `FARMHOUSE_PRESS`

Cancelling prevents the result from being awarded; `setResult(ItemStack)` swaps the output item (Core updates `FoodFactsV2` lineage after approved result replacements).

```java
import ke.ric.api.events.HeirloomItemCraftedEvent;
import ke.ric.cooking.CookingStation;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;

public final class CraftListener implements Listener {
    @EventHandler(ignoreCancelled = true)
    public void onCraft(HeirloomItemCraftedEvent event) {
        if (event.getStation() == CookingStation.OVEN && "APPLE_PIE".equals(event.getRecipeId())) {
            // Adjust or log crafted result
        }
    }
}
```

## Crop Harvesting

### `HeirloomCropHarvestedEvent`

Fired when a player harvests a mature Heirloom custom crop. Add bonus drops with `addDrop(ItemStack)`, replace drops via `setDrops(List<ItemStack>)`, toggle auto-replanting via `setWillReplant(boolean)`, or cancel the harvest.

```java
import ke.ric.api.events.HeirloomCropHarvestedEvent;
import org.bukkit.Material;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.inventory.ItemStack;

public final class HarvestListener implements Listener {
    @EventHandler(ignoreCancelled = true)
    public void onCropHarvested(HeirloomCropHarvestedEvent event) {
        if ("TOMATO".equals(event.getCropId())) {
            event.addDrop(new ItemStack(Material.STICK, 1));
            event.setWillReplant(true);
        }
    }
}
```

## Admin Item Grants

### `HeirloomAdminItemEvent`

Fired before delivering a fresh stack granted through `/hl give` or the admin cheat GUI (never fired for recipe browser previews, existing inventories, or normal crafting). Addons that initialize playable item metadata on spawned samples should listen here and avoid cancelling legitimate grants unless policy forbids the item.
