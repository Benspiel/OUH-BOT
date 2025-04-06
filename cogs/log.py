import discord
from discord.ext import commands
import datetime

LIFECYCLE_CHANNEL_ID = 1358381517872562218  # 👈 Ersetze mit deiner Channel-ID

class LifecycleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None

    def get_embed(self, title: str, description: str, color: discord.Color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Bot Lifecycle")
        return embed

    async def send_embed(self, embed: discord.Embed):
        if self.channel is None:
            self.channel = self.bot.get_channel(LIFECYCLE_CHANNEL_ID)
        if self.channel:
            await self.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        embed = self.get_embed(
            title="✅ Bot ist online!",
            description="Der Bot wurde erfolgreich gestartet und ist einsatzbereit.",
            color=discord.Color.green()
        )
        await self.send_embed(embed)

    @commands.Cog.listener()
    async def on_disconnect(self):
        embed = self.get_embed(
            title="🛑 Bot wurde getrennt!",
            description="Der Bot hat die Verbindung zu Discord verloren oder wurde gestoppt.",
            color=discord.Color.red()
        )
        await self.send_embed(embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        embed = self.get_embed(
            title="📥 Textbefehl ausgeführt",
            description=f"`{ctx.command}` wurde von `{ctx.author}` in `{ctx.channel}` ausgeführt.",
            color=discord.Color.blurple()
        )
        await self.send_embed(embed)

    @commands.Cog.listener()
    async def on_app_command(self, interaction: discord.Interaction):
        embed = self.get_embed(
            title="📥 Slash Command ausgeführt",
            description=f"`/{interaction.command.name}` wurde von `{interaction.user}` in `{interaction.channel}` ausgeführt.",
            color=discord.Color.teal()
        )
        await self.send_embed(embed)

async def setup(bot):
    await bot.add_cog(LifecycleCog(bot))
