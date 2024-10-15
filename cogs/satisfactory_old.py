import datetime
import json

import discord
from discord.ext import commands
from satisfactory_api_client import APIError

bot_logo = "https://raw.githubusercontent.com/Brazier85/Ficsit2Discord/refs/heads/main/files/f2d_logo.webp"


class Satisfactory(commands.Cog, name="Satisfactory Commands"):
    """**!sf <command>**\nEverything Satisfactory related."""

    def __init__(self, bot):
        self.bot = bot
        self.api = self.bot.api
        self.servername = self.bot.server

    @commands.group()
    async def sf(self, ctx):
        """Everything related to Satisfactory Servers"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf`")

    @sf.command(name="restart")
    async def restart(self, ctx):
        """This command will save the game an then restart the server."""
        api = self.api
        if await self.save(api).success:
            if api.self.shutdown().success:
                embed = await self.create_embed(title="Server Successfully stopped!")
                embed.add_field(
                    name="Server is restarting...",
                    value="The restart can take up to 5 minutes.",
                    inline=False,
                )
                ctx.send(embed=embed)
            else:
                ctx.send("Could not restart the server!")
        else:
            ctx.send("I could not save the game! No restart possible!")

    @sf.command(name="save")
    async def save(self, ctx, save_name="Ficit2Discord"):
        """This command will save the game"""
        api = self.api
        msg = await ctx.send("Saving game...")
        response = api.save_game(save_name)
        if response.success:
            print("Game saved!")
            await msg.edit(content=":white_check_mark: Game saved Successfully!")
            await self.download_save(ctx, msg, save_name)
            return True
        else:
            await msg.edit(content=":x: Could not save game!")

    async def download_save(self, ctx, msg, save_name):
        api = self.api
        save_filename = f"{save_name}.sav"
        with open(f"./files/savegames/{save_filename}", "wb") as file:
            file.write(api.download_save_game(save_name).data)
            print("File saved")

        file = discord.File(f"./files/savegames/{save_filename}")

        # Define embed
        embed = await self.create_embed(title=f"{self.server} Savegame", color=0x00F51D)
        embed.add_field(
            name="",
            value=":white_check_mark: Successfully saved game!",
            inline=False,
        )
        embed.add_field(name="Save File", value=f"`{save_filename}`")
        try:
            await ctx.send(file=file, embed=embed)
            await msg.delete()
        except APIError as e:
            print(f"Error: {e}")

    @sf.command(name="state")
    async def state(self, ctx):
        """Will post the current server state"""
        api = self.api
        res_state = api.query_server_state()
        res_health = api.health_check()
        current_state = res_state.data["serverGameState"]
        playtime = str(datetime.timedelta(seconds=current_state["totalGameDuration"]))
        p_max = str(current_state["playerLimit"])
        p_online = current_state["numConnectedPlayers"]
        ticks = current_state["averageTickRate"]
        health = res_health.data["health"]
        if health == "healthy":
            icon = ":green_circle:"
            color = 0x00F51D
        else:
            icon = ":yellow_circle"
            color = 0xFFF700

        # Define Embed
        embed = await self.create_embed(color=color, title=f"{self.servername} Status")

        embed.add_field(name="", value=f"{icon} Server is **{health}**", inline=False)
        embed.add_field(name="Players", value=f"{p_online}/{p_max}", inline=True)
        embed.add_field(name="Avg Ticks", value=f"{ticks:.2f}", inline=True)
        embed.add_field(name="Playtime", value=f"{playtime}", inline=True)

        await ctx.send(embed=embed)

    @sf.command(name="settings")
    async def options(self, ctx):
        """Show the current server settings"""
        api = self.api
        settings = api.get_server_options()
        current_settings = settings.data["serverOptions"]
        auto_pause = current_settings["FG.DSAutoPause"]
        auto_save = current_settings["FG.DSAutoSaveOnDisconnect"]
        save_interval = current_settings["FG.AutosaveInterval"]
        restart_time = current_settings["FG.ServerRestartTimeSlot"]
        gameplay_data = current_settings["FG.SendGameplayData"]
        network_quality = current_settings["FG.NetworkQuality"]

        # Define Embed
        embed = await self.create_embed(title=f"{self.servername} Settings")
        embed.add_field(name="Auto Pause", value=f"{auto_pause}", inline=True)
        embed.add_field(name="Auto Save", value=f"{auto_save}", inline=True)
        embed.add_field(name="Save Interval", value=f"{save_interval}", inline=True)
        embed.add_field(name="Restart Time", value=f"{restart_time}", inline=True)
        embed.add_field(name="Send Gameplay Data", value=f"{gameplay_data}")
        embed.add_field(name="Network Quality", value=f"{network_quality}", inline=True)

        await ctx.send(embed=embed)

    @sf.group()
    async def set(self, ctx):
        """Change server settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf`")

    @set.command(name="autosave")
    async def autosave(self, ctx, value):
        """Auto save game on player disconnect"""
        api = self.api
        print(f"change autosave requested {value}")
        new_settings = json.dumps({"FG.DSAutoSaveOnDisconnect": value})
        print(f"New settings: {new_settings}")
        if api.apply_server_options(new_settings).success:
            await ctx.send(f"I changed the value of **Auto Save** to **{value}**")
        else:
            await ctx.send("Could not change setting")

    async def change_setting(self, ctx, setting, value):
        api = self.api
        payload = {setting: value}
        print(f"Payload: {payload}")
        if api.apply_server_options(payload).success:
            await ctx.send(f"I changed the value of **{setting}** to **{value}**")
        else:
            await ctx.send("Could not change setting")

    async def create_embed(self, title="Ficsit2Discord Bot", color=0x00B0F4):
        # Define Embed
        embed = discord.Embed(
            title=title,
            colour=color,
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name="Ficsit2Discord Bot", icon_url=bot_logo)
        embed.set_thumbnail(url=bot_logo)
        embed.set_footer(text="Ficsit2Discord Bot")
        return embed


async def setup(bot):
    await bot.add_cog(Satisfactory(bot))