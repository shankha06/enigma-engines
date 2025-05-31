"""
Example usage of the ActionPlan system for villagers.
This demonstrates how villagers can plan and execute various actions.
"""

from enigma_engines.village_simulation.agents.action_plan import (
    ActionPlan,
    ActionType,
    create_buying_action,
    create_eating_action,
    create_interaction_action,
    create_sleep_action,
    create_working_action,
)
from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.resources.food import apple, bread, fish
from enigma_engines.village_simulation.resources.clothing import daily_clothes


def demonstrate_action_planning():
    """Demonstrates the action planning system for villagers."""

    # Create a villager
    villager = Villager(
        name="John Smith",
        age=25,
        skills={"farming": 3, "fishing": 2, "crafting": 1},
        inventory={bread: 2, apple: 1},
        money=50.0,
        health=60,
        happiness=70,
        energy=80,
    )

    print(f"Initial state of {villager.name}:")
    print(
        f"  Health: {villager.health}, Happiness: {villager.happiness}, Energy: {villager.energy}"
    )
    print(f"  Money: ${villager.money}")
    print(
        f"  Inventory: {[(item.name, qty) for item, qty in villager.inventory.items()]}"
    )
    print()

    # Create some action plans
    print("Creating action plans...")

    # Plan 1: Eat some bread
    eat_action = create_eating_action(bread)
    print(f"1. {eat_action}")

    # Plan 2: Buy fish
    buy_fish_action = create_buying_action(fish, quantity=2)
    print(f"2. {buy_fish_action}")

    # Plan 3: Work for 8 hours
    work_action = create_working_action("Farm", duration=8)
    print(f"3. {work_action}")

    # Plan 4: Sleep for 8 hours
    sleep_action = create_sleep_action(duration=8)
    print(f"4. {sleep_action}")

    # Plan 5: Interact with another villager
    interact_action = create_interaction_action("Mary Johnson", duration=2)
    print(f"5. {interact_action}")
    print()

    # Add actions to villager's plan
    villager.add_action_to_plan(eat_action)
    villager.add_action_to_plan(buy_fish_action)
    villager.add_action_to_plan(work_action)
    villager.add_action_to_plan(sleep_action)
    villager.add_action_to_plan(interact_action)

    print(f"Current action plan (sorted by priority):")
    for i, action in enumerate(villager.current_action_plan, 1):
        print(f"  {i}. {action}")
    print()

    # Execute actions
    print("Executing actions...")
    while villager.current_action_plan:
        next_action = villager.get_next_planned_action()
        if next_action:
            print(f"\nExecuting: {next_action}")
            success = villager.execute_action(next_action)
            if success:
                print(f"  Success! Current state:")
                print(
                    f"    Health: {villager.health}, Happiness: {villager.happiness}, Energy: {villager.energy}"
                )
                print(f"    Money: ${villager.money}")
            else:
                print(f"  Failed to execute action")
                # Remove the action from the plan if it can't be executed
                villager.current_action_plan.remove(next_action)
        else:
            print("\nNo executable actions remaining in plan")
            break

    print(f"\nFinal state of {villager.name}:")
    print(
        f"  Health: {villager.health}, Happiness: {villager.happiness}, Energy: {villager.energy}"
    )
    print(f"  Money: ${villager.money}")
    print(
        f"  Inventory: {[(item.name, qty) for item, qty in villager.inventory.items()]}"
    )
    print(f"  Actions completed: {len(villager.action_history)}")

    # Demonstrate automatic action planning
    print("\n" + "=" * 50)
    print("Demonstrating automatic action planning...")

    # Set villager to a state that needs attention
    villager.health = 30
    villager.energy = 20
    villager.money = 100

    print(
        f"\nVillager state: Health={villager.health}, Energy={villager.energy}, Money=${villager.money}"
    )

    # Let the villager plan their next action
    next_action = villager.plan_next_action()
    if next_action:
        print(f"Villager plans to: {next_action}")
        print(f"This action has priority: {next_action.priority}/10")

    # Create a custom action with specific requirements and impact
    print("\n" + "=" * 50)
    print("Creating a custom action...")

    custom_action = ActionPlan(
        action_type=ActionType.FISHING,
        duration=4,
        priority=6,
        requirements={"min_health": 40, "min_energy": 30},
        location="River",
    )

    print(f"Custom fishing action: {custom_action}")
    print(f"Can execute with current state? {custom_action.can_execute(villager)}")

    # Restore some energy and health
    villager.energy = 50
    villager.health = 45
    print(f"\nAfter rest: Health={villager.health}, Energy={villager.energy}")
    print(f"Can execute now? {custom_action.can_execute(villager)}")


if __name__ == "__main__":
    demonstrate_action_planning()
