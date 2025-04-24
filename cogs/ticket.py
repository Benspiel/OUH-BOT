import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import asyncio
from datetime import datetime

# KONFIGURATION
TICKET_CHANNEL_ID = 1338961833997897844  # Ticket-Dropdown-Channel
LOG_CHANNEL_ID = 1355552186867908797     # Log-Channel

# Einstellungen für jede Kategorie
CATEGORY_SETTINGS = {
    "event": {
        "support_role_id": 1259047794446958632,
        "category_name": "Eigenes Event",
        "emoji": "🎫",
        "discord_category_id": 1330568895404441733
    },
    "oberattack": {
        "support_role_id": 1357297363697402028,
        "category_name": "Oberattack",
        "emoji": "🌍",
        "discord_category_id": 1357070504875266138
    },
    "normal": {
        "support_role_id": 123456789012345678,  # 👈 Ersetze mit deiner Support-Rollen-ID
        "category_name": "Normales Ticket",
        "emoji": "📩",
        "discord_category_id": 123456789012345678  # 👈 Ersetze mit deiner Kategorie-ID
    }
}

class TicketView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        placeholder="Wählen Sie eine Kategorie aus",
        custom_id="ticket_category",
        options=[
            discord.SelectOption(
                label=settings["category_name"],
                value=key,
                emoji=settings["emoji"]
            )
            for key, settings in CATEGORY_SETTINGS.items()
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        await interaction.response.defer()

        selected = select.values[0]
        settings = CATEGORY_SETTINGS[selected]
        guild = interaction.guild
        creator = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            creator: discord.PermissionOverwrite(read_messages=True),
            guild.get_role(settings["support_role_id"]): discord.PermissionOverwrite(read_messages=True)
        }

        category = guild.get_channel(settings["discord_category_id"])
        if not category:
            category = await guild.create_category(settings["category_name"])

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{creator.display_name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"{settings['emoji']} {settings['category_name']} Ticket",
            color=discord.Color.green()
        )
        embed.description = f"**Ersteller:** {creator.mention}\n"
        embed.description += f"**Kategorie:** {settings['category_name']}\n"
        embed.description += f"**Kümmert sich um dich:** Niemand"

        view = TicketActionsView(self.bot, settings["support_role_id"])

        await ticket_channel.send(embed=embed, view=view)

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🎫 Ticket eröffnet",
                description=f"{settings['emoji']} **{settings['category_name']}** Ticket von {creator.mention}",
                color=discord.Color.green()
            )
            log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=False)
            log_embed.add_field(name="Kategorie", value=category.name, inline=False)
            log_embed.timestamp = datetime.now()
            await log_channel.send(embed=log_embed)

        await interaction.followup.send(f"Dein Ticket wurde erstellt: {ticket_channel.mention}", ephemeral=True)

class TicketActionsView(View):
    def __init__(self, bot, support_role_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.support_role_id = support_role_id

    @discord.ui.button(label="Ticket schließen", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Bist du sicher, dass du das Ticket schließen möchtest?", view=ConfirmCloseView(self.bot), ephemeral=True)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="claim_ticket", emoji="🙋")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        support_role = interaction.guild.get_role(self.support_role_id)
        if support_role not in interaction.user.roles:
            await interaction.response.send_message("Nur Mitglieder des Support-Teams können Tickets claimen.", ephemeral=True)
            return

        message = interaction.message
        embed = message.embeds[0]

        new_description = []
        for line in embed.description.split('\n'):
            if line.startswith("**Kümmert sich um dich:**"):
                new_description.append(f"**Kümmert sich um dich:** {interaction.user.mention}")
            else:
                new_description.append(line)

        embed.description = '\n'.join(new_description)

        self.claim_ticket.disabled = True
        self.claim_ticket.style = discord.ButtonStyle.gray

        await message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"{interaction.user.mention} hat das Ticket übernommen.", ephemeral=False)

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🙋 Ticket geclaimed",
                description=f"{interaction.user.mention} kümmert sich nun um das Ticket in {interaction.channel.mention}",
                color=discord.Color.blue()
            )
            log_embed.timestamp = datetime.now()
            await log_channel.send(embed=log_embed)

class ConfirmCloseView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Bestätigen", style=discord.ButtonStyle.red, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: Button):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🔒 Ticket geschlossen",
                description=f"Ticket {interaction.channel.mention} wurde von {interaction.user.mention} geschlossen.",
                color=discord.Color.red()
            )
            log_embed.timestamp = datetime.now()
            await log_channel.send(embed=log_embed)

        await interaction.channel.delete()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Ticket-Schließen abgebrochen.", view=None)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.initialize_ticket_system()

    async def initialize_ticket_system(self):
        ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
        if ticket_channel:
            await ticket_channel.purge(limit=None)

            embed = discord.Embed(
                title="🎫 Ticket-System",
                description="Wählen Sie eine Kategorie aus, um ein Ticket zu erstellen.",
                color=discord.Color.blue()
            )

            await ticket_channel.send(embed=embed, view=TicketView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_tickets(self, ctx):
        """Manuelles Zurücksetzen des Ticket-Systems"""
        await self.initialize_ticket_system()
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Ticket(bot))
