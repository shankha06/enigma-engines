"""
Simulation entry point for the medieval village simulation.
This script runs a full simulation of village operations using the VillageManager and its inbuilt systems.
"""
import typer
from enigma_engines.village_simulation.simulation_engine.village_manager import VillageManager

def run_village_simulation(
    num_days: int = 30,
    num_villagers: int = 15,
    forest_size_sqkm: float = 3.0,
    river_name: str = "Silverstream",
    village_name: str = "Oakhaven"
):
    """
    Runs the full village simulation for a specified number of days.
    """
    # Initialize the village manager
    village = VillageManager(name=village_name)
    village.initialize_village(
        num_villagers=num_villagers,
        forest_size_sqkm=forest_size_sqkm,
        river_name=river_name
    )

    for day in range(1, num_days + 1):
        village.simulate_daily_tick()
        # Optionally display a rich daily report (if running in a rich-compatible terminal)
        if hasattr(village, "_display_daily_report_rich"):
            village._display_daily_report_rich()
        # Log detailed villager status every 5 days
        # if day % 5 == 0:
        #     from enigma_engines.village_simulation.utilities.logger import backend_logger
        #     backend_logger.info(f"--- Villager Status Check - End of Day {day} ---")
        #     if not village.villagers:
        #         backend_logger.info("No villagers left.")
        #         break
        #     for v_id, v in village.villagers.items():
        #         inv_summary = {item.name: qty for item, qty in v.inventory.items()}
        #         backend_logger.info(
        #             f"  {v.name} ({v.occupation}, {v.age}yo): H:{v.health} E:{v.energy} Hap:{v.happiness} M:{v.money:.1f} Skills:{v.skills} Inv:{inv_summary} Alive:{v.is_alive}"
        #         )
    # Final summary
    from enigma_engines.village_simulation.utilities.logger import backend_logger
    backend_logger.info("\n===== SIMULATION FINISHED =====")
    backend_logger.info(f"Final Village State for '{village.name}' on {village.current_date.strftime('%Y-%m-%d')}:")
    backend_logger.info(f"  Population: {village.total_population}")
    backend_logger.info(f"  Avg Happiness: {village.average_happiness:.2f}, Avg Health: {village.average_health:.2f}")
    backend_logger.info(f"  Treasury: {village.treasury:.2f}")
    backend_logger.info(f"  Food Storage: {[(f.name,q) for f,q in village.food_storage.items()]}")
    backend_logger.info(f"  Resource Storage: {[(r.name,q) for r,q in village.resource_storage.items()]}")
    backend_logger.info(f"  Village Attractiveness: {village.village_attractiveness:.2f}")

if __name__ == "__main__":
    run_village_simulation(
        village_name="Greendale",
        num_days=10,
        num_villagers=20, forest_size_sqkm=5.0, river_name="Crystal River")