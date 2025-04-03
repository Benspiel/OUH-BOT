import discord
from discord.ext import commands
from discord import ui

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = {}  # Speichert Tickets nur im Speicher

        # Konfiguration
        self.ticket_category_id = 1315353918913515611
        self.staff_role_id = 1297585996464128163
        self.ticket_channel_id = 1345112122442649761
        self.ticket_message_id = None

    async def _update_ticket_message(self, channel):
        """Erstellt oder aktualisiert die Ticket-Nachricht."""
        try:
            await channel.purge()
            embed = discord.Embed(
                title="🏛️ Einbürgerung beantragen",
                description="Klicke auf den Button, um ein privates Ticket zu erstellen.",
                color=discord.Color.green()
            )
            message = await channel.send(embed=embed, view=self.TicketButtonView(self))
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

                # Zuerst das Embed mit den Buttons senden
                await ticket_channel.send(embed=embed, view=view)

                # Danach den langen Text senden
                long_text = """
Hallo,
Bitte les dir die Regeln durch und akzeptiere sie,
Wer nicht mithilft, bzw. gegen Oberüberhausen arbeitet wird ausgeschlossen.

Ohne Discord, gibt es keine Teilnahme am Geschehen.

Wer sich nicht für alle mit verpflichtet und Aufgaben übernimmt muss auf Dauer gehen.

Auf dem Discord ist kein Platz für Hass und Rassismus und wird mit einem permanenten Bann und Ausschluss geandet.

Bitte Schreibe deinen Minecraftnamen in das Ticket damit wir wissen wie du ingame heißt.

Wer Fragen oder Probleme hat, oder sich Einbürgern möchte, kann sich in den entsprechenden Kanälen an den Support wenden (⁠ ⁠support-bewerbungen ⁠einbürgerungen)

Schreibe bitte noch dein Alter in das Ticket.

Wenn du die Regeln gelesen hast antworte mit „Chicken" um diese zu akzeptieren.

-- Wenn du nicht innerhalb 48 Stunden Antwortest wird das Ticket geschlossen -

Der Oberattack Minecraft server wurde geschlossen, es gibt zurzeit keine Möglichkeit darauf zu spielen!
Unser Discord wird dadurch aber in keiner weise eingeschränkt
                """
                await ticket_channel.send(long_text)

                self.cog.tickets[ticket_channel.id] = {
                    "user_id": interaction.user.id,
                    "channel_id": ticket_channel.id
                }

                await interaction.response.send_message(
                    f"✅ Ticket erstellt: {ticket_channel.mention}", ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(f"❌ Fehler: {str(e)}", ephemeral=True)

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
            embed = interaction.message.embeds[0]
            embed.add_field(name="Kümmert sich um dich:", value=interaction.user.mention, inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

        @ui.button(label="Ticket schließen", style=discord.ButtonStyle.red, custom_id="close_ticket")
        async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
            await interaction.channel.delete()
            self.cog.tickets.pop(interaction.channel.id, None)

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.ticket_channel_id)
        if channel:
            await self._update_ticket_message(channel)
        print("✅ Ticket-System erfolgreich gestartet!")

async def setup(bot):
    cog = TicketSystem(bot)
    await bot.add_cog(cog)
    bot.add_view(cog.TicketButtonView(cog))
    bot.add_view(cog.TicketManagementView(cog))
