#!/usr/bin/env python3

import os
import sys

# Imports
import discord
from discord.ext import commands
from dotenv import load_dotenv

# SF Imports
from pyfactorybridge import API

# Load Variables from env file
load_dotenv()
DC_TOKEN = os.getenv("DISCORD_TOKEN")
SF_IP = os.getenv("SF_IP")
SF_PORT = os.getenv("SF_PORT")
SF_TOKEN = os.getenv("SF_TOKEN")
SF_SERVER_NAME = os.getenv("SF_SERVER_NAME")

# Define global variables
api = ""
initial_extensions = ["cogs.satisfactory"]

intents = discord.Intents.default()
# intents.members = True
# intents.guilds = True
# intents.messages = True


# Define all prefixes here
async def get_prefix(bot, message):
    prefixes = ["!"]
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Define bot
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents.all(),
    description="Ficit2Discord - your personal Assistant",
)


# Event wehn the bot ist started
@bot.event
async def on_ready():
    await load_cogs()
    print(
        f"Logged in as: {bot.user.name} - {bot.user.id}\nVersion; {discord.__version__}\n"
    )


# When something goes wrong
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(
            "You do not have the correct role for this command or it does not exist!"
        )


# Loading cogs into the bot
# see initial_extensions variable
async def load_cogs():
    for extension in initial_extensions:
        try:
            print(f"Loading extension: {extension}")
            await bot.load_extension(extension)
            print(f"Successfully loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}", file=sys.stderr)


# Main function
def main():
    # Connect to the Satisfactory server
    bot.api = API(address=f"{SF_IP}:{SF_PORT}", token=SF_TOKEN)
    bot.server = SF_SERVER_NAME
    # Login into Discord
    bot.run(DC_TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
