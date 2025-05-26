
# --- 5. Simulation Loop ---
from enigma_engines.agent import SocialEconomistAgent
from enigma_engines.core_classes import ACNHEnvironment, ACNHItemDataset
from enigma_engines.plotting_utils import plot_simulation_results


def run_simulation(days_to_simulate):
    print("--- Starting ACNH Social Economist Agent Simulation ---")
    
    dataset = ACNHItemDataset() # Load once
    num_villagers = 3
    env = ACNHEnvironment(num_villagers=num_villagers, dataset=dataset)
    agent = SocialEconomistAgent(dataset=dataset, num_villagers_on_island=num_villagers)

    env.reset() # Initialize environment

    total_rewards_log = {"friendship": [], "bells": [], "nook_miles": []}
    agent_state_log = []


    for day in range(days_to_simulate):
        current_env_state = env.get_state()
        print(f"\n--- Day {env.current_day} ({current_env_state['date_str']}) ---")
        print(f"State: Bells={current_env_state['bells']}, NookMiles={current_env_state['nook_miles']}, AvgFriendship={current_env_state['avg_friendship']:.2f}")
        if current_env_state['turnip_buy_price'] > 0: print(f"Daisy Mae selling turnips at: {current_env_state['turnip_buy_price']}")
        if current_env_state['turnip_sell_price'] > 0: print(f"Nooklings buying turnips at: {current_env_state['turnip_sell_price']}")
        print(f"Available Nook Tasks: {current_env_state['available_nook_tasks']}")
        for v_obj in env.villagers: print(f"  - {v_obj.name}: {v_obj.friendship_level}")


        action = agent.choose_action(current_env_state, env.villagers)
        #print(f"Action chosen: {action}")

        # Environment processes action and returns rewards for *that step*
        reward_friendship, reward_bells, reward_nook_miles = env.step(action, current_env_state)
        
        # Log cumulative status for plotting/analysis later
        final_state_today = env.get_state()
        total_rewards_log["friendship"].append(final_state_today["avg_friendship"])
        total_rewards_log["bells"].append(final_state_today["bells"])
        total_rewards_log["nook_miles"].append(final_state_today["nook_miles"])
        agent_state_log.append(final_state_today) # Log the full state after action

        if day % 100 == 0 or day == days_to_simulate -1 : # Print progress
            print(f"Day {env.current_day} ({final_state_today['date_str']}): "
                  f"Bells: {final_state_today['bells']}, "
                  f"Miles: {final_state_today['nook_miles']}, "
                  f"AvgFriend: {final_state_today['avg_friendship']:.2f}")


    print("\n--- Simulation Ended ---")
    final_state = env.get_state()
    print(f"Final State after {days_to_simulate} days:")
    print(f"  Bells: {final_state['bells']}")
    print(f"  Nook Miles: {final_state['nook_miles']}")
    print(f"  Average Villager Friendship: {final_state['avg_friendship']:.2f}")
    print("  Villager Friendships:")
    for v in env.villagers:
        print(f"    {v.name}: {v.friendship_level}")

    # plot_simulation_results(rewards_log=total_rewards_log)

if __name__ == "__main__":
    run_simulation(days_to_simulate=100)