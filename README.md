<div align="center">
  <p>
    <img width="100%" src="https://animalcrossing.nintendo.com/new-horizons/assets/img/home/hero.jpg" alt="Animal Crossing New Horizon Simulator"></a>
  </p>
</div>
<div align="center">

# 🎮 Enigma Engines - Animal Crossing New Horizon Simulator 🏝️

</div>
https://animalcrossing.nintendo.com/new-horizons/assets/img/home/hero.jpg
Welcome to the Enigma Engines - Animal Crossing Simulator! This project simulates various aspects of the beloved game Animal Crossing: New Horizons (ACNH).

## 📖 Table of Contents

- [🐾 What is Animal Crossing?](#🐾-what-is-animal-crossing)
- [🎯 Objective of the Code](#🎯-objective-of-the-code)
- [🛠️ Setup](#🛠️-setup)
- [⚙️ Explanation of the Process](#⚙️-explanation-of-the-process)
  - [Core Classes](#core-classes)
    - [`ACNHItemDataset`](#acnhitemdataset)
    - [`ACNHVillager`](#acnhvillager)
    - [`ACNHEnvironment`](#acnhenvironment)
- [🚀 How to Run](#🚀-how-to-run)
- [🤝 Contributing](#🤝-contributing)
- [📝 License](#📝-license)

## 🐾 What is Animal Crossing?

Animal Crossing is a beloved [social simulation video game series](https://en.wikipedia.org/wiki/Animal_Crossing) developed and published by [Nintendo](https://www.google.com/search?q=https://www.nintendo.com/). In these charming games, the player character embarks on a new life in a village (or, in the latest installment, an island) inhabited by a delightful cast of anthropomorphic animals. Gameplay revolves around a wide array of relaxing activities such as fishing, bug catching, fossil hunting, gardening, and extensive home and environment decoration. The series is particularly renowned for its open-ended gameplay, allowing players to set their own goals, and its unique use of the console's internal clock and calendar to simulate the real-time passage of days and seasons, influencing in-game events and an ever-changing environment.

### Animal Crossing: New Horizons (ACNH)

The latest and massively popular installment, [Animal Crossing: New Horizons (ACNH)](https://www.animal-crossing.com/new-horizons/), launched for the [Nintendo Switch](https://www.google.com/search?q=https://www.nintendo.com/switch/), takes players to a deserted island as part of the "Nook Inc. Deserted Island Getaway Package." Players are tasked with transforming this untouched wilderness into a thriving, personalized community for themselves and a growing number of animal residents.

Key features and activities in ACNH include:

  * **Resource Gathering & Crafting (DIY):** Players collect natural resources like wood, stone, and iron to craft a vast array of items, including tools, furniture, and decorative pieces using [DIY Recipes](https://nookipedia.com/wiki/DIY_recipes).
  * **Island Customization:** Unprecedented freedom to customize not only your home's interior and exterior but also the island itself through [terraforming](https://www.google.com/search?q=https://nookipedia.com/wiki/Island_Designer_\(application\)) (landscaping paths, cliffs, and waterways) once unlocked.
  * **Villager Interaction:** Befriend and interact with a charming and diverse cast of up to 10 animal [villagers](https://nookipedia.com/wiki/Villager), each with unique personalities, catchphrases, and homes.
  * **Economic Simulation:** Engage in various economic activities:
      * Earning and spending **Bells** (the in-game currency) by selling fish, bugs, fruit, crafted items, and more.
      * Participating in the volatile "Stalk Market" by buying turnips from Daisy Mae on Sundays and selling them at [Nook's Cranny](https://nookipedia.com/wiki/Nook%27s_Cranny) throughout the week for fluctuating prices.
      * Earning **Nook Miles**, a secondary currency, by completing various tasks and achievements, which can be redeemed for special items, recipes, and services like [Nook Miles Tickets](https://nookipedia.com/wiki/Nook_Miles_Ticket) to visit mystery islands.
  * **Collections & Museum:** Donate discovered [fish](https://www.google.com/search?q=https://nookipedia.com/wiki/Fish_\(New_Horizons\)), [bugs](https://www.google.com/search?q=https://nookipedia.com/wiki/Bugs_\(New_Horizons\)), [fossils](https://nookipedia.com/wiki/Fossil), and [art](https://www.google.com/search?q=https://nookipedia.com/wiki/Art_\(New_Horizons\)) to Blathers, the owl curator of the island's magnificent [museum](https://www.google.com/search?q=https://nookipedia.com/wiki/Museum_\(New_Horizons\)).
  * **Seasonal Events & Updates:** The game regularly features seasonal events, holidays (like Toy Day in December or Bunny Day in spring), fishing tourneys, bug-offs, and free updates that introduce new characters, items, and gameplay mechanics.
  * **Real-Time Progression:** The game syncs with the Nintendo Switch's system clock, meaning a day in ACNH is a real-world day. Shops have opening hours, characters have schedules, and the environment changes with the actual seasons of the player's chosen hemisphere.

-----
<details open>
<summary>Core Mechanics</summary>

### How is Animal Crossing: New Horizons Actually Played?

Animal Crossing: New Horizons offers a gentle, open-ended experience where players dictate their own pace and goals. 

Here's a general overview of the gameplay loop:

1.  **Arrival and Humble Beginnings:**

      * Players start by customizing their character and choosing a deserted island layout. Upon arrival, they are greeted by Tom Nook and his nephews, Timmy and Tommy, who run Nook Inc.
      * The initial days involve setting up a tent, learning basic survival skills (like crafting flimsy tools), and helping Tom Nook with initial tasks to get the island settlement started. This often includes choosing locations for the first few new animal residents' tents.

2.  **Daily Island Life:**

      * **Morning Routine:** Many players start their day by checking their mailbox for letters and packages, looking for new announcements from Isabelle at Resident Services, finding the daily hidden "money rock," and searching for buried fossils.
      * **Resource Management:** Gathering resources is a daily activity – shaking trees for branches and fruit, hitting rocks for stone, clay, and iron nuggets, chopping wood, and pulling weeds.
      * **Crafting & Building:** Using collected resources and DIY recipes, players craft tools, furniture, and other items. They contribute to community projects like building bridges and inclines to improve island accessibility.
      * **Shopping & Economy:** Players visit Nook's Cranny to buy and sell goods, and the Able Sisters tailor shop to purchase new clothing. They might check turnip prices if they've invested in the Stalk Market.
      * **Nook Miles & Tasks:** Players complete various short-term and long-term tasks listed in their NookPhone to earn Nook Miles. These can range from "catch 5 bugs" to "decorate your home." The Nook Stop terminal in Resident Services allows players to redeem miles and access other services.

3.  **Developing the Island Paradise:**

      * **Attracting New Residents:** As the island develops, more animal villagers will be invited to move in, each requiring a new housing plot to be set up.
      * **Upgrading Facilities:** Key buildings like the Museum, Nook's Cranny, and Able Sisters shop will be established and can be upgraded over time. Resident Services also upgrades from a tent to a proper building, unlocking more features with Isabelle.
      * **Home Sweet Home:** Players can upgrade their own tent into a house and then expand it multiple times, paying off loans to Tom Nook. Each expansion adds more rooms and customization options.
      * **Island Designing:** A significant mid-to-late game feature is unlocking the "Island Designer" app on the NookPhone. This allows players to terraform the island – creating or removing cliffs, waterways, and paths – and extensively decorate the entire island landscape.

4.  **Socializing and Collecting:**

      * **Villager Interactions:** Talking to animal residents, fulfilling their requests, giving them gifts, and celebrating their birthdays helps build friendships. Happy villagers are more interactive and may give players gifts or teach them new reactions (emotes).
      * **Museum Curation:** A major long-term goal for many is completing the museum's collections by catching every type of fish and bug (which vary by season, time of day, and weather), digging up all fossils, and acquiring genuine pieces of art from Redd.
      * **Seasonal Activities:** Players participate in seasonal events, collect limited-time items, and experience the changing flora and fauna that each season brings.

5.  **Setting Personal Goals:**

      * Beyond the initial objectives set by Tom Nook, ACNH is largely about self-directed play. Some players might focus on achieving a 5-star island rating from Isabelle, others on collecting all K.K. Slider songs, breeding hybrid flowers, designing elaborate themed areas, or simply enjoying the calm, daily rhythm of island life.

6.  **Multiplayer Fun (Optional):**

      * Players can visit their friends' islands (or have friends visit theirs) locally or online using Dodo Airlines (DAL). This allows for trading items, sharing custom designs, exploring new environments, and participating in activities together.
</details>
ACNH is designed to be played over a long period, with new discoveries and small joys unfolding each day. It's a game about creativity, community, and finding comfort in a charming virtual world.

## 🎯 Objective of the Code

This Python project aims to create a simplified simulation of the Animal Crossing: New Horizons environment. The primary objectives include:

-   **Simulating Core Game Mechanics:** Implementing systems for item management, villager interactions, economic activities (like earning Bells and Nook Miles), and resource gathering (fishing, farming).
-   **Data-Driven Design:** Utilizing CSV files to load and manage game data (items, villagers, fish, crops, achievements, etc.), making the simulation extensible and customizable.
-   **Agent-Based Modeling:** Representing villagers as agents who can perform actions, interact with the environment, and manage their own inventories and goals.
-   **Environment Dynamics:** Simulating changes over time, such as daily Nook Miles tasks, fluctuating turnip prices, and crop growth cycles.
-   **Extensibility:** Designing the core classes in a way that allows for future expansion with more complex behaviors, events, and game features.

Essentially, this project provides a framework to explore and experiment with the game dynamics of ACNH in a programmatic way.

## 🛠️ Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone https://github.com/shankha06/enigma-engines.git
    cd enigma-engines
    ```

2.  **Ensure Python is installed:**
    This project requires Python 3.13 or higher. You can download it from [python.org](https://www.python.org/).

3.  **Install dependencies:**
    The project uses `uv` for environment management if you have it, or you can use `pip`. Dependencies are listed in `pyproject.toml`.
    ```bash
    # Using pip
    pip install uv
    ```
    > **Note**   It's highly recommended to use uv. If using `uv`, you need to prefix all commands with `uv run`.

4.  **Data Files:**
    Ensure the `data` directory is present in the root of the project and contains all necessary CSV files (e.g., `villagers.csv`, `items.csv`, `fish.csv`, etc.). The simulator relies on these files to load game information. The expected CSV files are:
    `accessories.csv`, `achievements.csv`, `art.csv`, `bags.csv`, `bottoms.csv`, `construction.csv`, `crops.csv`, `dress-up.csv`, `fencing.csv`, `fish.csv`, `floors.csv`, `fossils.csv`, `headwear.csv`, `housewares.csv`, `insects.csv`, `miscellaneous.csv`, `music.csv`, `other.csv`, `photos.csv`, `posters.csv`, `reactions.csv`, `recipes.csv`, `rugs.csv`, `shoes.csv`, `socks.csv`, `tools.csv`, `tops.csv`, `umbrellas.csv`, `villagers.csv`, `wall-mounted.csv`, `wallpaper.csv`.

## ⚙️ Explanation of the Process

The simulation is built around a few core Python classes that interact to model the ACNH world.

Okay, here's that section enhanced with more readable formatting, including the use of icons (emojis), tables for summarizing key responsibilities, highlights, and clearer structure.

-----

## 🚀 Core Classes Deep Dive

This section breaks down the primary classes that form the backbone of the ACNH simulation logic.

-----

### 💾 `ACNHItemDataset`

> **Primary Role:** Serves as the central repository and provider for all static game data, loaded from CSV files. It's the source of truth for items, villagers, critters, and tasks.

| Feature Group         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 📂 **Data Loading** | Loads game data from CSV files within the <code>/data</code> directory. This includes: <ul><li>Items (housewares, fossils, tools, etc.)</li><li>Villagers</li><li>Fish</li><li>Crops</li><li>Nook Miles tasks (achievements)</li></ul>|
| 🛡️ **Error Handling** | Manages potential issues during CSV loading (e.g., missing files/columns). <ul><li>Can provide fallback data or warnings.</li></ul> |
| ⚙️ **Data Accessors** | Offers methods to retrieve specific game information, such as: <ul><li>Random villager names.</li><li>Details for giftable/sellable items (e.g., <code>cost</code>, <code>friendship_points</code>, <code>sell_price</code>).</li><li>Random gift options for villagers.</li><li>Templates for daily Nook Miles tasks.</li><li>Specific data for fish (e.g., spawn conditions, price) or crops (e.g., <code>GrowthTimeDays</code>).</li></ul>                  |
| 🛠️ **Underlying Tech** | Utilizes the <code>pandas</code> library for efficient parsing and handling of CSV data.|

-----
### 👤 `ACNHVillager`

> **Primary Role:** Represents an individual character in the simulation, whether it's a non-player villager or the player themself. Manages personal attributes, inventory, and interactions.

| Attribute/Method                     | Description                                                                                                                                                                                             |
| :----------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 🆔 **Identity & Social** | Each villager has a unique <code>name</code> and a <code>friendship_level</code> (particularly relevant for interactions with the player or other NPCs).                                                 |
| 🎒 **Inventory Management** | Maintains an <code>inventory</code> (dictionary mapping item names to quantities). <ul><li><code>add_to_inventory()</code>: Adds items.</li><li><code>remove_from_inventory()</code>: Removes items.</li></ul> |
| 🎁 **Gift Interactions** | Tracks <code>last_gifted_day</code> to prevent daily gifting exploits. <ul><li><code>receive_gift()</code>: Updates <code>friendship_level</code> based on the gift's value and villager preferences (if modeled).</li></ul> |
| 📈 **Economic Activity Tracking** | <code>log_sale()</code>: Records items sold by the villager. This data can be crucial for tracking progress towards economic Nook Miles tasks or achievements.                                             |
| 🗓️ **Daily Reset** | <code>reset_daily_log()</code>: Clears any logs or flags specific to a single day's activities (e.g., daily gift status).                                                                                   |
-----

### 🏝️ `ACNHEnvironment`

> **Primary Role:** The main engine of the simulation. It orchestrates game state, manages time progression, houses all villagers, and controls global systems like the economy, tasks, and farming.

**Core Functionalities:**

  * 🌍 **Initialization & Setup:**

      * Initializes with a specified number of villagers.
      * Creates and holds an instance of `ACNHItemDataset` for all game data needs.
      * Manages the `current_day` and `current_date` of the simulation.
      * Tracks global player resources like `bells` (currency) and `nook_miles`.
      * `_populate_initial_villagers()`: Creates the villager instances at the start.
      * `reset()`: Resets the entire environment to its default initial state for new simulation runs.

  * 📈 **Economic Systems:**

      * **Turnip Market (`Stalk Market`):**
          * Simulates weekly turnip price fluctuations:
              * Buy prices set on Sundays.
              * Sell prices vary daily from Monday to Saturday.
          * Features a `turnip_market_saturation_factor` that can adjust sell prices based on recent collective sales volume, simulating supply/demand.
      * **Fish Market Saturation:**
          * Adjusts the effective sell price of fish based on the quantity recently sold by all agents, mimicking a dynamic market.

  * 🎯 **Nook Miles Tasks System:**

      * Assigns a set of `active_nook_tasks` daily to the player/agent.
      * Task templates are drawn from the `ACNHItemDataset`.
      * Includes a method `_check_task_criteria()` for verifying task completion (though the detailed per-action checking might be distributed or handled by the agent).

  * 🌱 **Crop Farming System:**

      * Manages `farm_plots` for planting and harvesting crops.
      * For each plot, tracks: `crop_name`, `plant_day`, and `ready_day` (when it can be harvested).

  * 🕰️ **Time Progression & Updates:**

      * Implicitly advances the day (e.g., when a simulation loop increments `current_day`).
      * Triggers daily updates to systems like turnip prices and Nook Miles task assignments.
      * Manages crop growth status based on elapsed days.

-----

### 🔄 **Overall Flow (Conceptual)**

The simulation progresses through a conceptual daily cycle, driven by an external loop (e.g., in a main script).

1.  ➡️ **Initialization:**

      * An `ACNHEnvironment` instance is created.
      * This, in turn, initializes the `ACNHItemDataset` (💾 loading all game data).
      * 👤 Villager instances are created and populated within the environment.
      * Initial game state is set: starting `bells`, `nook_miles`, initial turnip prices, first set of Nook Miles tasks.

2.  ➡️ **Daily Cycle (Repeated for the duration of the simulation):**

      * ☀️ **Day Advances:** The `current_day` in the `ACNHEnvironment` increments.
      * ⚙️ **Environment Updates:**
          * Turnip prices are recalculated based on the new day of the week and market factors.
          * New daily Nook Miles tasks are assigned/refreshed.
          * Crop growth on `farm_plots` is updated; some may become ready for harvest.
          * Market saturation factors (fish, turnips) might be adjusted.
      * 🧑‍🤝‍🧑 **Agent Actions (Conceptual - driven by an Agent class not detailed here):**
          * Based on their goals and the current `ACNHEnvironment` state, agents (villagers/player) would:
              * Make economic decisions (buy/sell items, invest in turnips).
              * Engage in activities (🎣 fishing, 🦋 bug catching, 🌱 farming).
              * Interact (🎁 give gifts, talk to others).
              * Attempt to complete their active Nook Miles tasks.
      * 📊 **State Update:** The `ACNHEnvironment` (and individual `ACNHVillager` states) are updated based on the outcomes of agent actions (e.g., `bells` change, `inventory` updates, `friendship_levels` adjust, task progress is recorded).
      * 🏁 **Continuation:** The simulation loop continues for a predetermined number of days or until specific end conditions are met.

-----

## 🚀 How to Run

Setup is using uv package manager.
```bash
uv sync && uv pip install -e .
uv run python enigma_engines\animal_crossing\simulation.py
```

## 🤝 Contributing

We welcome contributions! Please fork the repository and submit a pull request. Please ensure your changes are well-documented and include tests if applicable. Contributions are highly appreciated.

## 📝 License

This project is licensed under the terms of the [MIT License](LICENSE). You are free to use, modify, and distribute this code as long as you comply with the license terms.

---

Happy Simulating! 🥳
