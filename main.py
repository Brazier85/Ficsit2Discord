#!/usr/bin/env python3

import sys
import traceback

# Imports
import discord
from discord.ext import commands

# SF Imports
from pyfactorybridge import API

from data.config import ConfigManager

# Define global variables
api = ""
conf = ConfigManager()
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
    await bot.tree.sync()
    print(f"Logged in as: {bot.user.name} - {bot.user.id}")
    chan_id = conf.get("DC_STATE_CHANNEL")
    channel = await bot.fetch_channel(chan_id)
    print(f"Special channel info: {channel=}")
    print(f"Version: {discord.__version__}")
    repr(bot)


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
    bot.api = API(
        address=f"{conf.get('SF_IP')}:{conf.get('SF_PORT')}", token=conf.get("SF_TOKEN")
    )
    # Login into Discord
    bot.run(conf.get("DC_TOKEN"), reconnect=True)


if __name__ == "__main__":
    main()
