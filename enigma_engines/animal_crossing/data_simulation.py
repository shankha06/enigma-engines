import csv
import os
import random

def generate_crops_dataset(file_path="data/crops.csv", num_crops=15):
    """
    Generates a sample crops dataset and saves it to a CSV file.

    Args:
        file_path (str): The path (including filename) to save the CSV.
        num_crops (int): The number of sample crop types to generate.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    headers = ["Name", "GrowthTimeDays", "SellPrice", "SeedCost", "Yield"]
    
    sample_crop_bases = [
        {"name": "Tomato", "growth_base": 5, "sell_base": 30, "seed_base": 10, "yield_base": 3},
        {"name": "Carrot", "growth_base": 4, "sell_base": 25, "seed_base": 8, "yield_base": 1},
        {"name": "Potato", "growth_base": 6, "sell_base": 40, "seed_base": 12, "yield_base": 2},
        {"name": "Wheat", "growth_base": 7, "sell_base": 20, "seed_base": 5, "yield_base": 4},
        {"name": "Strawberry", "growth_base": 8, "sell_base": 120, "seed_base": 40, "yield_base": 2},
        {"name": "Pumpkin", "growth_base": 10, "sell_base": 350, "seed_base": 100, "yield_base": 1},
        {"name": "Corn", "growth_base": 9, "sell_base": 80, "seed_base": 30, "yield_base": 3},
        {"name": "Lettuce", "growth_base": 3, "sell_base": 15, "seed_base": 5, "yield_base": 1},
        {"name": "Bell Pepper", "growth_base": 8, "sell_base": 90, "seed_base": 35, "yield_base": 2},
        {"name": "Sugarcane", "growth_base": 5, "sell_base": 50, "seed_base": 20, "yield_base": 3},
        {"name": "Watermelon", "growth_base": 12, "sell_base": 250, "seed_base": 80, "yield_base": 1},
        {"name": "Blueberry", "growth_base": 10, "sell_base": 150, "seed_base": 50, "yield_base": 4},
        {"name": "Grape", "growth_base": 9, "sell_base": 100, "seed_base": 30, "yield_base": 3},
        {"name": "Onion", "growth_base": 4, "sell_base": 30, "seed_base": 10, "yield_base": 1},
        {"name": "Cauliflower", "growth_base": 8, "sell_base": 175, "seed_base": 70, "yield_base": 1},
    ]

    crops_data = []
    if num_crops > len(sample_crop_bases):
        print(f"Warning: Requested {num_crops} crops, but only {len(sample_crop_bases)} unique base types available. Using all available.")
        num_crops = len(sample_crop_bases)

    selected_bases = random.sample(sample_crop_bases, num_crops)

    for i, base in enumerate(selected_bases):
        # Add slight variations for more "generated" feel if desired, or use directly
        name = f"{base['name']}" # Could add suffixes like "Variety {i+1}" if generating many more than bases
        growth_time = base['growth_base'] + random.randint(-1, 1)
        sell_price = base['sell_base'] + random.randint(-base['sell_base']//10, base['sell_base']//10)
        seed_cost = base['seed_base'] + random.randint(-base['seed_base']//10, base['seed_base']//10)
        crop_yield = base['yield_base'] + random.randint(0,1) if base['yield_base'] > 1 else base['yield_base']
        
        crops_data.append([
            name,
            max(1, growth_time), # Ensure positive time
            max(1, sell_price),  # Ensure positive price
            max(1, seed_cost),   # Ensure positive cost
            max(1, crop_yield)   # Ensure positive yield
        ])

    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(crops_data)
        print(f"Successfully generated and saved crops dataset to {file_path}")
    except IOError:
        print(f"Error: Could not write to {file_path}")