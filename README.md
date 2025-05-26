<style>
    .content {
        margin: 0 auto;
        width: calc(80% - 100px); /* Corrected: Added spaces around the minus operator */
    }
</style>

<div class="content">
<div align="center">

# 🎮 Enigma Engines - Animal Crossing Simulator 🏝️

</div>
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
- [📦 Dependencies](#-dependencies)
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

### How is Animal Crossing: New Horizons Actually Played?

Animal Crossing: New Horizons offers a gentle, open-ended experience where players dictate their own pace and goals. Here's a general overview of the gameplay loop:

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
    git clone <your-repository-url>
    cd enigma-engines
    ```

2.  **Ensure Python is installed:**
    This project requires Python 3.13 or higher. You can download it from [python.org](https://www.python.org/).

3.  **Install dependencies:**
    The project uses `uv` for environment management if you have it, or you can use `pip`. Dependencies are listed in `pyproject.toml`.
    ```bash
    # Using pip
    pip install -r requirements.txt # (You might need to generate this from pyproject.toml or install manually)
    # or install listed dependencies directly:
    pip install beautifulsoup4 black fake-useragent matplotlib openpyxl pandas rich ruff seaborn
    ```
    It's highly recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install beautifulsoup4 black fake-useragent matplotlib openpyxl pandas rich ruff seaborn
    ```

4.  **Data Files:**
    Ensure the `data` directory is present in the root of the project and contains all necessary CSV files (e.g., `villagers.csv`, `items.csv`, `fish.csv`, etc.). The simulator relies on these files to load game information. The expected CSV files are:
    `accessories.csv`, `achievements.csv`, `art.csv`, `bags.csv`, `bottoms.csv`, `construction.csv`, `crops.csv`, `dress-up.csv`, `fencing.csv`, `fish.csv`, `floors.csv`, `fossils.csv`, `headwear.csv`, `housewares.csv`, `insects.csv`, `miscellaneous.csv`, `music.csv`, `other.csv`, `photos.csv`, `posters.csv`, `reactions.csv`, `recipes.csv`, `rugs.csv`, `shoes.csv`, `socks.csv`, `tools.csv`, `tops.csv`, `umbrellas.csv`, `villagers.csv`, `wall-mounted.csv`, `wallpaper.csv`.

## ⚙️ Explanation of the Process

The simulation is built around a few core Python classes that interact to model the ACNH world.

### Core Classes

#### `ACNHItemDataset`

-   **Purpose:** This class is responsible for loading and providing access to all game data from the CSV files located in the `/data` directory.
-   **Functionality:**
    -   Loads data for items (housewares, fossils, tools, etc.), villagers, fish, crops, and Nook Miles tasks (achievements).
    -   Handles potential errors during CSV loading, such as missing files or columns, and provides fallback data if necessary.
    -   Provides methods to retrieve:
        -   Random villager names.
        -   Details about specific giftable/sellable items (cost, friendship points, sell price).
        -   Random gift options.
        -   Templates for daily Nook Miles tasks.
        -   Data for specific fish or crops.
    -   Internally uses `pandas` for efficient CSV parsing.

#### `ACNHVillager`

-   **Purpose:** Represents an individual villager (or the player character) within the simulation.
-   **Functionality:**
    -   Each villager has a `name`, `friendship_level`, and an `inventory` (a dictionary of item names to quantities).
    -   Keeps track of the `last_gifted_day` to prevent multiple gifts on the same day.
    -   `receive_gift()`: Updates friendship level based on the gift received.
    -   `add_to_inventory()` / `remove_from_inventory()`: Manages the villager's items.
    -   `log_sale()`: Records items sold by the villager, which can be used for task/achievement tracking.
    -   `reset_daily_log()`: Clears the daily activity log.

#### `ACNHEnvironment`

-   **Purpose:** This class orchestrates the entire simulation. It manages the game state, time, villagers, and global systems like the economy and tasks.
-   **Functionality:**
    -   Initializes the simulation with a specified number of villagers and loads data using an `ACNHItemDataset` instance.
    -   Manages `current_day` and `current_date`.
    -   Keeps track of the player's main resources: `bells` (currency) and `nook_miles`.
    -   **Turnip Market:**
        -   Simulates weekly turnip buying (Sundays) and selling (Monday-Saturday) prices.
        -   Includes a `turnip_market_saturation_factor` that affects sell prices based on recent sales volume.
    -   **Nook Miles Tasks:**
        -   Assigns a set of `active_nook_tasks` daily using templates from the `ACNHItemDataset`.
        -   Provides a method `_check_task_criteria()` (though the detailed logic for checking completion against villager actions is more involved and part of the agent's decision-making process, which isn't fully detailed in `core_classes.py` but is implied).
    -   **Crop Farming System:**
        -   Manages `farm_plots` where crops can be planted and harvested.
        -   Tracks `crop_name`, `plant_day`, and `ready_day` for each plot.
    -   **Fish Market Saturation:**
        -   Adjusts the effective sell price of fish based on how many have been recently sold, simulating supply and demand.
    -   `reset()`: Resets the environment to its initial state.
    -   `_populate_initial_villagers()`: Creates villager instances.
    -   Methods to advance the day (implicitly, by changing `current_day` and calling updates), update turnip prices, and assign tasks.

### Overall Flow (Conceptual)

1.  **Initialization:**
    -   An `ACNHEnvironment` is created.
    -   It initializes an `ACNHItemDataset` to load all game data.
    -   Villagers are created.
    -   Initial Bells, Nook Miles, turnip prices, and Nook Miles tasks are set up.

2.  **Daily Cycle (Conceptual - requires a simulation loop not explicitly in `core_classes.py`):**
    -   The `current_day` advances.
    -   The environment updates:
        -   Turnip prices are updated based on the day of the week.
        -   New daily Nook Miles tasks are assigned.
        -   Crop growth is checked/updated.
    -   Villagers (agents) would then perform actions based on their goals and the current environment state:
        -   Decide to buy/sell items.
        -   Fish, catch bugs, farm crops.
        -   Interact with other villagers (e.g., give gifts).
        -   Attempt to complete Nook Miles tasks.
    -   The environment state (Bells, Nook Miles, inventories, friendship levels, task progress) is updated based on these actions.
    -   The simulation continues for a set number of days or until certain conditions are met.

## 🚀 How to Run

Setup is using uv package manager.
```bash
uv sync && uv pip install -e .
uv run python enigma_engines\animal_crossing\simulation.py
```

## 📦 Dependencies

This project relies on the following Python libraries:

-   `beautifulsoup4>=4.13.3`
-   `black>=25.1.0` (for code formatting)
-   `fake-useragent>=2.1.0`
-   `matplotlib>=3.10.3` (likely for data visualization, though not used in `core_classes.py`)
-   `openpyxl>=3.1.5` (for reading/writing Excel files, though CSVs are the primary data source in `core_classes.py`)
-   `pandas>=2.2.3` (for data manipulation, especially CSV handling)
-   `rich>=14.0.0` (for rich text and beautiful formatting in terminal, not directly used in `core_classes.py`)
-   `ruff>=0.11.0` (for linting)
-   `seaborn>=0.13.2` (for statistical data visualization, not used in `core_classes.py`)

These are listed in the `pyproject.toml` file.

## 🤝 Contributing

We welcome contributions! Please fork the repository and submit a pull request.

## 📝 License

This project is licensed under the terms of the [MIT License](LICENSE) (assuming `LICENSE` file contains MIT, otherwise update accordingly).

---

Happy Simulating! 🥳
</div>