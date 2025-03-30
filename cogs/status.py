import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Lade die Berechtigungen aus der Datei
PERMISSIONS_FILE = "permissions.txt"
def get_required_role():
    try:
        with open(PERMISSIONS_FILE, "r") as f:
            for line in f.readlines():
                if line.startswith("status:"):
                    return int(line.split(":")[1].strip())
    except FileNotFoundError:
        return None
    return None

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.required_role = get_required_role()

    @commands.hybrid_command(name="status", with_app_command=True)
    async def status(self, ctx, status_type: str, *, status_text: str):
        """Setzt den Status des Bots. Wähle zwischen: custom, playing, streaming, listening, watching."""

        # Prüfen, ob der Benutzer die erforderliche Rolle hat
        if self.required_role and self.required_role not in [role.id for role in ctx.author.roles]:
            await ctx.send("Du hast keine Berechtigung, diesen Befehl zu nutzen.", ephemeral=True)
            return

        if status_type.lower() == "custom":
            activity = discord.CustomActivity(name=status_text)
        elif status_type.lower() == "playing":
            activity = discord.Game(name=status_text)
        elif status_type.lower() == "streaming":
            activity = discord.Streaming(name=status_text, url="https://twitch.tv/example")
        elif status_type.lower() == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_text)
        elif status_type.lower() == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
        else:
            await ctx.send("Ungültiger Status-Typ! Wähle zwischen: custom, playing, streaming, listening, watching.", ephemeral=True)
            return

        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Status wurde gesetzt: `{status_type.capitalize()}` - `{status_text}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusCog(bot))