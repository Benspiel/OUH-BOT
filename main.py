import discord
from discord.ext import commands
import os
import asyncio

def load_token():
    """Liest den Token aus info.txt"""
    try:
        with open("info.txt", "r") as file:
            for line in file:
                if line.startswith("DISCORD_TOKEN="):
                    return line.strip().split("=")[1]  # Extrahiert den Token
        raise ValueError("❌ Token nicht in info.txt gefunden!")
    except FileNotFoundError:
        raise FileNotFoundError("❌ info.txt nicht gefunden! Erstelle die Datei.")

# Bot-Initialisierung
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands gesynct")
    except Exception as e:
        print(f"❌ Sync-Fehler: {e}")

async def load_cogs():
    """Lädt alle Cogs aus dem cogs-Ordner"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load_cogs()
    token = load_token()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
#bot.run("MTI4NTMxNDI2MTc4NjAzODM3Ng.GOtxGx.IYGRSmgHCpt-YHOqjnSfLQ19xHWlf7-wVaXIMA
