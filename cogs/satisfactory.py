import datetime
import socket
import struct
import sys
import time

import discord
import numpy as np
from discord.ext import commands, tasks
from pyfactorybridge.exceptions import SaveGameFailed

from data.config import ConfigManager

# Mappers
from data.mappers import (
    icon_mapper,
    messageTypes,
    serverStates,
    serverSubStates,
    settings_mapper,
)

bot_logo = "https://raw.githubusercontent.com/Brazier85/Ficsit2Discord/refs/heads/main/files/f2d_logo.webp"
conf = ConfigManager()
heart_beats = 0
last_server_state = ""
next_save = datetime.datetime.now()

utc = datetime.timezone.utc

times = [
    datetime.time(hour=0, tzinfo=utc),
    datetime.time(hour=2, tzinfo=utc),
    datetime.time(hour=4, tzinfo=utc),
    datetime.time(hour=6, tzinfo=utc),
    datetime.time(hour=8, tzinfo=utc),
    datetime.time(hour=10, tzinfo=utc),
    datetime.time(hour=12, tzinfo=utc),
    datetime.time(hour=14, tzinfo=utc),
    datetime.time(hour=16, tzinfo=utc),
    datetime.time(hour=18, tzinfo=utc),
    datetime.time(hour=20, tzinfo=utc),
    datetime.time(hour=22, tzinfo=utc),
]


class Satisfactory(commands.Cog, name="Satisfactory Commands"):
    """**!sf <command>**\nEverything Satisfactory related."""

    def __init__(self, bot):
        self.bot = bot
        self.api = self.bot.api
        self.serverStates = serverStates
        self.messageTypes = messageTypes
        self.serverSubStates = serverSubStates
        self.protocolVersion = 1
        self.servername = conf.get("SF_SERVER_NAME")
        self.sf_server_monitor.start()

    def cog_unload(self):
        self.sf_server_monitor.cancel()

    @tasks.loop(seconds=30)
    async def sf_server_monitor(self):
        global heart_beats
        global last_server_state
        heart_beats += 1
        print(f"heartbeat: {heart_beats:4}")
        udpstatus = self.probe_udp(conf)
        server_state = self.serverStates[udpstatus["ServerState"]]
        print(f"\tUDP Probe complete.  {server_state=}")
        # server_name = udpstatus['ServerName']
        if server_state != last_server_state:
            if server_state != "Offline":
                prefix_icon = "✅"
            elif server_state != "Ready":
                prefix_icon = "⚠️"
            else:
                prefix_icon = "❌"
        else:
            print("heartbeat: State did not change!")
        chan_id = conf.get("DC_STATE_CHANNEL")
        channel = await self.bot.fetch_channel(chan_id)
        await channel.edit(name=f"satisfactory-{prefix_icon}")
        await self.sf_auto_save(channel)

    async def sf_auto_save(self, channel):
        global next_save
        if datetime.datetime.now() > next_save:
            print(f"Using {channel} for auto save posts")
            await self.save(channel, save_name="Discord_AutoSave", silent=True)
            next_save = datetime.datetime.now() + datetime.timedelta(hours=2)
            print(f"Next save: {next_save}")
        else:
            print("No autosave required")

    @commands.hybrid_group(fallback="sf")
    async def sf(self, ctx):
        """Everything related to Satisfactory Servers"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf`")

    @commands.has_role(conf.get("DC_SF_ADMIN_ROLE"))
    @sf.command(name="restart")
    async def restart(self, ctx):
        """Save the game and restart the server."""
        api = self.api
        if await self.save(ctx):
            try:
                api.shutdown()
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error on shutdown!")
                await ctx.send("Could not shutdown the server!")
            else:
                embed = await self.create_embed(title="Server Successfully stopped!")
                embed.add_field(
                    name="Server is restarting...",
                    value="The restart can take up to 5 minutes.",
                    inline=False,
                )
                await ctx.send(embed=embed)
        else:
            await ctx.send("I could not save the game! No restart possible!")

    @commands.has_role(conf.get("DC_SF_ADMIN_ROLE"))
    @sf.command(name="save")
    async def save(self, ctx, save_name="Ficit2Discord", silent=False):
        """This command will save the game"""
        api = self.api
        msg = await ctx.send("Saving game...", silent=silent)
        try:
            api.save_game(SaveName=save_name)
        except SaveGameFailed as error:
            await msg.edit(content=f":x: Could not save game: {error}")
            return False
        else:
            await msg.edit(content=":white_check_mark: Game saved Successfully!")
            await self.download_save(ctx, msg, save_name, silent=silent)
            return True

    async def download_save(self, ctx, msg, save_name, silent=False):
        api = self.api
        save_filename = f"{save_name}.sav"
        save_path = f"./files/savegames/{save_filename}"
        try:
            await msg.edit(content="Downloading save game!")
            api.download_save_game(save_name, save_path)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Could not download save game")
            await msg.edit(content="Coud not download the save game")
        else:
            file = discord.File(save_path)

            # Define embed
            embed = await self.create_embed(
                title=f"{self.servername} Savegame", color=0x00F51D
            )
            embed.add_field(
                name="",
                value=":white_check_mark: Successfully saved game!",
                inline=False,
            )
            embed.add_field(name="Save File", value=f"`{save_filename}`")
            try:
                await ctx.send(file=file, embed=embed, silent=silent)
                await msg.delete()
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error sending file")
                await msg.edit("Cloud not send save file to Discord!", silent=silent)

    @sf.command(name="connect")
    async def sf_connect(self, ctx):
        """Show server connection details"""
        embed = await self.create_embed(title=f"{self.servername} Details")

        embed.add_field(name="Address", value=conf.get("SF_PUBLIC_ADDR"), inline=False)
        embed.add_field(name="Password", value="Ask a Moderator", inline=False)
        await ctx.send(embed=embed)

    @sf.command(name="state")
    async def state(self, ctx):
        """Will post the current server state"""
        api = self.api
        current_state = api.query_server_state()["serverGameState"]
        current_health = api.get_server_health()["health"]

        # Create vars
        playtime = str(datetime.timedelta(seconds=current_state["totalGameDuration"]))
        p_max = current_state["playerLimit"]
        p_online = current_state["numConnectedPlayers"]
        ticks = current_state["averageTickRate"]
        tech_tier = current_state["techTier"]
        session_name = current_state["activeSessionName"]
        paused = current_state["isGamePaused"]
        health = current_health
        if health == "healthy":
            color = 0x00F51D
        else:
            color = 0xFFF700

        # Define Embed
        embed = await self.create_embed(color=color, title=f"{self.servername} Status")

        embed.add_field(
            name="",
            value=f"{icon_mapper.get(health, health)} Server is **{health}**",
            inline=False,
        )
        embed.add_field(name="Players", value=f"{p_online}/{p_max}", inline=True)
        embed.add_field(name="Avg Ticks", value=f"{ticks:.2f}", inline=True)
        embed.add_field(name="Playtime", value=f"{playtime}", inline=True)
        embed.add_field(
            name="Game paused",
            value=f"{icon_mapper.get(str(paused), paused)}",
            inline=True,
        )
        embed.add_field(name="Tech Tier", value=f"{tech_tier}", inline=True)
        embed.add_field(name="Session Name", value=f"{session_name}", inline=True)

        await ctx.send(embed=embed)

    @sf.command(name="settings")
    async def options(self, ctx):
        """Show the current server settings"""
        api = self.api
        current_settings = api.get_server_options()["serverOptions"]

        # Define Embed
        embed = await self.create_embed(title=f"{self.servername} Settings")
        for param, value in current_settings.items():
            embed.add_field(
                name=settings_mapper.get(param, param),
                value=icon_mapper.get(value, value),
                inline=True,
            )

        await ctx.send(embed=embed)

    @commands.is_owner()
    @sf.command(name="console")
    async def console(self, ctx, *, cmd):
        """Send a console command"""
        api = self.api
        try:
            result = api.run_command(cmd)
        except Exception as e:
            print(e)
            await ctx.send(f"Cloud not execute the command: {cmd}")
            await ctx.send(e)
        else:
            await ctx.send(f"Command `{cmd}` executed!")
            await ctx.send(f"Result: {result}")

    @commands.is_owner()
    @sf.group()
    async def user(self, ctx):
        """Manage bot access rights"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Commadn not found. Use `!help sf user`")

    @user.command(name="add")
    async def add_bot_user(self, ctx, member: discord.Member):
        """Add user to bot admin role"""
        guild = ctx.guild
        admin_role = self.admin_role
        # Check if role exists
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            print(f"Role `{admin_role}` already exists.")
        else:
            # create role
            try:
                await guild.create_role(name=admin_role, hoist=True)
            except Exception as e:
                print(e)
                await ctx.send(f"Could not create role `{admin_role}`.")
                return
            else:
                print(f"Role {admin_role} created")
                await ctx.send(f"I created role `{admin_role}`.")

        # Add user to role
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            try:
                await member.add_roles(discord.utils.get(guild.roles, name=admin_role))
            except Exception as e:
                print(e)
                await ctx.send(f"Could not add `{member}` role `{admin_role}`.")
            else:
                print(f"@{member} added to role {admin_role} created")
                await ctx.send(f"I added {member.mention} to role `{admin_role}`.")

    @user.command(name="remove")
    async def remove_bot_user(self, ctx, member: discord.Member):
        """Remove user from bot admin role"""
        guild = ctx.guild
        admin_role = self.admin_role
        # Check if role exists
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            print(f"Role {admin_role} already exists.")
        else:
            print(f"Role {admin_role} does not exist!")
            await ctx.send(f"There are no users configured in role `{admin_role}`.")

        # Remove user from role
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            try:
                await member.remove_roles(
                    discord.utils.get(guild.roles, name=admin_role)
                )
            except Exception as e:
                print(e)
                await ctx.send(f"Could not remove `{member}` from role `{admin_role}`.")
            else:
                print(f"@{member} removed from role {admin_role}")
                await ctx.send(f"I removed {member.mention} from role `{admin_role}`.")

    @commands.has_role(conf.get("DC_SF_ADMIN_ROLE"))
    @sf.group()
    async def set(self, ctx):
        """Change server settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf set`")

    @set.command(name="auto_save")
    async def auto_save(self, ctx, value):
        """Auto save game on player disconnect"""
        await self.change_setting(ctx, "FG.DSAutoSaveOnDisconnect", value)

    @set.command(name="auto_pause")
    async def auto_pause(self, ctx, value):
        """Auto pause game on player disconnect"""
        await self.change_setting(ctx, "FG.DSAutoPause", value)

    @set.command(name="save_interval")
    async def save_interval(self, ctx, value):
        """Auto save interval"""
        await self.change_setting(ctx, "FG.AutosaveInterval", value)

    @set.command(name="restart_time")
    async def restart_time(self, ctx, value):
        """Server restart time"""
        await self.change_setting(ctx, "FG.ServerRestartTimeSlot", value)

    @set.command(name="gameplay_data")
    async def gameplay_data(self, ctx, value):
        """Send Gameplay Data"""
        await self.change_setting(ctx, "FG.SendGameplayData", value)

    @set.command(name="network_quality")
    async def network_quality(self, ctx, value):
        """Set network quality"""
        await self.change_setting(ctx, "FG.NetworkQuality", int(value))

    # Do the actual change
    async def change_setting(self, ctx, setting, value):
        api = self.api
        try:
            api.apply_server_options({setting: value})
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            await ctx.send("Could not change setting")
        else:
            await ctx.send(
                f"I changed the value of **{settings_mapper.get(setting, setting)}** to **{value}**"
            )

    # Create a discord embed
    async def create_embed(self, title="Ficsit2Discord Bot", color=0x00B0F4):
        # Define Embed
        embed = discord.Embed(
            title=title,
            colour=color,
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(
            name="Ficsit2Discord Bot",
            icon_url=bot_logo,
            url="https://github.com/Brazier85/Ficsit2Discord",
        )
        embed.set_thumbnail(url=bot_logo)
        embed.set_footer(text="Ficsit2Discord Bot")
        return embed

    def probeLightAPI(self, conf: ConfigManager):
        msgID = bytes.fromhex("D5F6")  # Protocol Magic identifying the UDP Protocol
        msgType = np.uint8(
            self.messageTypes["PollServerState"]
        )  # Identifier for 'Poll Server State' message
        msgProtocol = np.uint8(
            self.protocolVersion
        )  # Identifier for protocol version identification
        msgData = np.uint64(
            time.perf_counter()
        )  # "Cookie" payload for server state query. Can be anything.
        msgEnds = np.uint8(1)  # End of Message marker

        srvAddress = conf.get("SF_IP")
        srvPort = int(conf.get("SF_PORT"))
        bufferSize = 1024
        msgToServer = msgID + msgType + msgProtocol + msgData + msgEnds
        msgFromServer = None

        time_sent = time.perf_counter()
        with socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM
        ) as UDPClientSocket:
            UDPClientSocket.sendto(msgToServer, (srvAddress, srvPort))
            UDPClientSocket.settimeout(0.7)
            try:
                msgFromServer = UDPClientSocket.recvfrom(bufferSize)
            except socket.timeout:
                return (None, None)
        time_recv = time.perf_counter()
        return msgFromServer[0], time_recv - time_sent

    def probe_udp(self, conf: ConfigManager):
        udp_probe = self.probeLightAPI(conf)
        if udp_probe == (None, None):
            return {"ServerState": 0, "ServerName": "X", "ServerNetCL": "None"}
        else:
            udp_result = self.parseLightAPIResponse(udp_probe[0])
            return udp_result

    def parseLightAPIResponse(self, data=None):
        if not data:
            raise ValueError("parseLightAPIResponse() called with empty response.")
        # Validate the envelope
        validFingerprint = (
            b"\xd5\xf6",
            self.messageTypes["ServerStateResponse"],
            self.protocolVersion,
        )
        packetFingerprint = struct.unpack("<2s B B", data[:4])
        if not packetFingerprint == validFingerprint:
            raise ValueError(
                f"Unknown packet type received.  Expected {validFingerprint}; received {packetFingerprint}. "
            )
        packetTerminator = struct.unpack("<B", data[-1:])
        validTerminator = (1,)
        if not packetTerminator == validTerminator:
            raise ValueError(
                f"Unknown packet terminator.  Expected {validTerminator}; received {packetTerminator}. "
            )
        payload = data[4:-1]  # strip the envelope from the datagram
        response = {}
        response["Cookie"] = struct.unpack("<Q", payload[:8])[0]
        response["ServerState"] = struct.unpack("B", payload[8:9])[0]
        response["ServerNetCL"] = struct.unpack("<I", payload[9:13])[0]
        response["ServerFlags"] = struct.unpack("<Q", payload[13:21])[0]
        response["NumSubStates"] = int(struct.unpack("B", payload[21:22])[0])
        response["SubStates"] = []
        sub_states_offset = 22
        if response["NumSubStates"] > 0:
            offset_cursor = sub_states_offset
            for _ in range(response["NumSubStates"]):
                sub_state = {}
                sub_state["SubStateId"] = struct.unpack(
                    "B", payload[offset_cursor : offset_cursor + 1]
                )[0]
                offset_cursor += 1
                sub_state["SubStateVersion"] = struct.unpack(
                    "<H", payload[offset_cursor : offset_cursor + 2]
                )[0]
                offset_cursor += 2
                response["SubStates"].append(sub_state)
                sub_states_offset += 3  # Adjust based on actual sub state size
        # Calculate server name offset once
        server_name_length_offset = sub_states_offset
        server_name_offset = server_name_length_offset + 2
        response["ServerNameLength"] = struct.unpack(
            "<H", payload[server_name_length_offset : server_name_length_offset + 2]
        )[0]
        raw_name = struct.unpack(
            f'{response["ServerNameLength"]}s',
            payload[
                server_name_offset : server_name_offset + response["ServerNameLength"]
            ],
        )[0]
        response["ServerName"] = raw_name.decode("utf-8")
        return response


async def setup(bot):
    await bot.add_cog(Satisfactory(bot))


def main() -> None:
    try:
        raise NotImplementedError("bot_config.py should not be executed directly.")
    except NotImplementedError as e:
        print(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
