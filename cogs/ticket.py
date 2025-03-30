from discord.ext import commands
from discord.ui import Select, View, Button
from discord import ButtonStyle, Interaction, PermissionOverwrite, Embed
import discord
import asyncio
from datetime import datetime

# Konfiguration
TICKET_CHANNEL_ID = 1338961833997897844  # Ticket-Erstellungs-Channel
LOG_CHANNEL_ID = 1355552186867908797     # Log-Channel-ID
CLOSED_CATEGORY_NAME = "🔒 Geschlossene Tickets"

# Kategorien mit individuellen Beschreibungen und Support-Rollen
TICKET_CATEGORIES = {
    "Stadtrat Bewerbung": {
        "category_id": 1315355000230117490,
        "support_role_id": 1315355000230117490,
        "description": "Bewerbung für das Stadtrat-Team einreichen"
    },
    "Support Bewerbung": {
        "category_id": 1315355000230117490,
        "support_role_id": 1315355000230117490,
        "description": "Bewerbung für unser Support-Team"
    },
    "Developer Bewerbung": {
        "category_id": 1315355000230117490,
        "support_role_id": 1315355000230117490,
        "description": "<:developper:1355633326161006682> Bewirb dich als Developer"
    },
    "Eigenes Event": {
        "category_id": 1330568895404441733,
        "support_role_id": 1330568895404441733,
        "description": "Eigenes Event vorschlagen oder organisieren"
    }
}

class PersistentView(View):
    def __init__(self):
        super().__init__(timeout=None)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category_name,
                description=category_data["description"],
                emoji="📩"
            )
            for category_name, category_data in TICKET_CATEGORIES.items()
        ]
        super().__init__(
            placeholder="Ticket-Typ wählen...",
            options=options,
            custom_id="persistent_ticket_dropdown",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("🔄 Ticket wird erstellt...", ephemeral=True)
        await self.create_ticket(interaction)

    async def create_ticket(self, interaction: Interaction):
        guild = interaction.guild
        user = interaction.user
        ticket_type = self.values[0]
        category_data = TICKET_CATEGORIES[ticket_type]

        category = guild.get_channel(category_data["category_id"])
        support_role = guild.get_role(category_data["support_role_id"])

        if not category or not support_role:
            await interaction.followup.send("❌ Konfigurationsfehler - Kategorie oder Rolle nicht gefunden!", ephemeral=True)
            return

        # Geschlossene Kategorie finden/erstellen
        closed_category = discord.utils.get(guild.categories, name=CLOSED_CATEGORY_NAME)
        if not closed_category:
            closed_category = await guild.create_category(CLOSED_CATEGORY_NAME)
            await closed_category.set_permissions(guild.default_role, view_channel=False)

        # Channel erstellen
        ticket_channel = await guild.create_text_channel(
            name=f"{ticket_type[:15]}-{user.display_name[:8]}".lower().replace(" ", "-"),
            category=category,
            reason=f"{ticket_type}-Ticket von {user.name}"
        )

        # Berechtigungen setzen
        await ticket_channel.set_permissions(guild.default_role, view_channel=False)
        await ticket_channel.set_permissions(user, view_channel=True, send_messages=True)
        await ticket_channel.set_permissions(support_role,
                                             view_channel=True,
                                             send_messages=True,
                                             manage_messages=True)

        # Ticket-Embed mit individueller Beschreibung
        embed = discord.Embed(
            title=f"{ticket_type} Ticket",
            description=f"**Erstellt von:** {user.mention}\n"
                        f"**Zuständiges Team:** {support_role.mention}\n"
                        f"**Beschreibung:** {category_data['description']}\n"
                        f"**Status:** Offen",
            color=0x3498db
        )

        view = PersistentView()
        view.add_item(CloseButton())

        await ticket_channel.send(embed=embed, view=view)
        await self.send_log(
            guild,
            f"🎟️ {ticket_type} Ticket erstellt: {ticket_channel.mention}\n"
            f"**Von:** {user.mention} | **Zuständig:** {support_role.mention}\n"
            f"**Beschreibung:** {category_data['description']}"
        )

    async def send_log(self, guild, message):
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = Embed(
                description=message,
                color=0x3498db,
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

class CloseButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.red,
            label="Schließen",
            custom_id="persistent_close_ticket"
        )

    async def callback(self, interaction: Interaction):
        confirm_embed = discord.Embed(
            title="Ticket wirklich schließen?",
            description="Sie werden diesen Channel nicht mehr sehen können, aber das zuständige Team behält Zugriff.",
            color=0xff0000
        )

        confirm_view = View()
        confirm_view.add_item(ConfirmCloseButton())
        confirm_view.add_item(CancelButton())

        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)

class ConfirmCloseButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.red,
            label="Bestätigen",
            custom_id="confirm_close_ticket"
        )

    async def callback(self, interaction: Interaction):
        channel = interaction.channel

        # Nur den aktuellen Nutzer unsichtbar machen
        await channel.set_permissions(interaction.user, view_channel=False)

        # Ticket-Typ aus Channel-Namen extrahieren
        ticket_type = channel.name.split("-")[0]
        category_data = next(
            (data for name, data in TICKET_CATEGORIES.items()
             if name.lower().startswith(ticket_type)),
            None
        )

        # Log-Eintrag
        log_msg = f"🔒 {ticket_type.capitalize()} Ticket geschlossen: {channel.mention} von {interaction.user.mention}"
        if category_data:
            support_role = interaction.guild.get_role(category_data["support_role_id"])
            if support_role:
                log_msg += f" | Zuständig: {support_role.mention}"

        await TicketDropdown().send_log(interaction.guild, log_msg)
        await interaction.response.send_message(
            "✅ Der Channel ist jetzt für Sie unsichtbar, bleibt aber für das zuständige Team verfügbar.",
            ephemeral=True
        )

class CancelButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.gray,
            label="Abbrechen",
            custom_id="cancel_close_ticket"
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(content="✅ Aktion abgebrochen", embed=None, view=None)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistent_views_added = False

    async def setup_hook(self):
        if not self.persistent_views_added:
            self.bot.add_view(PersistentView().add_item(TicketDropdown()))
            self.persistent_views_added = True

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot ist online als {self.bot.user}")
        if not hasattr(self, 'ticket_message_sent'):
            self.ticket_message_sent = True
            await self.update_ticket_message()

    async def update_ticket_message(self):
        channel = self.bot.get_channel(TICKET_CHANNEL_ID)
        if channel:
            try:
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user:
                        await message.delete()

                embed = discord.Embed(
                    title="🎫 Ticket-System",
                    description="Wähle eine Kategorie aus um ein Ticket zu erstellen:",
                    color=0x3498db
                )
                view = PersistentView()
                view.add_item(TicketDropdown())
                await channel.send(embed=embed, view=view)
            except Exception as e:
                print(f"Fehler beim Aktualisieren: {e}")

async def setup(bot):
    cog = Ticket(bot)
    await bot.add_cog(cog)
    await cog.setup_hook()