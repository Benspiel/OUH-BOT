import discord
from discord import app_commands
from discord.ext import commands

class SayModal(discord.ui.Modal, title="Nachricht senden"):
    # Mehrzeiliges Eingabefeld
    message = discord.ui.TextInput(
        label="Was soll der Bot sagen?",
        style=discord.TextStyle.paragraph,  # Mehrzeilig
        placeholder="Tippe hier deine Nachricht...",
        max_length=2000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Nachricht im aktuellen Channel senden
        await interaction.channel.send(self.message.value)
        # Bestätigung (nur für den Nutzer)
        await interaction.response.send_message(
            "✅ Nachricht wurde gesendet!",
            ephemeral=True
        )

class SayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="say",
        description="Sende eine Nachricht als Bot (öffnet ein Formular)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)  # Nur für Admins/Mods
    async def say(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SayModal())

async def setup(bot):
    await bot.add_cog(SayCog(bot))