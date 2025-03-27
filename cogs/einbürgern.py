import discord
import sqlite3
import os
from discord.ext import commands
from discord import ui
from datetime import datetime

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(os.path.dirname(__file__), 'ticket.db')
        self._initialize_db()

        # Konfiguration
        self.ticket_category_id = 1315353918913515611
        self.staff_role_id = 1297585996464128163
        self.ticket_channel_id = 1345112122442649761
        self.ticket_message_id = None

    def _initialize_db(self):
        """Datenbank initialisieren"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS einbuergerung
                            (channel_id INTEGER PRIMARY KEY,
                             user_id INTEGER NOT NULL,
                             staff_id INTEGER,
                             status TEXT NOT NULL,
                             created_at TEXT NOT NULL)''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Datenbankfehler: {e}")
            raise

    async def _update_ticket_message(self, channel):
        """Aktualisiert die Ticket-Nachricht im Ziel-Channel"""
        try:
            await channel.purge()
            embed = discord.Embed(
                title="🏛️ Einbürgerung beantragen",
                description="Klicke auf den Button, um ein privates Ticket zu erstellen.",
                color=discord.Color.green()
            )
            message = await channel.send(
                embed=embed,
                view=self.TicketButtonView(self)
            )
            self.ticket_message_id = message.id
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Ticket-Nachricht: {e}")

    class TicketButtonView(ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)
            self.cog = cog

        @ui.button(label="Einbürgern", style=discord.ButtonStyle.green, custom_id="ticket_button")
        async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
            try:
                category = interaction.guild.get_channel(self.cog.ticket_category_id)
                if not category:
                    await interaction.response.send_message("❌ Ticket-Kategorie nicht gefunden!", ephemeral=True)
                    return

                ticket_channel = await interaction.guild.create_text_channel(
                    name=f"einbürgerung-{interaction.user.display_name}",
                    category=category,
                    overwrites={
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True),
                        interaction.guild.get_role(self.cog.staff_role_id): discord.PermissionOverwrite(read_messages=True)
                    }
                )

                embed = discord.Embed(
                    title="🏛️ Einbürgerungsantrag",
                    description=f"{interaction.user.mention} möchte sich einbürgern\n**Grund:** Staatsbürgerschaft",
                    color=discord.Color.blue()
                )

                view = self.cog.TicketManagementView(self.cog)
                await ticket_channel.send(embed=embed, view=view)

                await interaction.response.send_message(
                    f"✅ Ticket erstellt: {ticket_channel.mention}",
                    ephemeral=True
                )

            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Fehler beim Erstellen des Tickets: {str(e)}",
                    ephemeral=True
                )

    class TicketManagementView(ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)
            self.cog = cog
            self.claimed = False

        @ui.button(label="Claim Ticket", style=discord.ButtonStyle.blurple, custom_id="claim_ticket")
        async def claim_ticket(self, interaction: discord.Interaction, button: ui.Button):
            if self.claimed:
                await interaction.response.defer()
                return

            staff_role = interaction.guild.get_role(self.cog.staff_role_id)
            if not staff_role or staff_role not in interaction.user.roles:
                await interaction.response.send_message("❌ Nur Moderatoren können Tickets claimen!", ephemeral=True)
                return

            self.claimed = True
            button.disabled = True

            message = interaction.message
            embed = message.embeds[0]
            embed.add_field(
                name="Kümmert sich um dich:",
                value=interaction.user.mention,
                inline=False
            )

            await interaction.response.edit_message(embed=embed, view=self)

        @ui.button(label="Ticket schließen", style=discord.ButtonStyle.red, custom_id="close_ticket")
        async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
            confirm_embed = discord.Embed(
                title="⚠️ Ticket wirklich schließen?",
                description="Dies löscht den Channel permanent!",
                color=discord.Color.red()
            )

            confirm_view = ui.View()
            confirm_view.add_item(ui.Button(
                style=discord.ButtonStyle.green,
                label="Bestätigen",
                custom_id="confirm_close"
            ))
            confirm_view.add_item(ui.Button(
                style=discord.ButtonStyle.grey,
                label="Abbrechen",
                custom_id="cancel_close"
            ))

            await interaction.response.edit_message(
                embed=confirm_embed,
                view=confirm_view
            )

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'ticket_setup_done'):
            try:
                channel = self.bot.get_channel(self.ticket_channel_id)
                if channel:
                    await self._update_ticket_message(channel)
                    self.bot.ticket_setup_done = True
                    print("✅ Ticket-System erfolgreich gestartet!")
            except Exception as e:
                print(f"❌ Fehler beim Ticket-Setup: {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            custom_id = interaction.data.get("custom_id")

            if custom_id == "confirm_close":
                await interaction.channel.delete()

            elif custom_id == "cancel_close":
                original_embed = discord.Embed(
                    title="🏛️ Einbürgerungsantrag",
                    description=f"{interaction.user.mention}'s Ticket",
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(
                    embed=original_embed,
                    view=self.TicketManagementView(self)
                )

        except Exception as e:
            print(f"Fehler bei Button-Interaktion: {e}")

async def setup(bot):
    try:
        cog = TicketSystem(bot)
        await bot.add_cog(cog)
        bot.add_view(cog.TicketButtonView(cog))
        bot.add_view(cog.TicketManagementView(cog))
    except Exception as e:
        print(f"Fehler beim Laden des Ticket-Cogs: {e}")
        raise