# Developer API

Integrate external Paper plugins with **Heirloom 2.11.0** to inspect `FoodFactsV2` dietary provenance, create or identify custom foods, listen to cooking/harvest/consumption events, and register programmatic items, recipes, crops, aging stages, advancements, or cookbook guides.

## Maven Repository & Dependency

Add the public Heirloom Maven repository and compile against `ke.ric:heirloom-api:2.11.0` (Java 21+, Paper 1.21.11+).

- **Repository URL:** `https://heirloom-maven.pages.dev`
- **Coordinates:** `ke.ric:heirloom-api:2.11.0`
- **Online Javadocs:** [`https://heirloom-maven.pages.dev/javadoc/`](https://heirloom-maven.pages.dev/javadoc/)

=== "Gradle (Kotlin DSL)"

    ```kotlin
    repositories {
        mavenCentral()
        maven("https://repo.papermc.io/repository/maven-public/")
        maven("https://heirloom-maven.pages.dev")
    }

    dependencies {
        compileOnly("io.papermc.paper:paper-api:1.21.11-R0.1-SNAPSHOT")
        compileOnly("ke.ric:heirloom-api:2.11.0")
    }
    ```

=== "Gradle (Groovy)"

    ```groovy
    repositories {
        mavenCentral()
        maven { url 'https://repo.papermc.io/repository/maven-public/' }
        maven { url 'https://heirloom-maven.pages.dev' }
    }

    dependencies {
        compileOnly 'io.papermc.paper:paper-api:1.21.11-R0.1-SNAPSHOT'
        compileOnly 'ke.ric:heirloom-api:2.11.0'
    }
    ```

=== "Maven (pom.xml)"

    ```xml
    <repositories>
        <repository>
            <id>papermc</id>
            <url>https://repo.papermc.io/repository/maven-public/</url>
        </repository>
        <repository>
            <id>heirloom-maven</id>
            <url>https://heirloom-maven.pages.dev</url>
        </repository>
    </repositories>

    <dependencies>
        <dependency>
            <groupId>io.papermc.paper</groupId>
            <artifactId>paper-api</artifactId>
            <version>1.21.11-R0.1-SNAPSHOT</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>ke.ric</groupId>
            <artifactId>heirloom-api</artifactId>
            <version>2.11.0</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>
    ```

=== "plugin.yml"

    ```yaml
    # Hard dependency if Heirloom is required:
    depend: [Heirloom]

    # Or soft dependency when integrating optionally:
    softdepend: [Heirloom]
    ```

!!! warning "Compile-Only SDK — Never Shade"
    `ke.ric:heirloom-api` ships compile-only API stubs whose methods throw `UnsupportedOperationException` if bundled into your plugin JAR. Always keep it `compileOnly` (Gradle) or `<scope>provided</scope>` (Maven) so Paper loads the real implementation from the Heirloom plugin at runtime.

!!! tip "IDE Autocomplete, Parameter Names & Hover Javadocs"
    `heirloom-maven.pages.dev` publishes `heirloom-api-2.11.0-javadoc.jar` and `heirloom-api-2.11.0-sources.jar` alongside `.jar`, and compiles bytecode with `-parameters`. IntelliJ IDEA, VS Code, and Eclipse automatically show full parameter names, Javadoc descriptions, and usage snippets on hover after syncing Gradle or Maven.

## Accessing `HeirloomAPI`

Verify that `Heirloom` is enabled before calling API methods, then check `api.isReady()` before performing registrations or runtime lookups:

```java
import ke.ric.api.HeirloomAPI;
import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;
import org.bukkit.plugin.java.JavaPlugin;

public final class MyIntegrationPlugin extends JavaPlugin {
    @Override
    public void onEnable() {
        Plugin heirloomPlugin = Bukkit.getPluginManager().getPlugin("Heirloom");
        if (heirloomPlugin == null || !heirloomPlugin.isEnabled()) {
            return;
        }

        HeirloomAPI api = HeirloomAPI.getInstance();
        if (api == null || !api.isReady()) {
            return;
        }

        // Safe to read items, listen to events, or register addons
    }
}
```

## Documentation Map

| Topic | Covers | Page |
| --- | --- | --- |
| **Items & FoodFacts V2** | Creating/identifying custom items, `FoodFactsV2` dietary truth & ingredient provenance, raw PDC JSON schema, beverage quality & alcohol helpers | [Items & FoodFacts V2](items-and-food-facts.md) |
| **Bukkit Events** | `HeirloomFoodConsumedEvent`, `HeirloomPlacedFoodConsumedEvent`, `HeirloomItemCraftedEvent`, `HeirloomCropHarvestedEvent`, `HeirloomAdminItemEvent` | [Bukkit Events](events.md) |
| **Addons & Registration** | `registerAddon` lifecycle callbacks, `/hl reload` rollback safety, registering items, recipes, crops, properties, advancements, aging & guides | [Addons & Registration](addons-and-registration.md) |
| **Online Javadocs** | Full method/record reference across `ke.ric.api.*`, `ke.ric.cooking.*`, and `ke.ric.gardening.data.*` | [`heirloom-maven.pages.dev/javadoc/`](https://heirloom-maven.pages.dev/javadoc/) |
