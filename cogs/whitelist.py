import discord
from discord.ext import commands
import json
import os
import requests

WHITELIST_FILE = "whitelist.json"
MOJANG_API_URL = "https://api.mojang.com/users/profiles/minecraft/"
REQUIRED_ROLE_ID = 1315043449606635621

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_minecraft_uuid(username):
    response = requests.get(MOJANG_API_URL + username)
    if response.status_code == 200:
        return response.json().get("id")
    return None

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="whitelist", description="Fügt einen Spieler zur Whitelist hinzu.")
    async def whitelist(self, interaction: discord.Interaction, minecraft_name: str, discord_user: discord.Member):
        # Überprüfen, ob der Benutzer die erforderliche Rolle hat
        if not any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Fehler: Du hast nicht die erforderliche Rolle, um diesen Befehl auszuführen.", ephemeral=True)
            return

        uuid = get_minecraft_uuid(minecraft_name)
        if not uuid:
            await interaction.response.send_message(f"Fehler: Konnte keine UUID für {minecraft_name} finden.", ephemeral=True)
            return

        whitelist_data = load_whitelist()
        new_entry = {
            "uuid": uuid,
            "name": minecraft_name
        }
        whitelist_data.append(new_entry)
        save_whitelist(whitelist_data)

        await interaction.response.send_message(f"{minecraft_name} wurde der Whitelist hinzugefügt für {discord_user.display_name}.", ephemeral=True)

        try:
            await discord_user.send(f"Du wurdest mit dem Minecraft-Namen '{minecraft_name}' zur Whitelist hinzugefügt!")
        except discord.Forbidden:
            await interaction.response.send_message(f"Ich konnte {discord_user.mention} keine DM senden. Bitte überprüfe deine Einstellungen.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Whitelist(bot))
