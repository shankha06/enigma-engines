from datetime import datetime
from typing import Dict, Any, List, Optional
import math

from enigma_engines.animal_crossing.core.load_data import ACNHItemDataset
from enigma_engines.animal_crossing.core.villager import ACNHVillager
class Multi_Objective_Agent:
    # Define constants for new constraints
    PLANTER_FOCUS_PERCENTAGE = 0.20  # 20% of villagers encouraged to plant
    PLANTER_SCORE_BONUS_FACTOR = 1.8
    FORCE_GIFT_SCORE_BONUS_FACTOR = 250
    FISHING_SPOT_POPULATION_RATIO = 0.25
    
    def __init__(self, dataset: ACNHItemDataset, num_villagers_on_island: int):
        self.dataset = dataset

        self.weights = {"friendship": 0.50, "bells": 0.35, "nook_miles": 0.15} # Emphasize friendship more

        self.friendship_target_min = 70 # Increased target
        self.bells_target_min = 4000
        self.nook_miles_target_min = 800

        # Track last action and repetition counter per villager
        self.villager_last_action_details: Dict[str, Dict[str, Any]] = {}
        self.villager_action_repetition_counter: Dict[str, int] = {}
        self.num_villagers_on_island = num_villagers_on_island

    def _is_action_repetitive(self, current_action_details: Dict[str, Any], agent_name: str) -> bool:
        """
        Checks if the current action is too similar to the last one for the specific agent.
        
        Args:
            current_action_details (Dict[str, Any]): The current action being considered
            agent_name (str): The name of the agent/villager performing the action
        Returns:
            bool: True if the action is repetitive, False otherwise
        """
        last_action = self.villager_last_action_details.get(agent_name)
        if not last_action:
            return False
        if current_action_details.get("type") != last_action.get("type"):
            return False
        
        # More specific checks for repetitive actions like gifting/talking to the SAME villager
        if current_action_details.get("type") in ["GIVE_GIFT", "TALK_TO_VILLAGER"]:
            if current_action_details.get("target_villager_name") == last_action.get("target_villager_name"):
                return True
        # Could add more checks for other action types if needed
        return False


    def choose_action(self, state: Dict[str, Any], villagers_details_list: List[ACNHVillager], agent_name: str ="Player", actions_taken_today_by_others: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Choose the best action based on the current state, villagers' details, and actions taken by others.

        Args:
            state (Dict[str, Any]): The current state of the environment.
            villagers_details_list (List[ACNHVillager]): List of villagers' details.
            agent_name (str): The name of the villager performing the action.
            actions_taken_today_by_others (Optional[List[Dict[str, Any]]]): 
                List of actions already performed by other villagers on the current day.
        Returns:
            Dict[str, Any]: The chosen action details.
        """
        possible_actions_with_scores: List[Dict[str, Any]] = []
        
        # --- Pre-calculation for new constraints ---
        num_total_villagers = len(villagers_details_list)
        # Fishing limit: Calculate based on current population
        fishing_spots_limit_today = math.ceil(num_total_villagers * self.FISHING_SPOT_POPULATION_RATIO)
        
        go_fishing_actions_count = 0
        give_gift_actions_count = 0
        
        if actions_taken_today_by_others:
            for action_info in actions_taken_today_by_others:
                action_type_taken = action_info.get('type')
                if action_type_taken == "GO_FISHING":
                    go_fishing_actions_count += 1
                elif action_type_taken == "GIVE_GIFT":
                    give_gift_actions_count += 1
        
        # Determine if this agent should be a "designated planter" for bonus
        is_designated_planter_for_bonus = False
        if num_total_villagers > 0:
            planter_candidate_count = math.ceil(num_total_villagers * self.PLANTER_FOCUS_PERCENTAGE)
            try:
                agent_index_in_list = [v.name for v in villagers_details_list].index(agent_name)
                if agent_index_in_list < planter_candidate_count:
                    is_designated_planter_for_bonus = True
            except (ValueError, AttributeError):
                # Agent not found in list or villagers don't have name attribute
                pass

        def get_urgency_multiplier(current_value, target_min, default=1.0, low_multiplier=5, very_low_multiplier=10):
            if current_value < target_min / 2: return very_low_multiplier
            if current_value < target_min: return low_multiplier
            return default

        friendship_urgency = get_urgency_multiplier(state.get("avg_friendship", 100), self.friendship_target_min)
        bells_urgency = get_urgency_multiplier(state.get("bells", 0), self.bells_target_min, very_low_multiplier=2.5) # Higher urgency if very broke
        nook_miles_urgency = get_urgency_multiplier(state.get("nook_miles", 0), self.nook_miles_target_min)

        current_day = state.get("day", -1)
        current_bells = state.get("bells", 0)
        player_inventory = state.get("player_inventory", []) # Assumed format: [{"name": str, "quantity": int, "sell_price": int, ...}]

        # --- 1. Evaluate Economic Actions (Bells & Turnips) ---
        # SELL_TURNIPS
        if state.get("turnips_owned", 0) > 0 and state.get("turnip_sell_price", 0) > 0:
            is_saturday = datetime.strptime(state.get("date_str", "2025-01-01 (Monday)")[:10], "%Y-%m-%d").weekday() == 5
            # Sell if price is good or it's Saturday (last chance)
            # Assume turnip_buy_price_paid_by_agent is available in state if turnips were bought
            agent_turnip_buy_price = state.get("turnip_buy_price_paid_by_agent", 100) # Default if not tracked
            if state["turnip_sell_price"] > 120 or \
               (is_saturday and state["turnip_sell_price"] > agent_turnip_buy_price):
                profit = (state["turnip_sell_price"] - agent_turnip_buy_price) * state["turnips_owned"]
                score = self.weights["bells"] * profit * bells_urgency * 1.5 # High incentive
                possible_actions_with_scores.append({
                    "action": {"type": "SELL_TURNIPS", "quantity": state["turnips_owned"], "villager_name": agent_name},
                    "score": score
                })

        # BUY_TURNIPS
        if state.get("turnip_buy_price", 0) > 0: # It's Sunday
            if state["turnip_buy_price"] <= 105:
                max_turnips_can_buy = current_bells // state["turnip_buy_price"]
                # Buy a significant portion, e.g., up to 200 or 1/4th of bells
                quantity_to_buy = min(max_turnips_can_buy, 200, current_bells // (4 * state["turnip_buy_price"])) 
                if quantity_to_buy >= 10: # Minimum sensible purchase
                    # Heuristic score: potential gain, inversely related to buy price
                    buy_score = (150 - state["turnip_buy_price"]) * quantity_to_buy 
                    possible_actions_with_scores.append({
                        "action": {"type": "BUY_TURNIPS", "quantity": quantity_to_buy, "villager_name": agent_name},
                        "score": self.weights["bells"] * buy_score * bells_urgency * 0.8
                    })
        
        # WORK_FOR_BELLS_ISLAND
        work_bells_score = 150 # Base estimated earning, less than specific activities usually
        possible_actions_with_scores.append({
            "action": {"type": "WORK_FOR_BELLS_ISLAND", "villager_name": agent_name},
            "score": self.weights["bells"] * work_bells_score * bells_urgency
        })

        # GO_FISHING - only if fishing spots limit not reached
        if go_fishing_actions_count < fishing_spots_limit_today:
            estimated_fish_value = self.dataset.get_estimated_fish_value() # Get this from dataset
            probability_of_catch = state.get("fishing_probability", 0.5) # Assume a default catch probability
            fishing_score = self.weights["bells"] * estimated_fish_value * bells_urgency * 0.7 # Slightly less than direct work
            possible_actions_with_scores.append({
                "action": {"type": "GO_FISHING", "villager_name": agent_name},
                "score": fishing_score
            })

        # SELL_ITEMS
        items_to_propose_selling_list = []
        potential_sell_value = 0
        # Prudent selling: sell common items, or items if bells are very low
        # Keep some items for gifts or if they are rare/valuable for other reasons
        # For simplicity, let's assume items in player_inventory are just {name: str, quantity: int, sell_price: int}
        # and we sell a portion of high-quantity common items or if bells are low.
        
        # Create a temporary dict for easy quantity management during selection
        inventory_map = {item['name']: item.copy() for item in player_inventory}
        
        items_considered_for_sale = []
        for item_name, item_data in inventory_map.items():
            sell_price = item_data.get("sell_price", 0)
            quantity = item_data.get("quantity", 0)
            # Simple heuristic: sell if not a tool/gift and if valuable or have many
            # A more complex agent would know which items are tools, quest items, or good gifts
            is_critical = item_data.get("is_tool", False) or item_data.get("is_gift_candidate", False)

            if quantity > 0 and sell_price > 20 and not is_critical: # Don't sell very cheap items unless many
                qty_to_sell = 0
                if bells_urgency > 1.5 and quantity > 0 : # If desperate for bells, sell more
                    qty_to_sell = quantity 
                elif quantity >= 5 and sell_price > 50: # Sell bulk common items
                    qty_to_sell = quantity // 2 
                elif quantity >=1 and sell_price > 500: # Sell valuable items
                    qty_to_sell = quantity

                if qty_to_sell > 0:
                    items_considered_for_sale.append({"name": item_name, "quantity": qty_to_sell, "value": qty_to_sell * sell_price})
        
        if items_considered_for_sale:
            # Sort by value and pick a few to sell to avoid selling everything
            items_considered_for_sale.sort(key=lambda x: x['value'], reverse=True)
            final_items_to_sell_list = []
            current_batch_value = 0
            for item_to_sell_proposal in items_considered_for_sale[:3]: # Sell up to 3 types of items
                final_items_to_sell_list.append({"name": item_to_sell_proposal["name"], "quantity": item_to_sell_proposal["quantity"]})
                current_batch_value += item_to_sell_proposal["value"]
            
            if final_items_to_sell_list:
                possible_actions_with_scores.append({
                    "action": {"type": "SELL_ITEMS", "villager_name": agent_name, "items_to_sell_list": final_items_to_sell_list},
                    "score": self.weights["bells"] * current_batch_value * bells_urgency
                })


        # --- 2. Evaluate Friendship Actions (Iterate through ALL villagers) ---
        for villager in villagers_details_list:
            if villager.name == agent_name: continue # Agent doesn't interact with itself

            # GIVE_GIFT to this villager
            # if villager.last_gifted_day != current_day:
            gift_name, gift_details = self.dataset.get_random_gift_option() # Agent has "infinite" access to random gifts for now
            if gift_details["friendship_points"] > 0:
                cost = gift_details.get("cost", 0)
                if current_bells >= cost:
                    friendship_gain_potential = gift_details["friendship_points"]
                    urgency_for_this_villager = get_urgency_multiplier(villager.friendship_level, self.friendship_target_min)
                    score = (friendship_gain_potential / (cost + 1.0)) * self.weights["friendship"] * friendship_urgency * urgency_for_this_villager
                    
                    # Apply bonus if no gifts have been given today
                    if give_gift_actions_count == 0:
                        score *= self.FORCE_GIFT_SCORE_BONUS_FACTOR
                    possible_actions_with_scores.append({
                        "action": {
                            "type": "GIVE_GIFT",
                            "villager_name": agent_name, # The agent performing the action
                            "target_villager_name": villager.name,
                            "gift_name": gift_name,
                        },
                        "score": score
                    })
            
            # TALK_TO_VILLAGER (New action type, environment must support it)
            # Assume talking gives a small, fixed friendship boost.
            # Agent might have a daily talk limit per villager (not modeled here, env might handle)
            base_talk_friendship_gain = 5 
            talk_score_raw = base_talk_friendship_gain 
            urgency_for_this_villager_talk = get_urgency_multiplier(villager.friendship_level, self.friendship_target_min, low_multiplier=1.2, very_low_multiplier=1.5)
            
            # Reduce score if talked recently (requires agent to remember talk history, simplified)
            # For now, just consider it as an option
            score = talk_score_raw * self.weights["friendship"] * friendship_urgency * urgency_for_this_villager_talk
            possible_actions_with_scores.append({
                "action": {"type": "TALK_TO_VILLAGER", "villager_name": agent_name, "target_villager_name": villager.name},
                "score": score
            })

        # --- 3. Evaluate Nook Miles Actions ---
        available_tasks_dict = state.get("active_nook_tasks", {}) # Should be {task_name: details_dict}
        if available_tasks_dict:
            for task_name, task_details in available_tasks_dict.items():
                miles_reward = task_details.get("miles", 0)
                if miles_reward > 0:
                    # Simplistic: Agent assumes it can attempt. A real agent would check criteria.
                    # The environment's _check_task_criteria will gate this.
                    score = miles_reward * self.weights["nook_miles"] * nook_miles_urgency
                    possible_actions_with_scores.append({
                        "action": {"type": "DO_NOOK_MILES_TASK", "task_name": task_name, "villager_name": agent_name},
                        "score": score
                    })
        
        # --- 4. Evaluate Farming Actions ---
        farm_plots_status = state.get("farm_plots", {}) 
        empty_plots = [pid for pid, status in farm_plots_status.items() if status.get("crop_name") is None]
        
        # PLANT_CROP
        if empty_plots:
            # Consider planting each type of known profitable crop if affordable
            # For simplicity, just consider one predefined crop like "Tomato"
            crop_to_plant = "Tomato" 
            crop_def = self.dataset.get_crop_definition(crop_to_plant)
            if crop_def and current_bells >= crop_def["SeedCost"]:
                potential_profit = (crop_def.get("SellPrice", 20) * crop_def.get("Yield", 1)) - crop_def["SeedCost"]
                if potential_profit > 0 :
                    score = self.weights["bells"] * potential_profit * bells_urgency * 0.7 # Farming is longer term
                    
                    # Apply planting bonus for designated planters
                    if is_designated_planter_for_bonus:
                        score *= self.PLANTER_SCORE_BONUS_FACTOR
                        
                    possible_actions_with_scores.append({
                        "action": {"type": "PLANT_CROP", "crop_name": crop_to_plant, "plot_id": empty_plots[0], "villager_name": agent_name},
                        "score": score
                    })

        # HARVEST_CROP
        if farm_plots_status:
            for plot_id, status in farm_plots_status.items():
                # Agent should only harvest crops it owns (or if it's communal and it's its turn/job)
                if status.get("crop_name") and \
                   status.get("ready_day", float('inf')) <= current_day and \
                   status.get("owner_villager") == agent_name: # Check ownership
                    crop_def = self.dataset.get_crop_definition(status["crop_name"])
                    if crop_def:
                        harvest_value = crop_def.get("SellPrice", 20) * crop_def.get("Yield", 1)
                        score = self.weights["bells"] * harvest_value * bells_urgency # Direct gain
                        possible_actions_with_scores.append({
                            "action": {"type": "HARVEST_CROP", "plot_id": plot_id, "villager_name": agent_name},
                            "score": score
                        })
                        # Consider harvesting multiple plots if available, but for now, one per decision cycle if good.

        # --- Apply Diversity Penalty ---
        # Penalize actions that have been taken frequently by other villagers today
        if actions_taken_today_by_others and possible_actions_with_scores:
            action_type_counts = {}
            for act_info in actions_taken_today_by_others:
                act_type = act_info.get('type')
                if act_type:
                    action_type_counts[act_type] = action_type_counts.get(act_type, 0) + 1
            
            for scored_action in possible_actions_with_scores:
                action_type = scored_action['action']['type']
                num_times_taken = action_type_counts.get(action_type, 0)
                if num_times_taken > 0:
                    # Apply a penalty factor, e.g., 0.85 for 1st repeat, 0.85^2 for 2nd, etc.
                    # Exception: Gift giving might be okay if multiple villagers want to give gifts
                    if action_type != "GIVE_GIFT" or num_times_taken > 1: # Allow at least one gift without penalty
                        # Max penalty factor to avoid scores becoming too small
                        penalty_multiplier = max(0.1, 0.85 ** num_times_taken) 
                        scored_action['score'] *= penalty_multiplier

        # --- Action Selection ---
        if not possible_actions_with_scores:
            chosen_action_details = {"type": "IDLE"}
        else:
            # Sort by score to pick the best
            possible_actions_with_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Anti-repetition logic: if top action is repetitive, try next best non-repetitive one
            current_agent_repetition_counter = self.villager_action_repetition_counter.get(agent_name, 0)
            best_action_info = possible_actions_with_scores[0]
            if current_agent_repetition_counter >= 2 and self._is_action_repetitive(best_action_info["action"], agent_name):
                found_alternative = False
                for alt_action_info in possible_actions_with_scores[1:]:
                    if not self._is_action_repetitive(alt_action_info["action"], agent_name):
                        best_action_info = alt_action_info
                        found_alternative = True
                        break
                if not found_alternative: # All high-scoring options are repetitive, pick the best of them
                    pass # best_action_info is already set to the top one
            
            chosen_action_details = best_action_info["action"]

        # Update repetition counter and last action details for this specific agent
        if chosen_action_details["type"] != "IDLE" and self._is_action_repetitive(chosen_action_details, agent_name):
            self.villager_action_repetition_counter[agent_name] = self.villager_action_repetition_counter.get(agent_name, 0) + 1
        else:
            self.villager_action_repetition_counter[agent_name] = 0
        
        self.villager_last_action_details[agent_name] = chosen_action_details.copy() # Store a copy
        
        # Ensure agent_name is in the action for the environment
        if "villager_name" not in chosen_action_details and chosen_action_details["type"] != "IDLE":
             chosen_action_details["villager_name"] = agent_name
        
        # Debug prints (optional)
        # print(f"Agent Choosing: Day {current_day}, Bells {current_bells}, AvgFriend {state.get('avg_friendship',0):.1f}")
        # print(f"Top 3 considered actions:")
        # for i, pa in enumerate(possible_actions_with_scores[:3]):
        # print(f"  {i+1}. {pa['action']['type']} (Target: {pa['action'].get('target_villager_name', 'N/A')}, Item: {pa['action'].get('gift_name', pa['action'].get('task_name','N/A'))}) - Score: {pa['score']:.2f}")
        # print(f"Chosen action: {chosen_action_details}")

        return chosen_action_details
