# --- 5. Simulation Loop ---
from enigma_engines.animal_crossing.core.agent import Multi_Objective_Agent
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


def _print_day_summary_panel(console_instance: Console, panel_title: str, info_elements: list):
    """
    Prints the day's summary information within a Rich Panel.

    Args:
        console_instance: The Rich Console object to use for printing.
        panel_title: The title for the panel.
        info_elements: A list of Rich renderables (Text, Table, strings) to display.
    """
    content_to_render = (
        "\n".join(str(item) for item in info_elements)
        if not isinstance(info_elements[0], Table)
        and not isinstance(info_elements[0], Text)
        else Columns(info_elements, expand=True, equal=True)
    )

    console_instance.print(
        Panel(
            Padding(content_to_render, (1, 2)),
            title=panel_title,
            border_style="cyan",
        )
    )


def print_summary_table(console_instance: Console, final_state: dict, days_to_simulate: int, environment: ACNHEnvironment):
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


def _display_daily_report(console_instance: Console, environment: ACNHEnvironment):
    """
    Prepares and displays the full daily report/summary panel.

    Args:
        console_instance: The Rich Console object.
        environment: The ACNHEnvironment instance for the current simulation state.
    """
    current_env_state = environment.get_state()
    day_panel_title = f":calendar: Day {environment.current_day} ({current_env_state['current_date']}) :sunrise_over_mountains:"

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

    for v_obj in environment.villagers:
        villager_table.add_row(
            v_obj.name, format_friendship(v_obj.friendship_level)
        )
    day_info.append(villager_table)

    _print_day_summary_panel(console_instance, day_panel_title, day_info)


def run_simulation(days_to_simulate, actions_per_day=15):
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
    agent = Multi_Objective_Agent(dataset=dataset, num_villagers_on_island=num_villagers)

    env.reset()  # Initialize environment

    total_rewards_log = {"friendship": [], "bells": [], "nook_miles": []}
    agent_state_log = []

    env.reset()

    total_rewards_log = {"friendship": [], "bells": [], "nook_miles": []}
    # agent_state_log = [] # Log the state at the end of each full day

    for day_idx in range(days_to_simulate): # This is the master day counter
        _display_daily_report(console, env) # Report at the start of the logical day

        day_was_advanced_by_agent = False

        for action_num in range(actions_per_day):
            current_env_state = env.get_state()

            # If the environment's day has already passed beyond the current 'day_idx',
            # it means an "ADVANCE_DAY" action was taken in a previous sub-step.
            # So, break from taking more actions for this 'day_idx'.
            if current_env_state["current_day"] > day_idx:
                day_was_advanced_by_agent = True # Mark that agent advanced the day
                break

            action = agent.choose_action(current_env_state, env.villagers)
            
            action_description = f"{action['type']}"
            if action.get('target_villager_name'): action_description += f" -> {action['target_villager_name']}"
            if action.get('gift_name'): action_description += f" (Gift: {action['gift_name']})"
            if action.get('task_name'): action_description += f" (Task: {action['task_name']})"
            if action.get('crop_name'): action_description += f" (Crop: {action['crop_name']})"
            if action.get('quantity'): action_description += f" (Qty: {action['quantity']})"
            
            console.print(f"  ↪ Day {current_env_state['current_day']} | Turn {action_num + 1}/{actions_per_day}: [italic]{action_description}[/italic]")

            if action["type"] == "IDLE":
                console.print("    Agent chose IDLE. Considering next turn or ending day.")
                # If agent is consistently IDLE, it will just use up its turns.
                # No need to break early unless IDLE means "I want to end my day now".
                # If ADVANCE_DAY is a choosable action, agent should pick that to end day.
                continue # Takes up an action point but does nothing

            # --- Execute Action ---
            # The 'agent_state' parameter for env.step in your original code was current_env_state (a dict).
            # If env.step uses action["villager_name"] to resolve the actor, this is fine.
            # The Multi_Objective_Agent should set action["villager_name"] = self.agent_name.
            # The original was: reward_friendship, reward_bells, reward_nook_miles = env.step(action, current_env_state)
            # Let's stick to that pattern for consistency with your setup.
            # Ensure your ACNHEnvironment.step can correctly identify the 'acting_villager'
            # from action["villager_name"] if the second argument is not an ACNHVillager instance.
            _, _, _ = env.step(action, None) # Pass None for agent_obj, rely on action["villager_name"]

            # If the action taken was ADVANCE_DAY, the environment's day counter will increment.
            if action["type"] == "ADVANCE_DAY":
                day_was_advanced_by_agent = True
                console.print(f"    [bold yellow]Agent advanced day. Moving to next simulation day.[/bold yellow]")
                break # End actions for this `day_idx`

        # --- End of Actions for `day_idx` ---
        final_state_today = env.get_state() # State after all actions for this logical day are done

        # Log overall daily results
        total_rewards_log["friendship"].append(final_state_today["avg_friendship"])
        total_rewards_log["bells"].append(final_state_today["bells"])
        total_rewards_log["nook_miles"].append(final_state_today["nook_miles"])
        # agent_state_log.append(final_state_today) # Log if needed for detailed daily state history

        if day_idx % 100 == 0 or day_idx == days_to_simulate - 1:
            progress_text = Text.assemble(
                (f"End of Day {day_idx} (Env Day: {final_state_today['current_day']}, Date: {final_state_today['current_date']}): ", "bold"),
                ("Bells: ", "italic"), format_bell_count(final_state_today["bells"]), " | ",
                ("Miles: ", "italic"), format_nook_miles(final_state_today["nook_miles"]), " | ",
                ("AvgFriend: ", "italic"), format_friendship(final_state_today["avg_friendship"]),
            )
            console.print(Padding(progress_text, (0, 0, 1, 0)), style="on grey19") # Added bottom padding

        # If the day was NOT advanced by an agent's ADVANCE_DAY action during its turns,
        # and the environment's current day is still effectively `day_idx`, advance it now.
        if not day_was_advanced_by_agent and env.get_state()["current_day"] == day_idx:
            env.advance_day_cycle()
            console.print(f"    End of day {day_idx} reached. Advancing to day {env.get_state()['current_day']}, Date: {env.get_state()['current_date']}.")
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
        run_simulation(days_to_simulate=15)
    except Exception:
        console.print_exception(show_locals=True)
