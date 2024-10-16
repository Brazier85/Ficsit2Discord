#!/usr/bin/env python3

import os
import sys
import traceback

# Imports
import discord
from discord.ext import commands
from dotenv import load_dotenv

# SF Imports
from pyfactorybridge import API

# Load Variables from env file
load_dotenv()
DC_TOKEN = os.getenv("DISCORD_TOKEN", "")
DC_GUILD = os.getenv("DISCORD_GUILD")
DC_OWNER = os.getenv("DISCORD_BOT_OWNER", "")
DC_SF_ADMIN_ROLE = os.getenv("DISCORD_SF_ADMIN_ROLE", "Ficsit2Discord")
SF_IP = os.getenv("SF_IP", "127.0.0.1")
SF_PORT = os.getenv("SF_PORT", "7777")
SF_TOKEN = os.getenv("SF_TOKEN", "")
SF_SERVER_NAME = os.getenv("SF_SERVER_NAME", "My awsome server!")

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


# Event when the bot ist started
@bot.event
async def on_ready():
    await load_cogs()
    print(
        f"Logged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n"
    )


# When something goes wrong
@bot.event
async def on_command_error(ctx, error):
    # This prevents any commands with local handlers being handled here in on_command_error.
    if hasattr(ctx.command, "on_error"):
        return

    # This prevents any cogs with an overwritten cog_command_error being handled here.
    cog = ctx.cog
    if cog:
        if cog._get_overridden_method(cog.cog_command_error) is not None:
            return

    # Msg to unknown menber
    if isinstance(error, commands.MemberNotFound):
        await ctx.send(f"I could not find member: {error.argument}. Pls try again.")
    # Missing argument
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{error.param.name} is a required argument.")
    # Missing permissions
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the correct role for this command!")
    # Disabled command
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send(f"{ctx.command} has been disabled.")
    # Private message error
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send(f"{ctx.command} can not be used in Private Messages.")
        except discord.HTTPException:
            pass
    # All other Errors not returned come here. And we can just print the default TraceBack.
    else:
        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )
        print(f"Ignoring exception in command {ctx} | !")

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
    bot.dc_sf_admin_role = DC_SF_ADMIN_ROLE
    # Login into Discord
    bot.run(DC_TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
