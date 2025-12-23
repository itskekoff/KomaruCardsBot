import toml
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
CONFIG_FILE_PATH = os.path.join(project_root, "config.toml")

def create_default_config(config_path=CONFIG_FILE_PATH):
    if not os.path.exists(config_path):
        default_config = {
            "api_id": 0,
            "api_hash": "YOUR_API_HASH_HERE",
            "target_bot_id": "KomaruCardsBot",
            "mode": "semi-automatic",
            "debug_logging": True,
            "game_settings": {
                "time_booster_cost": 15,
                "luck_booster_cost": 20,
                "luck_booster_min_coins_threshold": 45
            },
            "behavior": {
                "use_time_booster_chance": 0.8,
                "spontaneous_profile_check_chance": 0.05,
                "max_actions_before_rest": 25,
                "rest_chance": 0.5,
                "rest_duration_min_minutes": 45,
                "rest_duration_max_minutes": 75
            }
        }
        with open(config_path, "w") as f:
            toml.dump(default_config, f)
        print(f"created default {config_path}. please fill in api_id and api_hash.")
    return toml.load(config_path)

def get_config(config_path=CONFIG_FILE_PATH):
    return create_default_config(config_path)
