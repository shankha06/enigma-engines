
# --- 4. Social Economist Agent (Rule-Based Multi-Objective) ---
from enigma_engines.core_classes import ACNHEnvironment, ACNHItemDataset


class SocialEconomistAgent:
    def __init__(self, dataset, num_villagers_on_island):
        self.dataset = dataset
        # Weights for objectives - how much the agent cares about each.
        # These could be learned or adapted in a more complex RL agent.
        self.weights = {
            "friendship": 0.4,
            "bells": 0.4,
            "nook_miles": 0.2
        }
        # Target thresholds - agent might try to bring lagging objectives up
        self.friendship_target_min = 50 
        self.bells_target_min = 5000
        self.nook_miles_target_min = 1000


    def choose_action(self, state, villagers_details):
        """
        A rule-based approach to select an action based on current state and objectives.
        A true MORL agent would use a learned policy (e.g., Q-values for a composite reward).
        """
        # --- Turnip Logic (High Priority if conditions are right) ---
        # Sell if profitable
        if state["turnip_sell_price"] > 150 and state["turnips_owned"] > 0: # Good profit margin
             #print(f"Agent: Decided to sell {state['turnips_owned']} turnips at {state['turnip_sell_price']}")
             return {"type": "SELL_TURNIPS"}
        
        # Buy on Sunday if price is good and has bells
        if state["turnip_buy_price"] > 0 and state["turnip_buy_price"] <= 100 and state["bells"] > (state["turnip_buy_price"] * 100): # Buy 100 if affordable
            #print(f"Agent: Decided to buy 100 turnips at {state['turnip_buy_price']}")
            return {"type": "BUY_TURNIPS", "quantity": 100}

        # --- Objective-driven actions ---
        possible_actions = []

        # 1. Friendship: Gift someone if average is low or a specific villager is very low
        avg_friendship = state["avg_friendship"]
        lowest_friend_villager = min(villagers_details, key=lambda v: v.friendship_level) if villagers_details else None

        if lowest_friend_villager and lowest_friend_villager.friendship_level < self.friendship_target_min:
            gift_name, gift_details = self.dataset.get_random_gift_option() # Get a random good gift
            if state["bells"] >= gift_details["cost"] and lowest_friend_villager.last_gifted_day != state["day"]:
                possible_actions.append({
                    "action": {"type": "GIVE_GIFT", "villager_name": lowest_friend_villager.name, "gift_name": gift_name},
                    "score": self.weights["friendship"] * (gift_details["friendship_points"] / (gift_details["cost"] + 0.01)) # Value per bell
                })
        
        # 2. Nook Miles: Do a task if miles are low or tasks are easy
        if state["nook_miles"] < self.nook_miles_target_min and state["available_nook_tasks"]:
            task_to_do = state["available_nook_tasks"][0] # Pick first available
            reward_estimate = self.dataset.nook_miles_tasks_daily.get(task_to_do, 0)
            possible_actions.append({
                "action": {"type": "DO_NOOK_MILES_TASK", "task_name": task_to_do},
                "score": self.weights["nook_miles"] * reward_estimate 
            })

        # 3. Bells: Work for bells if low
        if state["bells"] < self.bells_target_min:
            # Estimate "work for bells" action value
            possible_actions.append({
                "action": {"type": "WORK_FOR_BELLS"},
                "score": self.weights["bells"] * 1000 # Avg expected earning
            })
        
        # --- Fallback/General Actions ---
        if not possible_actions: # If no urgent needs met by specific actions above
            # Default to trying to earn bells if nothing else pressing
            if state["bells"] < 20000 : # Arbitrary threshold to keep earning
                 possible_actions.append({"action": {"type": "WORK_FOR_BELLS"}, "score": self.weights["bells"] * 500}) # Lower score if not urgent
            # Or try to complete any Nook Miles task
            elif state["available_nook_tasks"]:
                task_to_do = state["available_nook_tasks"][0]
                reward_estimate = self.dataset.nook_miles_tasks_daily.get(task_to_do, 0)
                possible_actions.append({
                    "action": {"type": "DO_NOOK_MILES_TASK", "task_name": task_to_do},
                    "score": self.weights["nook_miles"] * reward_estimate * 0.5 # Lower priority
                })


        # Choose the action with the highest "score" (simple heuristic for multi-objective)
        if possible_actions:
            best_action_info = max(possible_actions, key=lambda x: x["score"])
            #print(f"Agent: Chose {best_action_info['action']['type']} with score {best_action_info['score']:.2f}")
            return best_action_info["action"]
        
        #print("Agent: Decided to IDLE")
        return {"type": "IDLE"} # Fallback if no other action seems beneficial