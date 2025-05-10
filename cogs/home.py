import discord
from discord import app_commands
from discord.ext import commands

ROLE_ID = 1357345202959814737  # Deine Rollen-ID
FORUM_CHANNEL_ID = 1370866761381183590  # Ersetze durch die ID deines Forum-Channels

class HomeForm(discord.ui.Modal, title="Koordinaten angeben"):

    x = discord.ui.TextInput(label="X", placeholder="z. B. 123", max_length=50)
    y = discord.ui.TextInput(label="Y", placeholder="z. B. 64", max_length=50)
    z = discord.ui.TextInput(label="Z", placeholder="z. B. 456", max_length=50)

    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def on_submit(self, interaction: discord.Interaction):
        forum_channel = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        if not isinstance(forum_channel, discord.ForumChannel):
            await interaction.response.send_message("Forum-Channel nicht gefunden!", ephemeral=True)
            return

        title = f"{self.x.value}, {self.y.value}, {self.z.value}"
        content = f"Von: {self.author.display_name}"

        await forum_channel.create_thread(name=title, content=content)
        await interaction.response.send_message("Eintrag wurde im Forum erstellt.", ephemeral=True)


class Home(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="home", description="Öffnet das Koordinatenformular")
    async def home(self, interaction: discord.Interaction):
        member = interaction.user
        if not any(role.id == ROLE_ID for role in member.roles):
            await interaction.response.send_message("Du hast keine Berechtigung, diesen Befehl zu nutzen.", ephemeral=True)
            return

        await interaction.response.send_modal(HomeForm(author=member))

async def setup(bot):
    await bot.add_cog(Home(bot))
