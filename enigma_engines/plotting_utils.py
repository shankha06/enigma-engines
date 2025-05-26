import seaborn as sns
import matplotlib.pyplot as plt

def plot_simulation_results(rewards_log):
    """
    Plots the simulation results (bells, nook_miles, friendship) using Seaborn.

    Args:
        rewards_log (dict): A dictionary containing lists of rewards over time.
                            Expected keys: "bells", "nook_miles", "friendship".
    """
    sns.set_theme(style="whitegrid")

    # Determine the number of days from the logs
    num_days = 0
    # Check a few common keys to find the length of the simulation
    for key in ["bells", "nook_miles", "friendship"]:
        if key in rewards_log and rewards_log[key]:
            num_days = len(rewards_log[key])
            break
    
    if num_days == 0:
        print("Warning: No data found in rewards_log to plot.")
        return

    days_axis = range(1, num_days + 1)  # Create an x-axis representing days

    fig, axs = plt.subplots(3, 1, sharex=True, figsize=(12, 9)) # Adjusted figsize for better layout

    plot_configurations = [
        {"key": "bells", "label": "Total Bells", "color": "skyblue"},
        {"key": "nook_miles", "label": "Total Nook Miles", "color": "lightcoral"},
        {"key": "friendship", "label": "Avg Friendship", "color": "mediumseagreen"},
    ]

    for i, config in enumerate(plot_configurations):
        ax = axs[i]
        if config["key"] in rewards_log and rewards_log[config["key"]]:
            sns.lineplot(x=days_axis, 
                         y=rewards_log[config["key"]], 
                         ax=ax, 
                         label=config["label"], 
                         color=config["color"], 
                         linewidth=2)
            ax.set_ylabel(config["label"])
            ax.legend(loc='upper left')
        else:
            ax.text(0.5, 0.5, f"No data for {config['label']}", 
                    horizontalalignment='center', 
                    verticalalignment='center', 
                    transform=ax.transAxes)
            ax.set_ylabel(config["label"])
        ax.grid(True, linestyle='--', alpha=0.7)


    axs[-1].set_xlabel("Day")
    fig.suptitle("Agent Performance Over Time", fontsize=16, y=0.99)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust rect to make space for suptitle
    plt.show()