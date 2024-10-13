#!/usr/bin/env python3

import os
import sys

# Imports
import discord
from discord.ext import commands
from dotenv import load_dotenv

# SF Imports
import sf
from custom_help import CustomHelpCommand

# Load Variables from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SF_IP = os.getenv("SF_IP")
SF_PORT = os.getenv("SF_PORT")
SF_PASSWD = os.getenv("SF_PASSWD")
SF_SERVER_NAME = os.getenv("SF_SERVER_NAME")
api = ""

initial_extensions = ["cogs.satisfactory"]

intents = discord.Intents.default()
# intents.members = True
# intents.guilds = True
# intents.messages = True


async def get_prefix(bot, message):
    prefixes = ["!sf ", "!"]
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents.all(),
    description="Harald, a litte discord bot",
)

bot.help_command = CustomHelpCommand()


@bot.event
async def on_ready():
    await load_cogs()
    print(
        f"Logged in as: {bot.user.name} - {bot.user.id}\nVersion; {discord.__version__}\n"
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(
            "You do not have the correct role for this command or it does not exist!"
        )


async def load_cogs():
    for extension in initial_extensions:
        try:
            print(f"Loading extension: {extension}")
            await bot.load_extension(extension)
            print(f"Successfully loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}", file=sys.stderr)


def main():
    # sf.test(SF_IP, SF_PORT, SF_PASSWD)
    # Connect to the sf-server
    bot.api = sf.connect(SF_IP, SF_PORT)
    bot.server = SF_SERVER_NAME
    # Login to the sf-server
    sf.login(bot.api, SF_PASSWD)
    # Login into Discord
    bot.run(TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
