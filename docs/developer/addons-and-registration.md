# Addons & Content Registration

Heirloom manages addon lifetimes, owner-scoped registrations, and safe rollback transactions across `/hl reload` through `HeirloomAPI` and the `ke.ric.api.registration` facades.

## Registering & Reloading an Addon

Prefer the callback `registerAddon` overloads on `HeirloomAPI` so your plugin does not depend on cross-classloader interface timing. Pass an enable callback, plus optional reload and cleanup callbacks:

```java
import ke.ric.api.HeirloomAPI;
import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;
import org.bukkit.plugin.java.JavaPlugin;

public final class MyFoodAddon extends JavaPlugin {
    private static final String ADDON_ID = "my_food_addon";

    @Override
    public void onEnable() {
        Plugin heirloom = Bukkit.getPluginManager().getPlugin("Heirloom");
        if (heirloom == null || !heirloom.isEnabled()) {
            return;
        }
        HeirloomAPI api = HeirloomAPI.getInstance();
        if (api == null || !api.isReady()) {
            return;
        }

        api.registerAddon(
                ADDON_ID,
                getPluginMeta().getVersion(),
                this,
                this::registerContent,
                this::onHeirloomReload,
                this::onHeirloomDisable
        );
    }

    private void registerContent(HeirloomAPI api) {
        // Items, crops, recipes, aging, advancements, and guides registered here
        // are automatically tracked under ADDON_ID
    }

    private void onHeirloomReload() {
        reloadConfig();
    }

    private void onHeirloomDisable() {
        // Released when Heirloom unregisters this addon independently
    }
}
```

Available registration and lifecycle methods on `HeirloomAPI`:

- `registerAddon(String addonId, String version, Plugin owningPlugin, Consumer<HeirloomAPI> registrationCallback)`
- `registerAddon(..., Runnable reloadCallback)` / `registerAddon(..., Runnable reloadCallback, Runnable disableCallback)`
- `registerAddon(Plugin owningPlugin, HeirloomAddon addon)` — legacy interface variant (`getAddonId()`, `getVersion()`, `onEnable(HeirloomAPI)`, `onReload()`, `onDisable()`)
- `unregisterAddon(String addonId)` — removes the addon and all owner-scoped registrations
- `isAddonRegistered(String addonId)` / `getAddon(String addonId)`
- `registerReloadState(String addonId, Supplier<Runnable> snapshot)` — participates in `/hl reload` rollback if a reload fails partway through
- `withAddonRegistrationContext(String addonId, Runnable registration)` — executes deferred updates under an explicit addon owner context

## Registration Facades

Access each owner-scoped registry directly from `HeirloomAPI`:

| Facade | Method | Accepts in `register(...)` |
| --- | --- | --- |
| Items | `api.items()` | `ItemRegistration.ItemDefinitionBuilder` |
| Recipes | `api.recipes()` | `RecipeRegistration.AddonRecipeBuilder` |
| Crops | `api.crops()` | `CropRegistration.CropDefinitionBuilder` |
| Seed Acquisition | `api.seedAcquisition()` | `File` (`registerFromFile(File, String addonId)`) |
| Dietary Properties | `api.properties()` | `PropertyRegistration.PropertyDefinitionBuilder` |
| Advancements | `api.advancements()` | `AdvancementDefinition` record |
| Cellar / Rack Aging | `api.aging()` | `AgingDefinition` (`AgingDefinition.builder()...build()`) |
| Addon Cookbook Guides | `api.guides()` | `GuideDefinition` record |

!!! important "Do not call `.build()` inside `items()`, `recipes()`, `crops()`, or `properties().register(...)`"
    `api.items().register(...)`, `api.recipes().register(...)`, `api.crops().register(...)`, and `api.properties().register(...)` take the **builder directly**, not `.build()`. By contrast, `api.aging().register(...)`, `api.advancements().register(...)`, and `api.guides().register(...)` take constructed records (`AgingDefinition.builder()...build()`, `new AdvancementDefinition(...)`, `new GuideDefinition(...)`).

## Custom Items (`api.items()`)

Register items programmatically with `ItemRegistration.builder()` or load editable JSON definitions via `registerFromFile(File, defaultAddonId)`. You can also register custom ingredient recognizers or qualifiers so specialized items match Heirloom recipe inputs cleanly:

```java
import ke.ric.api.registration.ItemRegistration;
import org.bukkit.potion.PotionEffectType;

api.items().register(ItemRegistration.builder()
        .id("HONEY_GLAZED_APPLE")
        .name("Honey Glazed Apple")
        .texture("http://textures.minecraft.net/texture/...")
        .edible(true)
        .foodValue(6)
        .saturation(0.7f)
        .consumeSeconds(1.6f)
        .animation("EAT")
        .canAlwaysEat(false)
        .tags("SWEET", "FRUIT")
        .addEffect(PotionEffectType.REGENERATION, 100, 0, 1.0f));
```

Useful helpers on `ItemRegistration`: `isRegistered(id)`, `registeredIds(addonId)`, `registerIngredientRecognizer(addonId, customItemId, predicate)`, `registerIngredientQualifier(addonId, qualifierId, canonicalCustomItemId, matches, preview)`, `unregisterProgrammaticAddon(addonId)`.

## Custom Recipes (`api.recipes()`)

Create addon recipes under your addon category, register editable JSON catalogs (`registerFromFile`), suppress existing recipes with override strength (`suppress(addonId, recipeId, overrideStrength)`), or hook runtime output creation/decoration/eligibility:

```java
import ke.ric.api.registration.RecipeRegistration;
import ke.ric.cooking.data.RecipeItemRef;

api.recipes().register(RecipeRegistration.builder()
        .id("MYADDON_BREW_MEAD")
        .addonId("my_food_addon")
        .stationName("Fermenting Vat")
        .output(RecipeItemRef.customItem("GOLDEN_MEAD"), 1)
        .processingTimeSeconds(30)
        .addIngredient("HONEY_BOTTLE", false, 2)
        .addIngredient("WHEAT", false, 1));
```

Additional hooks on `RecipeRegistration`:
- `registerOutputHandler(recipeId, CustomOutputHandler)` — produce dynamic outputs from actual inputs
- `registerOutputDecorator(addonId, recipeId, RecipeOutputDecorator)` — annotate or adjust crafted stacks in place
- `registerEligibilityPredicate(recipeId, RecipeEligibilityPredicate)` — enforce custom pre-craft checks before inputs are reserved
- `inspectFile(File, defaultAddonId, customItemExists)` — validate editable recipe files offline without mutating registries
- Helper factories: `RecipeRegistration.vanillaItemMatcher(materialId)`, `customItemMatcher(customItemId)`, `action(type, key, value)`, `visualAction(visualId)`, `nameAction(displayName)`

## Crops & Seed Acquisition (`api.crops()`, `api.seedAcquisition()`)

```java
import ke.ric.api.registration.CropRegistration;
import org.bukkit.Material;
import org.bukkit.Sound;

api.crops().register(CropRegistration.builder()
        .id("BLUEBERRY_BUSH")
        .itemId("BLUEBERRY")
        .plantType("SHORT_PLANT")
        .growthDuration(600)
        .growthStages(4)
        .validPlantingBlocks(Material.FARMLAND, Material.GRASS_BLOCK)
        .harvestDrop("BLUEBERRY", 2, 4)
        .replantAfterHarvest(true)
        .sounds(Sound.BLOCK_SWEET_BERRY_BUSH_PICK_BERRIES, Sound.BLOCK_CROP_BREAK)
        .textures("http://textures.minecraft.net/texture/...", "http://textures.minecraft.net/texture/..."));
```

Register custom plant growth behaviors via `api.crops().registerPlantType(PlantType, addonId)` and load addon seed packets, biome grass drops, chest loot, and block drops via `SeedAcquisitionRegistration` (`api.seedAcquisition().registerFromFile(file, addonId)`).

## Dietary Properties, Advancements, Aging & Guides

### Dietary Properties (`api.properties()`)

```java
import ke.ric.api.registration.PropertyRegistration;

api.properties().register(PropertyRegistration.builder()
        .id("CAFFEINE_FREE")
        .displayName("Caffeine-Free")
        .displayIcon("🍵")
        .description("Contains no coffee or tea")
        .violatorCustomItems("ESPRESSO", "MATCHA_LATTE"));
```

### Advancements (`api.advancements()`)

```java
import ke.ric.api.advancement.AdvancementDefinition;

api.advancements().register(AdvancementDefinition.hiddenChallenge(
        "taste_golden_mead",
        "Cellar Connoisseur",
        "Sample a bottle of Golden Mead",
        "GOLDEN_MEAD",
        null
));
```

### Cellar / Rack Aging (`api.aging()`)

Define owner-scoped timed aging stages (with `AgingCondition`s, `AgingEnvironmentProbe`s, dynamic outcomes, and in-place item preservation):

```java
import ke.ric.api.aging.AgingCondition;
import ke.ric.api.aging.AgingDefinition;
import ke.ric.api.aging.AgingStage;
import java.time.Duration;

api.aging().register(AgingDefinition.builder()
        .id("myaddon:aged_mead")
        .input("YOUNG_MEAD")
        .stage(AgingStage.of("Rested", Duration.ofMinutes(10), AgingCondition.ZERO_SKYLIGHT, AgingCondition.COOL))
        .output("GOLDEN_MEAD")
        .outputYield(1)
        .build());
```

### Cookbook Guides (`api.guides()`)

Register custom addon hub entries, routed guide pages, exact ingredient production deep links (`registerProductionDestination`), tag destinations (`registerTagProductionDestination`), and custom non-recipe item uses (`registerItemUse`):

```java
import ke.ric.api.guide.GuideDefinition;
import ke.ric.api.guide.GuideDestination;
import ke.ric.api.guide.GuidePage;
import ke.ric.cooking.data.RecipeItemRef;
import java.util.List;

api.guides().register(new GuideDefinition(
        "myaddon_guide",
        10,
        player -> api.createItem("GOLDEN_MEAD"),
        player -> new GuidePage("My Food Addon", List.of())
));

api.guides().registerProductionDestination(
        RecipeItemRef.customItem("GOLDEN_MEAD"),
        null,
        new GuideDestination("myaddon_guide", "mead_overview")
);
```
