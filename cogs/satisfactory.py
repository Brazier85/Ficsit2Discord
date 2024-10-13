import datetime

import discord
from discord.ext import commands
from satisfactory_api_client import APIError


class Satisfactory(commands.Cog, name="Satisfactory Commands"):
    """**!sf <command>**\nEverything Satisfactory related."""

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.prefix = "!sf "
        self.api = self.bot.api
        self.servername = self.bot.server

    # Custom check for prefix enforcement
    async def cog_check(self, ctx):
        return ctx.prefix == self.prefix

    @commands.command(name="restart")
    async def restart(self, ctx):
        """This command will save the game an then restart the server."""
        api = self.api
        if await self.save(api).success:
            return api.self.shutdown()
        else:
            return "I could not save the game! No restart possible!"

    @commands.command(name="save")
    async def save(self, ctx, save_name="Ficit2Discord"):
        """this command will save the game"""
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
        embed = discord.Embed(
            title=f"{self.server} Savegame",
            # url=link,
            colour=0x00F51D,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(
            name="",
            value=":white_check_mark: Successfully saved game!",
            inline=False,
        )
        embed.add_field(name="Save File", value=f"`{save_filename}`")
        embed.set_footer(text="Harald")
        try:
            await ctx.send(file=file, embed=embed)
            await msg.delete()
        except APIError as e:
            print(f"Error: {e}")

    @commands.command(name="state")
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
        embed = discord.Embed(
            title=f"{self.servername} Status",
            colour=color,
            timestamp=datetime.datetime.now(),
        )

        embed.add_field(name="", value=f"{icon} Server is **{health}**", inline=False)
        embed.add_field(name="Players", value=f"{p_online}/{p_max}", inline=True)
        embed.add_field(name="Avg Ticks", value=f"{ticks:.2f}", inline=True)
        embed.add_field(name="Playtime", value=f"{playtime}", inline=True)

        embed.set_footer(text="Server Status Updated")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Satisfactory(bot))
