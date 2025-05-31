# Rich library imports
from typing import Any, Dict, List

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from enigma_engines.village_simulation.agents.action_plan import ActionPlan
from enigma_engines.village_simulation.agents.villager import Villager

# --- Rich Console Initialization ---
console = Console()


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


def _display_daily_report(
    console_instance: Console,
    logical_day_num: int,
    current_env_state: Dict[str, Any],
    villagers: List[Villager],
):
    """
    Prepares and displays the full daily report/summary panel.
    Display most relevant information about the current logical day in the village simulation.
    This includes leaderboards of villagers with most profits, losses on that day.
    Display includes the logical day number, current environment state, and a summary of actions taken.

    """
    day_panel_title = (
        f":calendar: Report for Logical Day {logical_day_num} "
        f"(Env. Day {current_env_state['current_day']}, Date: {current_env_state['current_date']}) "
        f":sunrise_over_mountains:"
    )

    ...
