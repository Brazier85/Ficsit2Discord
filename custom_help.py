import discord
from discord.ext import commands


class CustomHelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category (cog)."
            }
        )

    async def send_bot_help(self, mapping):
        try:
            ctx = self.context  # Ensure context is not None
            embed = discord.Embed(
                title="Bot Commands",
                description="Here is a list of all available commands:",
                color=discord.Color.blue(),
            )

            for cog, commands_list in mapping.items():
                if cog is not None:
                    cog_name = cog.qualified_name
                    cog_description = cog.description or "No description provided."

                    command_names = [
                        command.name for command in commands_list if not command.hidden
                    ]
                    if command_names:
                        # command_list_str = ", ".join(command_names)
                        command_list_str = ""
                        for cmd in command_names:
                            command_list_str = f"{command_list_str}\n- {cmd}"
                        embed.add_field(
                            name=cog_name,
                            value=f"{cog_description}\n\n**Commands:**{command_list_str}",
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=cog_name, value=cog_description, inline=False
                        )

            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in send_bot_help: {e}")

    async def send_cog_help(self, cog):
        try:
            ctx = self.context  # Ensure context is available
            embed = discord.Embed(
                title=f"{cog.qualified_name} Commands",
                description=cog.description or "No description",
                color=discord.Color.blue(),
            )
            for command in cog.get_commands():
                embed.add_field(
                    name=command.name,
                    value=command.help or "No description",
                    inline=False,
                )

            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in send_cog_help: {e}")

    async def send_command_help(self, command):
        try:
            ctx = self.context  # Ensure context is available
            embed = discord.Embed(
                title=command.name,
                description=command.help or "No description",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in send_command_help: {e}")


def setup(bot):
    print("Setting up Custom Help Command...")  # Debugging statement
    bot.help_command = CustomHelpCommand()  # Ensure this does not return None
