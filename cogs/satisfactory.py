import datetime
import logging
import socket
import struct
import sys
import time

import discord
import numpy as np
from discord.ext import commands, tasks
from pyfactorybridge.exceptions import SaveGameFailed
from satisfactory_api_client.data import ServerOptions

from data.config import ConfigManager

# Mappers
from data.mappers import (
    icon_mapper,
    messageTypes,
    serverStates,
    serverSubStates,
    settings_mapper,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot_logo = "https://raw.githubusercontent.com/Brazier85/Ficsit2Discord/refs/heads/main/files/f2d_logo.webp"
conf = ConfigManager()
heart_beats = 0
last_server_state = ""
dt = datetime.datetime.now()
next_save = dt + datetime.timedelta(hours=1, minutes=-dt.minute, seconds=-dt.second)

utc = datetime.timezone.utc


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

    @tasks.loop(seconds=15)
    async def sf_server_monitor(self):
        global heart_beats
        global last_server_state
        heart_beats += 1
        logger.info(f"heartbeat: {heart_beats:4}")
        try:
            udpstatus = self.probe_udp(conf)
            server_state = self.serverStates[udpstatus["ServerState"]]
            logger.info(f"UDP Probe complete.  {server_state=}")
            # server_name = udpstatus['ServerName']
            if server_state != last_server_state:
                if server_state == "Offline":
                    prefix_icon = "❌"
                elif server_state == "Live":
                    prefix_icon = "✅"
                else:
                    prefix_icon = "⚠"
                # Do channel update
                chan_id = conf.get("DISCORD_STATE_CHANNEL")
                channel = await self.bot.fetch_channel(chan_id)
                await channel.edit(name=f"satisfactory-{prefix_icon}")
            else:
                logger.info("heartbeat: State did not change!")
        except Exception as err:
            self.handle_error(err, "Cloud not get server state!")
        else:
            await self.sf_auto_save()

    async def sf_auto_save(self):
        global next_save
        try:
            thread = await self.bot.fetch_channel(conf.get("DISCORD_AUTOSAVE_CHANNEL"))
        except Exception as err:
            self.handle_error(err, "Could not find Channel/Thread for Autosave")
            # Creating Thread
            channel = await self.bot.fetch_channel(conf.get("DISCORD_STATE_CHANNEL"))
            thread = await channel.create_thread(
                name="F2D AutoSave", type=discord.ChannelType.public_thread
            )
            conf.set("DISCORD_AUTOSAVE_CHANNEL", thread.id)

        if datetime.datetime.now() > next_save:
            logger.info(f"Using {thread} for auto save posts")
            dt = datetime.datetime.now()
            next_save = dt + datetime.timedelta(
                hours=2, minutes=-dt.minute, seconds=-dt.second
            )
            await self.save(thread, save_name="Discord_AutoSave", silent=True)
            logger.info(f"Next save: {next_save}")
        else:
            logger.info(f"No autosave required: Next save: {next_save}")

    @commands.hybrid_group(fallback="sf")
    async def sf(self, ctx):
        """Everything related to Satisfactory Servers"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf`")

    @commands.has_role(conf.get("DISCORD_SF_ADMIN_ROLE"))
    @sf.command(name="restart")
    async def restart(self, ctx):
        """Save the game and restart the server."""
        await self.perform_server_action(
            ctx,
            self.api.shutdown,
            "Server Successfully stopped!",
            "Error on shutdown!",
            "Could not shutdown the server!",
            save_before=True,
        )

    @commands.has_role(conf.get("DISCORD_SF_ADMIN_ROLE"))
    @sf.command(name="save")
    async def save(self, ctx, save_name="Ficit2Discord", silent=False):
        """This command will save the game"""
        api = self.api
        msg = await ctx.send("Saving game...", silent=silent)
        try:
            api.save_game(save_name=save_name)
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
            response = api.download_save_game(save_name)
            if response and isinstance(response.data, bytes):  # Ensure data is in bytes
                with open(save_path, "wb") as file:
                    file.write(response.data)
        except Exception as err:
            self.handle_error(err, "Could not download save game")
            await msg.edit(content="Could not download the save game")
        else:
            file = discord.File(save_path)

            # Define embed
            embed = await self.create_embed(
                title=f"{self.servername} Savegame",
                color=0x00F51D,
                fields=[
                    {
                        "name": "",
                        "value": ":white_check_mark: Successfully saved game!",
                        "inline": False,
                    },
                    {
                        "name": "Save File",
                        "value": f"`{save_filename}`",
                        "inline": True,
                    },
                ],
            )
            try:
                await ctx.send(file=file, embed=embed, silent=silent)
                await msg.delete()
            except Exception as err:
                self.handle_error(err, "Error sending file")
                await msg.edit("Could not send save file to Discord!", silent=silent)

    @sf.command(name="connect")
    async def sf_connect(self, ctx):
        """Show server connection details"""
        embed = await self.create_embed(
            title=f"{self.servername} Details",
            fields=[
                {
                    "name": "Address",
                    "value": conf.get("SF_PUBLIC_ADDR"),
                    "inline": False,
                },
                {"name": "Password", "value": "Ask a Moderator", "inline": False},
            ],
        )
        await ctx.send(embed=embed)

    @sf.command(name="state")
    async def state(self, ctx):
        """Will post the current server state"""
        api = self.api
        server_state = api.query_server_state()
        current_health = api.health_check().data["health"]
        if server_state.success:
            # Create vars
            current_state = server_state.data["serverGameState"]
            playtime = str(
                datetime.timedelta(seconds=current_state["totalGameDuration"])
            )
            p_max = current_state["playerLimit"]
            p_online = current_state["numConnectedPlayers"]
            ticks = current_state["averageTickRate"]
            tech_tier = current_state["techTier"]
            session_name = current_state["activeSessionName"]
            paused = current_state["isGamePaused"]
            health = current_health
            color = 0x00F51D if health == "healthy" else 0xFFF700

            # Define Embed
            embed = await self.create_embed(
                color=color,
                title=f"{self.servername} Status",
                fields=[
                    {
                        "name": "",
                        "value": f"{icon_mapper.get(health, health)} Server is **{health}**",
                        "inline": False,
                    },
                    {"name": "Players", "value": f"{p_online}/{p_max}", "inline": True},
                    {"name": "Avg Ticks", "value": f"{ticks:.2f}", "inline": True},
                    {"name": "Playtime", "value": f"{playtime}", "inline": True},
                    {
                        "name": "Game paused",
                        "value": f"{icon_mapper.get(str(paused), paused)}",
                        "inline": True,
                    },
                    {"name": "Tech Tier", "value": f"{tech_tier}", "inline": True},
                    {
                        "name": "Session Name",
                        "value": f"{session_name}",
                        "inline": True,
                    },
                ],
            )

        await ctx.send(embed=embed)

    @sf.command(name="settings")
    async def options(self, ctx):
        """Show the current server settings"""
        api = self.api
        current_settings = api.get_server_options().data["serverOptions"]

        # Define Embed
        fields = [
            {
                "name": settings_mapper.get(param, param),
                "value": icon_mapper.get(value, value),
                "inline": True,
            }
            for param, value in current_settings.items()
        ]
        embed = await self.create_embed(
            title=f"{self.servername} Settings", fields=fields
        )
        await ctx.send(embed=embed)

    @commands.is_owner()
    @sf.command(name="console")
    async def console(self, ctx, *, cmd):
        """Send a console command"""
        await self.perform_server_action(
            ctx,
            lambda: self.api.run_command(cmd),
            f"Command `{cmd}` executed!",
            f"Could not execute the command: {cmd}",
            f"Could not execute the command: {cmd}",
        )

    @commands.is_owner()
    @sf.group()
    async def user(self, ctx):
        """Manage bot access rights"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf user`")

    @user.command(name="add")
    async def add_bot_user(self, ctx, member: discord.Member):
        """Add user to bot admin role"""
        guild = ctx.guild
        admin_role = self.admin_role
        # Check if role exists
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            logger.info(f"Role `{admin_role}` already exists.")
        else:
            # create role
            try:
                await guild.create_role(name=admin_role, hoist=True)
            except Exception as e:
                self.handle_error(e, f"Could not create role `{admin_role}`.")
                return
            else:
                logger.info(f"Role {admin_role} created")
                await ctx.send(f"I created role `{admin_role}`.")

        # Add user to role
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            try:
                await member.add_roles(discord.utils.get(guild.roles, name=admin_role))
            except Exception as e:
                self.handle_error(
                    e, f"Could not add `{member}` to role `{admin_role}`."
                )
            else:
                logger.info(f"@{member} added to role {admin_role} created")
                await ctx.send(f"I added {member.mention} to role `{admin_role}`.")

    @user.command(name="remove")
    async def remove_bot_user(self, ctx, member: discord.Member):
        """Remove user from bot admin role"""
        guild = ctx.guild
        admin_role = self.admin_role
        # Check if role exists
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            logger.info(f"Role {admin_role} already exists.")
        else:
            logger.info(f"Role {admin_role} does not exist!")
            await ctx.send(f"There are no users configured in role `{admin_role}`.")

        # Remove user from role
        if discord.utils.get(guild.roles, name=admin_role) is not None:
            try:
                await member.remove_roles(
                    discord.utils.get(guild.roles, name=admin_role)
                )
            except Exception as e:
                self.handle_error(
                    e, f"Could not remove `{member}` from role `{admin_role}`."
                )
            else:
                logger.info(f"@{member} removed from role {admin_role}")
                await ctx.send(f"I removed {member.mention} from role `{admin_role}`.")

    @commands.has_role(conf.get("DISCORD_SF_ADMIN_ROLE"))
    @sf.group()
    async def set(self, ctx):
        """Change server settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Command not found. Use `!help sf set`")

    @set.command(name="auto_save")
    async def auto_save(self, ctx, value):
        """Auto save game on player disconnect"""
        await self.change_setting(ctx, "DSAutoSaveOnDisconnect", value)

    @set.command(name="auto_pause")
    async def auto_pause(self, ctx, value):
        """Auto pause game on player disconnect"""
        await self.change_setting(ctx, "DSAutoPause", value)

    @set.command(name="save_interval")
    async def save_interval(self, ctx, value):
        """Auto save interval"""
        await self.change_setting(ctx, "AutosaveInterval", value)

    @set.command(name="restart_time")
    async def restart_time(self, ctx, value):
        """Server restart time"""
        await self.change_setting(ctx, "ServerRestartTimeSlot", value)

    @set.command(name="gameplay_data")
    async def gameplay_data(self, ctx, value):
        """Send Gameplay Data"""
        await self.change_setting(ctx, "SendGameplayData", value)

    @set.command(name="network_quality")
    async def network_quality(self, ctx, value):
        """Set network quality"""
        await self.change_setting(ctx, "NetworkQuality", int(value))

    # Do the actual change
    async def change_setting(self, ctx, setting, value):
        api = self.api
        try:
            new_setting = ServerOptions()
            setattr(new_setting, setting, value)
            api.apply_server_options(new_setting)
        except Exception as err:
            self.handle_error(err, "Could not change setting")
            await ctx.send("Could not change setting")
        else:
            await ctx.send(
                f"I changed the value of **{settings_mapper.get(setting, setting)}** to **{value}**"
            )

    # Create a discord embed
    async def create_embed(
        self, title="Ficsit2Discord Bot", color=0x00B0F4, fields=None
    ):
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
        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", True),
                )
        return embed

    def handle_error(self, err, context_message="An error occurred"):
        logger.error(f"{context_message}: Unexpected {err=}, {type(err)=}")

    async def perform_server_action(
        self,
        ctx,
        action,
        success_message,
        error_log_message,
        error_message,
        save_before=False,
    ):
        if save_before:
            save_success = await self.save(ctx)
            if not save_success:
                await ctx.send("I could not save the game! No further action possible!")
                return
        try:
            action()
        except Exception as err:
            self.handle_error(err, error_log_message)
            await ctx.send(error_message)
        else:
            await ctx.send(success_message)

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
        raise NotImplementedError("satisfactory.py should not be executed directly.")
    except NotImplementedError as e:
        logger.error(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
