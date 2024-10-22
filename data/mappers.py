# Dictionary mapping technical parameters to human-friendly names
settings_mapper = {
    "FG.DSAutoPause": "Auto Pause",
    "FG.DSAutoSaveOnDisconnect": "Save on DC",
    "FG.AutosaveInterval": "Autosave Interval",
    "FG.ServerRestartTimeSlot": "Server Restart Time",
    "FG.SendGameplayData": "Send Gameplay Data",
    "FG.NetworkQuality": "Network Quality",
}

state_mapper = {
    "totalGameDuration": "Total Playtime",
    "playerLimit": "Max Players",
    "numConnectedPlayers": "Currently online",
    "averageTickRate": "Avg. Tick Rate",
    "techTier": "Technologie Tier",
    "activeSessionName": "Session Name",
    "isGamePaused": "Game paused",
}

icon_mapper = {
    "True": ":white_check_mark:",
    "False": ":x:",
    "healthy": ":green_circle:",
    "slow": ":yellow_circle:",
}

messageTypes = {"PollServerState": 0, "ServerStateResponse": 1}

serverStates = {
    0: "Offline",  # This should never actually be sent as a running server will not send this state, but it is defined.
    1: "Idle",  # The server is running, but no save is currently loaded.
    2: "Preparing world",  # The server is running, and currently loading a map.  The HTTPS API will not respond in this state.
    3: "Live",  # The server is running, and a save is loaded.  The server is joinable by players.
}

serverSubStates = {
    0: "ServerGameState",  # Game state.  Maps to REST API QueryServerState function.
    1: "ServerOptions",  # Global options set on the server.  Maps to REST API GetServerOptions function.
    2: "AdvancedGameSettings",  # AGS is currently enabled in the loaded session.  Maps to REST API GetAdvancedGameSettings function.
    3: "SaveCollection",  # List of saves available on the server for loading/downloading.  Maps to REST API EnimarateSessions.
    4: "Custom1",  # A value that can be used by mods or custom servers.  Not used on Vanilla servers.
    5: "Custom2",  # A value that can be used by mods or custom servers.  Not used on Vanilla servers.
    6: "Custom3",  # A value that can be used by mods or custom servers.  Not used on Vanilla servers.
    7: "Custom4",  # A value that can be used by mods or custom servers.  Not used on Vanilla servers.
}

serverFlags = {
    0: "Modded",  # The server self-identifies as being Modded.  Vanilla (i. e. un-modded) clients will not attempt to connect.
    1: "Custom1",  # A flag with server-specific or context-specific meaning, currently undefined.
    2: "Custom2",  # A flag with server-specific or context-specific meaning, currently undefined.
    3: "Custom3",  # A flag with server-specific or context-specific meaning, currently undefined.
    4: "Custom4",  # A flag with server-specific or context-specific meaning, currently undefined.
}
