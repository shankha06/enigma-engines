# --- 5. Simulation Loop ---
try:
    from enigma_engines.animal_crossing.core.agent import Multi_Objective_Agent
    from enigma_engines.animal_crossing.core.environment import ACNHEnvironment
    from enigma_engines.animal_crossing.core.load_data import ACNHItemDataset
except ImportError as e:
    raise ImportError(f"Required module could not be imported: {e}")

# Rich library imports
from typing import Any, Dict, List

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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


def _print_day_summary_panel(
    console_instance: Console, panel_title: str, info_elements: list
):
    """
    Prints the day's summary information within a Rich Panel.
    Handles a list of Rich renderables (Text, Table, Panel, etc.).

    Args:
        console_instance: The Rich Console object to use for printing.
        panel_title: The title for the panel.
        info_elements: A list of Rich renderables to display.
    """
    panel_content_renderables = []
    for item in info_elements:
        if hasattr(item, "__rich_console__"):  # Check if it's a Rich renderable
            panel_content_renderables.append(item)
        else:  # Convert simple strings to Text
            panel_content_renderables.append(Text(str(item)))

    content_group = Group(*panel_content_renderables)

    console_instance.print(
        Panel(
            Padding(content_group, (1, 2)),  # Padding around the group
            title=panel_title,
            border_style="cyan",
            expand=False,  # Prevent panel from taking full width if content is small
        )
    )


def print_summary_table(
    console_instance: Console,
    final_state: dict,
    days_to_simulate: int,
    environment: ACNHEnvironment,
):
    """
    Generates and prints the final summary table.

    Args:
        console_instance: The Rich Console object to use for printing.
        final_state: Dictionary containing the final simulation state.
        days_to_simulate: Number of days that were simulated.
    """
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

    console_instance.print(summary_table)

    villager_final_table = Table(
        title=":busts_in_silhouette: Final Villager Friendships",
        show_header=True,
        header_style="bold cyan",
    )
    villager_final_table.add_column("Villager Name", style="italic")
    villager_final_table.add_column("Friendship Level", justify="center")

    for v in environment.villagers:
        villager_final_table.add_row(v.name, format_friendship(v.friendship_level))

    console_instance.print(villager_final_table)


def _display_daily_report(
    console_instance: Console,
    environment: ACNHEnvironment,  # Still useful for direct access if needed beyond state
    current_env_state: Dict[str, Any],  # State *after* actions for logical_day_num
    actions_log: List[Dict[str, Any]],
    logical_day_num: int,  # The simulation loop's day index
):
    """
    Prepares and displays the full daily report/summary panel, including actions.

    Args:
        console_instance: The Rich Console object.
        environment: The ACNHEnvironment instance.
        current_env_state: The current state dictionary from environment.get_state().
        actions_log: A list of action dictionaries performed during the logical day.
        logical_day_num: The logical day number from the simulation loop.
    """
    day_panel_title = (
        f":calendar: Report for Logical Day {logical_day_num} "
        f"(Env. Day {current_env_state['current_day']}, Date: {current_env_state['current_date']}) "
        f":sunrise_over_mountains:"
    )

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

    # Villager Actions Table
    if actions_log:
        actions_table = Table(
            title=":performing_arts: Villager Actions This Logical Day",
            show_header=True,
            header_style="bold magenta",
            expand=False,
        )
        actions_table.add_column(
            "Villager", style="italic yellow", width=15, overflow="fold"
        )
        actions_table.add_column("Action Type", style="cyan", width=20, overflow="fold")
        actions_table.add_column("Details", overflow="fold")

        for action_item in actions_log:
            actor = action_item.get("villager_name", "N/A")
            action_type = action_item.get("type", "UNKNOWN")

            details_parts = []
            if action_item.get("target_villager_name"):
                details_parts.append(f"Target: {action_item['target_villager_name']}")
            if action_item.get("gift_name"):
                details_parts.append(f"Gift: {action_item['gift_name']}")
            if action_item.get("task_name"):
                details_parts.append(f"Task: {action_item['task_name']}")
            if action_item.get("crop_name"):
                details_parts.append(f"Crop: {action_item['crop_name']}")
            if action_item.get("plot_id") is not None:
                details_parts.append(f"Plot: {action_item['plot_id']}")
            if action_item.get("quantity"):
                details_parts.append(f"Qty: {action_item['quantity']}")
            if action_item.get("items_to_sell_list"):
                items_summary = ", ".join(
                    [
                        f"{item['name']}(x{item['quantity']})"
                        for item in action_item["items_to_sell_list"][:2]
                    ]
                )
                if len(action_item["items_to_sell_list"]) > 2:
                    items_summary += "..."
                details_parts.append(f"Items: {items_summary}")

            details_str = "; ".join(details_parts)
            if action_type == "IDLE":
                details_str = "[dim]Took a break[/dim]"

            actions_table.add_row(
                actor, action_type, details_str if details_str else "[dim]-[/dim]"
            )
        day_info.append(actions_table)
    else:
        day_info.append(":zzz: No villager actions logged for this logical day.")

    if current_env_state["active_nook_tasks"]:
        tasks_table = Table(
            title=":scroll: Available Nook Tasks",
            show_header=True,
            header_style="bold blue",
            expand=False,
        )
        tasks_table.add_column("Task Name", style="dim", width=30, overflow="fold")
        tasks_table.add_column("Miles", justify="right")
        tasks_table.add_column("Category", justify="right", overflow="fold")
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
        expand=False,
    )
    villager_table.add_column("Villager Name", style="italic")
    villager_table.add_column("Friendship", justify="center")

    for v_obj in environment.villagers:
        villager_table.add_row(v_obj.name, format_friendship(v_obj.friendship_level))
    day_info.append(villager_table)

    _print_day_summary_panel(console_instance, day_panel_title, day_info)


def run_simulation(days_to_simulate: int, actions_per_day: int = None):
    """
    Run the Animal Crossing simulation with per-villager actions.

    Args:
        days_to_simulate: Number of days to simulate
        actions_per_day: Maximum number of villagers that can act per day.
                         If None, all villagers will act each day.
    """
    import random  # For shuffling villagers

    console.print(
        Panel(
            "[bold magenta]--- Starting ACNH Social Economist Agent Simulation --- :rocket:",
            title="Simulation Start",
            expand=False,
        )
    )

    dataset = ACNHItemDataset()  # Load once
    num_villagers = 10
    env = ACNHEnvironment(num_villagers=num_villagers, dataset=dataset)
    agent = Multi_Objective_Agent(
        dataset=dataset, num_villagers_on_island=num_villagers
    )

    env.reset()  # Initialize environment

    total_rewards_log = {"friendship": [], "bells": [], "nook_miles": []}

    # If actions_per_day is not specified, allow all villagers to act
    if actions_per_day is None:
        actions_per_day = num_villagers

    for day_idx in range(days_to_simulate):  # This is the master day counter
        current_env_state_at_loop_start = (
            env.get_state()
        )  # State at the beginning of the logical day

        # Get all villagers and shuffle them for random action order
        villagers_for_today = list(env.villagers)
        random.shuffle(villagers_for_today)

        # Track actions for this logical day for the report
        actions_for_this_logical_day = []
        villagers_acted_count_this_logical_day = 0

        day_was_advanced_by_agent = False

        # Limit the number of villagers that can act today
        max_villagers_to_act = min(actions_per_day, len(villagers_for_today))

        for villager_idx, acting_villager in enumerate(villagers_for_today):
            if villagers_acted_count_this_logical_day >= max_villagers_to_act:
                break  # Reached max number of villagers for the day

            # Get fresh state for each villager's decision
            current_env_state_for_decision = env.get_state()

            # If day was already advanced, stop processing villagers
            if (
                current_env_state_for_decision["current_day"]
                > current_env_state_at_loop_start["current_day"]
            ):
                day_was_advanced_by_agent = True
                break

            # Choose action for this specific villager, considering diversity
            action = agent.choose_action(
                current_env_state_for_decision,
                env.villagers,
                agent_name=acting_villager.name,
                actions_taken_today_by_others=actions_for_this_logical_day,
            )

            # Add action to log for the report
            actions_for_this_logical_day.append(action.copy())

            if action["type"] == "IDLE":
                # Still count this villager as having acted
                villagers_acted_count_this_logical_day += 1
                continue

            # Execute the action
            _, _, _ = env.step(
                action, acting_villager
            )  # Pass acting_villager for direct use

            # Track this villager's action
            villagers_acted_count_this_logical_day += 1

            # If the action taken was ADVANCE_DAY, the environment's day counter will increment
            if action["type"] == "ADVANCE_DAY":
                day_was_advanced_by_agent = True
                break  # End actions for this `day_idx`

        # --- End of Actions for `day_idx` ---
        state_after_actions = (
            env.get_state()
        )  # State after all actions for this logical day are done

        # Display the daily report for the logical day that just finished
        _display_daily_report(
            console,
            env,
            state_after_actions,  # Current state of the environment
            actions_for_this_logical_day,  # Actions performed during this logical day
            day_idx,  # The logical day number
        )

        # Log overall daily results
        total_rewards_log["friendship"].append(state_after_actions["avg_friendship"])
        total_rewards_log["bells"].append(state_after_actions["bells"])
        total_rewards_log["nook_miles"].append(state_after_actions["nook_miles"])

        if day_idx % 100 == 0 or day_idx == days_to_simulate - 1:
            progress_text = Text.assemble(
                (
                    f"End of Day {day_idx} (Env Day: {state_after_actions['current_day']}, Date: {state_after_actions['current_date']}): ",
                    "bold",
                ),
                ("Bells: ", "italic"),
                format_bell_count(state_after_actions["bells"]),
                " | ",
                ("Miles: ", "italic"),
                format_nook_miles(state_after_actions["nook_miles"]),
                " | ",
                ("AvgFriend: ", "italic"),
                format_friendship(state_after_actions["avg_friendship"]),
            )
            console.print(
                Padding(progress_text, (0, 0, 1, 0)), style="on grey19"
            )  # Added bottom padding

        # If the day was NOT advanced by an agent's ADVANCE_DAY action during its turns,
        # and the environment's current day is still effectively `day_idx`, advance it now.
        if (
            not day_was_advanced_by_agent
            and env.get_state()["current_day"]
            == current_env_state_at_loop_start["current_day"]
        ):
            env.advance_day_cycle()
    # --- End of Simulation ---
    # Final summary at the end of the simulation

    console.print(
        Panel(
            "[bold magenta]--- Simulation Ended --- :checkered_flag:",
            title="Simulation Complete",
            expand=False,
        )
    )
    final_state_at_end = env.get_state()
    print_summary_table(console, final_state_at_end, days_to_simulate, env)

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
        # Allow all villagers to act each day (actions_per_day=None)
        run_simulation(days_to_simulate=5, actions_per_day=None)
    except Exception:
        console.print_exception(show_locals=True)
