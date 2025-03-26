import discord
from discord.ext import commands
from discord import app_commands

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_roles = self._load_allowed_roles()

    def _load_allowed_roles(self):
        """Liest Rollen-IDs aus permissions.txt (Format: 'clear:ROLE_ID')"""
        allowed_roles = []
        try:
            with open("permissions.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("clear:"):
                        role_id = int(line.split(":")[1].strip())
                        allowed_roles.append(role_id)
        except (FileNotFoundError, ValueError):
            print("⚠️ permissions.txt fehlt oder enthält ungültige Daten!")
        return allowed_roles

    def _has_permission(self, user_roles):
        """Prüft, ob der Nutzer eine der erlaubten Rollen hat."""
        return any(role.id in self.allowed_roles for role in user_roles)

    @app_commands.command(
        name="clear",
        description="Löscht ALLE Nachrichten im Channel (Admin-only)"
    )
    async def clear_all(self, interaction: discord.Interaction):
        # Berechtigung prüfen
        if not self._has_permission(interaction.user.roles):
            await interaction.response.send_message(
                "❌ Nur Admins können diesen Befehl nutzen!",
                ephemeral=True
            )
            return

        # Bestätigung anfordern
        confirm_embed = discord.Embed(
            title="⚠️ WARNUNG",
            description="**Dies löscht ALLE Nachrichten in diesem Channel!**\nBist du sicher?",
            color=discord.Color.red()
        )
        await interaction.response.send_message(
            embed=confirm_embed,
            view=ConfirmView(self),  # Button-Abfrage (siehe unten)
            ephemeral=True
        )

class ConfirmView(discord.ui.View):
    """Bestätigungs-Buttons für /clear"""
    def __init__(self, cog):
        super().__init__(timeout=30)
        self.cog = cog

    @discord.ui.button(label="Löschen", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Channel komplett leeren (Discord-API-Limit: 100 Nachrichten/Runde)
        try:
            await interaction.channel.purge(limit=None)  # Löscht ALLE Nachrichten
            await interaction.followup.send(
                "✅ Channel wurde komplett geleert!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Fehler: {e}",
                ephemeral=True
            )

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="❌ Löschen abgebrochen.",
            view=None,
            embed=None
        )

async def setup(bot):
    await bot.add_cog(ClearCog(bot))