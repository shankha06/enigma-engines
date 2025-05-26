# --- 5. Simulation Loop ---
from enigma_engines.animal_crossing.core.agent import SocialEconomistAgent
from enigma_engines.animal_crossing.core.environment import ACNHEnvironment
from enigma_engines.animal_crossing.core.load_data import ACNHItemDataset

# from enigma_engines.animal_crossing.plotting_utils import plot_simulation_results # Keep if you still want image plots

# Rich library imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.padding import Padding
from rich.columns import Columns

# --- Rich Console Initialization ---
console = Console()


def format_bell_count(bells):
    """Formats bell count with commas and a bell icon."""
    return f":bell: [bold green]{bells:,}[/bold green]"


def format_nook_miles(miles):
    """Formats Nook Miles with a leaf icon."""
    return f":fallen_leaf: [bold cyan]{miles:,}[/bold cyan]"


def format_friendship(friendship_level):
    """Formats friendship level with a heart icon and color based on level."""
    if friendship_level < 2:
        style = "bold red"
        icon = ":broken_heart:"
    elif friendship_level < 4:
        style = "bold yellow"
        icon = ":yellow_heart:"
    else:
        style = "bold green"
        icon = ":heart:"
    return f"{icon} [{style}]{friendship_level:.2f}[/{style}]"


def run_simulation(days_to_simulate):
    console.print(
        Panel(
            "[bold magenta]--- Starting ACNH Social Economist Agent Simulation --- :rocket:",
            title="Simulation Start",
            expand=False,
        )
    )

    dataset = ACNHItemDataset()  # Load once
    num_villagers = 3
    env = ACNHEnvironment(num_villagers=num_villagers, dataset=dataset)
    agent = SocialEconomistAgent(dataset=dataset, num_villagers_on_island=num_villagers)

    env.reset()  # Initialize environment

    total_rewards_log = {"friendship": [], "bells": [], "nook_miles": []}
    agent_state_log = []

    for day in range(days_to_simulate):
        current_env_state = env.get_state()
        day_panel_title = f":calendar: Day {env.current_day} ({current_env_state['current_date']}) :sunrise_over_mountains:"

        header_text = Text(justify="center")
        header_text.append(
            f"Bells: {format_bell_count(current_env_state['bells'])} | ", style="bold"
        )
        header_text.append(
            f"Nook Miles: {format_nook_miles(current_env_state['nook_miles'])} | ",
            style="bold",
        )
        header_text.append(
            f"Avg. Friendship: {format_friendship(current_env_state['avg_friendship'])}",
            style="bold",
        )

        day_info = [header_text]

        if current_env_state["turnip_buy_price"] > 0:
            day_info.append(
                f":moneybag: Daisy Mae selling turnips at: [bold yellow]{current_env_state['turnip_buy_price']}[/bold yellow] bells"
            )
        if current_env_state["turnip_sell_price"] > 0:
            day_info.append(
                f":chart_with_upwards_trend: Nooklings buying turnips at: [bold green]{current_env_state['turnip_sell_price']}[/bold green] bells"
            )

        if current_env_state["active_nook_tasks"]:
            tasks_table = Table(
                title=":scroll: Available Nook Tasks",
                show_header=True,
                header_style="bold blue",
            )
            tasks_table.add_column("Task Name", style="dim", width=30)
            tasks_table.add_column("Miles", justify="right")
            tasks_table.add_column("Category", justify="right")
            tasks_table.add_column("Quantity", justify="right")
            for task_name, details in current_env_state["active_nook_tasks"].items():
                tasks_table.add_row(
                    task_name,
                    str(details.get("miles", "N/A")),
                    str(details["criteria"]["category"]),
                    str(details["criteria"]["quantity"]),
                )
            day_info.append(tasks_table)
        else:
            day_info.append(":information_source: No Nook Tasks available today.")

        villager_table = Table(
            title=":house_with_garden: Villager Friendship Levels",
            show_header=True,
            header_style="bold purple",
        )
        villager_table.add_column("Villager Name", style="italic")
        villager_table.add_column("Friendship", justify="center")

        for v_obj in env.villagers:
            villager_table.add_row(
                v_obj.name, format_friendship(v_obj.friendship_level)
            )
        day_info.append(villager_table)

        console.print(
            Panel(
                Padding(
                    (
                        "\n".join(str(item) for item in day_info)
                        if not isinstance(day_info[0], Table)
                        and not isinstance(day_info[0], Text)
                        else Columns(day_info, expand=True, equal=True)
                    ),
                    (1, 2),
                ),
                title=day_panel_title,
                border_style="cyan",
            )
        )

        action = agent.choose_action(current_env_state, env.villagers)
        # console.print(f":gear: Action chosen: [italic]{action}[/italic]") # Optional: print chosen action

        reward_friendship, reward_bells, reward_nook_miles = env.step(
            action, current_env_state
        )

        final_state_today = env.get_state()
        total_rewards_log["friendship"].append(final_state_today["avg_friendship"])
        total_rewards_log["bells"].append(final_state_today["bells"])
        total_rewards_log["nook_miles"].append(final_state_today["nook_miles"])
        agent_state_log.append(final_state_today)

        if day % 100 == 0 or day == days_to_simulate - 1:
            progress_text = Text.assemble(
                (
                    f"Day {env.current_day} ({final_state_today['current_date']}): ",
                    "bold",
                ),
                ("Bells: ", "italic"),
                format_bell_count(final_state_today["bells"]),
                " | ",
                ("Miles: ", "italic"),
                format_nook_miles(final_state_today["nook_miles"]),
                " | ",
                ("AvgFriend: ", "italic"),
                format_friendship(final_state_today["avg_friendship"]),
            )
            console.print(Padding(progress_text, (0, 1)), style="on grey23")
        env.advance_day_cycle()

    console.print(
        Panel(
            "[bold magenta]--- Simulation Ended --- :checkered_flag:",
            title="Simulation Complete",
            expand=False,
        )
    )
    final_state = env.get_state()

    summary_table = Table(
        title=f":bar_chart: Final State after {days_to_simulate} days",
        show_header=True,
        header_style="bold yellow",
    )
    summary_table.add_column("Metric", style="dim", width=30)
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Total Bells", format_bell_count(final_state["bells"]))
    summary_table.add_row(
        "Total Nook Miles", format_nook_miles(final_state["nook_miles"])
    )
    summary_table.add_row(
        "Average Villager Friendship", format_friendship(final_state["avg_friendship"])
    )

    console.print(summary_table)

    villager_final_table = Table(
        title=":busts_in_silhouette: Final Villager Friendships",
        show_header=True,
        header_style="bold cyan",
    )
    villager_final_table.add_column("Villager Name", style="italic")
    villager_final_table.add_column("Friendship Level", justify="center")

    for v in env.villagers:
        villager_final_table.add_row(v.name, format_friendship(v.friendship_level))

    console.print(villager_final_table)

    # If you want to keep the original matplotlib plots:
    # plot_simulation_results(rewards_log=total_rewards_log)


if __name__ == "__main__":
    console.print(
        Panel(
            Text("Welcome to the Animal Crossing Simulator!", justify="center"),
            style="bold green on black",
        )
    )
    try:
        # Example: Simulate for a small number of days to see rich output
        run_simulation(days_to_simulate=2)
    except Exception:
        console.print_exception(show_locals=True)
