import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

blocked_users = {}  # Gesperrte Benutzer pro Voice-Channel

async def clear_channel(channel):
    """Löscht alle Nachrichten in einem Textkanal."""
    await channel.purge()

class KickDropdown(discord.ui.Select):
    def __init__(self, voice_channel):
        self.voice_channel = voice_channel
        options = [discord.SelectOption(label=member.name, value=str(member.id)) for member in voice_channel.members]
        super().__init__(placeholder="Wähle Benutzer zum Kicken", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            user_id = int(self.values[0])
            user = interaction.guild.get_member(user_id)
            if user:
                await user.move_to(None)
                await interaction.response.send_message(f"{user.name} wurde gekickt.", ephemeral=True)
            else:
                await interaction.response.send_message("Benutzer nicht gefunden.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Kicken des Benutzers: {e}", ephemeral=True)

class KickView(discord.ui.View):
    def __init__(self, voice_channel):
        super().__init__()
        self.add_item(KickDropdown(voice_channel))

class BlockDropdown(discord.ui.Select):
    def __init__(self, voice_channel):
        self.voice_channel = voice_channel
        options = [discord.SelectOption(label=member.name, value=str(member.id)) for member in voice_channel.members]
        super().__init__(placeholder="Wähle Benutzer zum Blockieren", options=options, min_values=1, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        try:
            if self.voice_channel not in blocked_users:
                blocked_users[self.voice_channel] = set()

            blocked = []
            for user_id in self.values:
                user = interaction.guild.get_member(int(user_id))
                if user:
                    blocked_users[self.voice_channel].add(user.id)
                    await self.voice_channel.set_permissions(user, connect=False)
                    blocked.append(user.name)

            await interaction.response.send_message(f"**Geblockt:** {', '.join(blocked)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Blockieren der Benutzer: {e}", ephemeral=True)

class BlockView(discord.ui.View):
    def __init__(self, voice_channel):
        super().__init__()
        self.add_item(BlockDropdown(voice_channel))

class UnblockDropdown(discord.ui.Select):
    def __init__(self, voice_channel):
        self.voice_channel = voice_channel
        blocked_members = blocked_users.get(self.voice_channel, set())

        # Optionen für entblockte Mitglieder erstellen
        options = [
            discord.SelectOption(label=interaction.guild.get_member(user_id).name, value=str(user_id))
            for user_id in blocked_members if interaction.guild.get_member(user_id)
        ]

        # Wenn keine Optionen vorhanden sind, Setzen des Platzhalters
        if not options:
            options = [discord.SelectOption(label="Keine blockierten Benutzer", value="no_users")]

        # max_values auf die Anzahl der Optionen setzen
        max_values = 1 if options[0].value == "no_users" else len(options)

        super().__init__(placeholder="Wähle Benutzer zum Entblocken", options=options, min_values=1, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        try:
            if "no_users" in self.values:
                await interaction.response.send_message("Es gibt keine blockierten Benutzer in diesem Kanal.", ephemeral=True)
                return

            unblocked = []
            for user_id in self.values:
                user = interaction.guild.get_member(int(user_id))
                if user:
                    blocked_users[self.voice_channel].discard(user.id)
                    await self.voice_channel.set_permissions(user, connect=None)
                    unblocked.append(user.name)

            await interaction.response.send_message(f"**Entblockt:** {', '.join(unblocked)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Entblocken der Benutzer: {e}", ephemeral=True)

class UnblockView(discord.ui.View):
    def __init__(self, voice_channel):
        super().__init__()
        self.add_item(UnblockDropdown(voice_channel))

@bot.event
async def on_ready():
    print(f'Bot ist bereit als {bot.user}')

    # Kanal-ID anpassen
    channel_id = 1338574059138453514
    channel = bot.get_channel(channel_id)

    if channel:
        try:
            await clear_channel(channel)

            # Kick View
            kick_view = discord.ui.View()
            kick_button = discord.ui.Button(label="Benutzer kicken", style=discord.ButtonStyle.danger)

            async def kick_button_callback(interaction: discord.Interaction):
                if interaction.user.voice and interaction.user.voice.channel:
                    voice_channel = interaction.user.voice.channel
                    # Nur der erste Benutzer im Channel darf die Buttons benutzen
                    if voice_channel.members[0] == interaction.user:
                        view = KickView(voice_channel)
                        await interaction.response.send_message("Wähle einen Benutzer zum Kicken:", view=view, ephemeral=True)
                    else:
                        await interaction.response.send_message("Nur der erste Benutzer im Kanal kann diese Funktion verwenden.", ephemeral=True)
                else:
                    await interaction.response.send_message("Du bist in keinem Voice-Channel.", ephemeral=True)

            kick_button.callback = kick_button_callback
            kick_view.add_item(kick_button)

            # Block View
            block_view = discord.ui.View()
            block_button = discord.ui.Button(label="Benutzer blockieren", style=discord.ButtonStyle.danger)

            async def block_button_callback(interaction: discord.Interaction):
                if interaction.user.voice and interaction.user.voice.channel:
                    voice_channel = interaction.user.voice.channel
                    # Nur der erste Benutzer im Channel darf die Buttons benutzen
                    if voice_channel.members[0] == interaction.user:
                        view = BlockView(voice_channel)
                        await interaction.response.send_message("Wähle Benutzer zum Blockieren:", view=view, ephemeral=True)
                    else:
                        await interaction.response.send_message("Nur der erste Benutzer im Kanal kann diese Funktion verwenden.", ephemeral=True)

            block_button.callback = block_button_callback
            block_view.add_item(block_button)

            # Unblock View
            unblock_view = discord.ui.View()
            unblock_button = discord.ui.Button(label="Benutzer entblocken", style=discord.ButtonStyle.success)

            async def unblock_button_callback(interaction: discord.Interaction):
                if interaction.user.voice and interaction.user.voice.channel:
                    voice_channel = interaction.user.voice.channel
                    # Nur der erste Benutzer im Channel darf die Buttons benutzen
                    if voice_channel.members[0] == interaction.user:
                        view = UnblockView(voice_channel)
                        await interaction.response.send_message("Wähle Benutzer zum Entblocken:", view=view, ephemeral=True)
                    else:
                        await interaction.response.send_message("Nur der erste Benutzer im Kanal kann diese Funktion verwenden.", ephemeral=True)

            unblock_button.callback = unblock_button_callback
            unblock_view.add_item(unblock_button)

            # Send messages to channel
            await channel.send("**Benutzer Management**", view=kick_view)
            await channel.send("**Blockierte Benutzer Verwaltung**", view=block_view)
            await channel.send("**Entblocken von Benutzern**", view=unblock_view)

        except Exception as e:
            print(f"Fehler beim Initialisieren des Bots: {e}")
    else:
        print(f"Channel mit der ID {channel_id} wurde nicht gefunden.")

# Lade den Token aus der info.txt Datei
def get_token_from_file():
    try:
        with open("info.txt", "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Fehler beim Laden des Tokens: {e}")
        return None

token = get_token_from_file()

if token:
    bot.run(token)
else:
    print("Bot konnte nicht gestartet werden, da der Token nicht gefunden wurde.")
