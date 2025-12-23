# KomaruCards telegram user-bot

This project is a Telegram user-bot designed to automate interactions with the KomaruCardsBot game in Telegram. It helps collect cards, manage cooldowns, and use boosters.

## Features

*   **Automatic Card Collection**: The bot sends commands to receive cards.
*   **Cooldown Management**: Automatically detects cooldowns and can use time boosters or wait for them to expire.
*   **Luck Booster Usage**: Can use luck boosters when a certain coin threshold is reached.
*   **Two Operating Modes**:
    *   **WIP: Automatic**: Fully automates the process, including booster usage and cooldown waiting.
    *   **Semi-automatic**: Sends the `/komaru` command and waits for manual initiation, but then continues to automate actions.
*   **Customizable Behavior**: You can configure profile check frequency, number of actions before rest, and rest duration.

*WIP - means: Work In Progress, may be unstable or not working. use `semi-automatic` mode.*
## Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/itskekoff/KomaruCardsBot.git
    cd KomaruCardsBot
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate # For Linux/macOS
    # .venv\Scripts\activate # For Windows
    ```

3.  **Install dependencies**:

    ```bash
    pip install .
    # Or, if you have 'uv' installed:
    # uv pip install .
    ```

4.  **Configure `config.toml`**:
    On first run or if the file is missing, `config.toml` will be created in the project's root directory. You will need to fill it with your data:

    ```toml
    # config.toml
    api_id = 1234567 # Your Telegram API ID
    api_hash = "YOUR_API_HASH_HERE" # Your Telegram API Hash
    target_bot_id = "KomaruCardsBot" # The username of the bot your bot will interact with
    mode = "automatic" # "automatic" or "semi-automatic"
    debug_logging = true

    [game_settings]
    time_booster_cost = 15
    luck_booster_cost = 20
    luck_booster_min_coins_threshold = 45

    [behavior]
    use_time_booster_chance = 0.8
    spontaneous_profile_check_chance = 0.05
    max_actions_before_rest = 25
    rest_chance = 0.5
    rest_duration_min_minutes = 45
    rest_duration_max_minutes = 75
    ```
    *   **`api_id` and `api_hash`**: Get them from my.telegram.org.
    *   **`target_bot_id`**: The username of the bot you want to interact with (default `KomaruCardsBot`).
    *   **`mode`**: Set to `"automatic"` for full automation or `"semi-automatic"` for manual initiation of the first `/komaru` command.
    *   Other settings allow fine-tuning of the bot's behavior.

## Running the Bot

After configuring `config.toml`, you can run the bot:

```bash
python main.py
```

The bot will start interacting with KomaruCardsBot according to your settings.

## Important Note
This bot interacts with a third-party service. Use it at your own risk and ensure you comply with the ToS of Telegram. The author is not responsible for any consequences caused by the use of this bot.
