# Ficit2Discord Bot

<p align="center">
<img src="https://raw.githubusercontent.com/Brazier85/Ficsit2Discord/refs/heads/main/files/s2d_logo.webp" width="300" height="300">
</p>

## Overview
Ficit2Discord is a custom Discord bot that interacts with a dedicated Satisfactory game server. The bot allows server administrators to manage the server directly from Discord, including saving the game, restarting the server, and viewing server stats.

## Features
- **Save Game**: Saves the game and sends the save file to Discord.
- **Restart Server**: Safely restarts the Satisfactory server.
- **Server State**: Displays the current state of the server, including player count, average tick rate, and server health.
- **Settings**: Shows the current server settings.

## Prerequisites
- Python 3.8+
- A running Satisfactory game server
- Discord API credentials (Bot Token)
- `satisfactory_api_client` package to interact with the Satisfactory server
- Required Python libraries:
  - `discord.py`
  - `python-dotenv`
  - `satisfactory_api_client`

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/ficit2discord.git
   cd ficit2discord
   ```

2. **Create a virtual environment** (highly recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and define the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   SF_IP=your_satisfactory_server_ip
   SF_PORT=your_satisfactory_server_port
   SF_PASSWD=your_satisfactory_server_password
   SF_SERVER_NAME=your_server_name
   ```

## Configuration

- **Bot Prefix**: The bot responds to commands starting with `!sf`. You can modify the prefix by adjusting the `prefix` in the `Satisfactory` cog.
  
- **Environment Variables**: Ensure the `.env` file contains the correct details for your Discord bot and Satisfactory server.

## Commands

| Command         | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `!sf save`      | Saves the game and sends the save file to Discord.                          |
| `!sf restart`   | Saves the game and restarts the server.                                     |
| `!sf state`     | Displays the current server status, including players, ticks, and health.   |
| `!sf settings`  | Shows the current settings of the Satisfactory server.                      |

### Example Command Usage

- To save the game and get the save file in Discord:
  ```
  !sf save
  ```

- To restart the server:
  ```
  !sf restart
  ```

## Code Structure

- **bot.py**: The main entry point for the bot. It initializes the bot, loads environment variables, and handles cog loading.
- **cogs/satisfactory.py**: Contains all the Satisfactory-related commands and functions, such as saving the game, restarting, and checking server status.
- **files/savegames/**: Directory where game save files are stored after download from the server.

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

## Acknowledgements

A special thanks to the maintainers of the libraries used in this project:
- **[`discord.py`](https://github.com/Rapptz/discord.py)**: For enabling Discord bot functionality. Maintained by [Rapptz](https://github.com/Rapptz).
- **[`satisfactory_api_client`](https://github.com/Programmer-Timmy/satisfactory-dedicated-server-api-SDK)**: For enabling smooth communication with the Satisfactory server. Maintained by [Programmer-Timmy](https://github.com/Programmer-Timmy).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

