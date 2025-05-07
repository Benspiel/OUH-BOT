import discord
from discord.ext import commands
from discord import ui
import random
import asyncio

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = {}  # Speichert Tickets nur im Speicher
        
        # Liste der möglichen Bestätigungswörter
        self.confirmation_words = ["Chicken", "Kartoffel", "Ananas", "Diamant", "Obsidian", 
                                  "Banane", "Kokosnuss", "Erdbeere", "Minecraft", "Oberüberhausen"]

        # Speichert das ausgewählte Wort für jedes Ticket
        self.ticket_keywords = {}

        # Konfiguration
        self.ticket_category_id = 1315353918913515611
        self.staff_role_id = 1315043449606635621
        self.ticket_channel_id = 1345112122442649761
        self.citizen_role_id = 1249370512040136734  # Rolle für genehmigte Einbürgerungen
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

                # Zufälliges Bestätigungswort auswählen
                selected_word = random.choice(self.cog.confirmation_words)
                self.cog.ticket_keywords[ticket_channel.id] = selected_word

                embed = discord.Embed(
                    title="🏛️ Einbürgerungsantrag",
                    description=f"{interaction.user.mention} möchte sich einbürgern\n**Grund:** Staatsbürgerschaft",
                    color=discord.Color.blue()
                )
                view = self.cog.TicketManagementView(self.cog)

                # Zuerst das Embed mit den Buttons senden
                await ticket_channel.send(embed=embed, view=view)

                # Danach den langen Text mit dem angepassten Bestätigungswort senden
                long_text = f"""
Hallo,
Bitte les dir die Regeln durch und akzeptiere sie,
Wer nicht mithilft, bzw. gegen Oberüberhausen arbeitet wird ausgeschlossen.

Ohne Discord, gibt es keine Teilnahme am Geschehen.

Wer sich nicht für alle mit verpflichtet und Aufgaben übernimmt muss auf Dauer gehen.

Auf dem Discord ist kein Platz für Hass und Rassismus und wird mit einem permanenten Bann und Ausschluss geandet.

Bitte Schreibe deinen Minecraftnamen in das Ticket damit wir wissen wie du ingame heißt.

Wer Fragen oder Probleme hat, oder sich Einbürgern möchte, kann sich in den entsprechenden Kanälen an den Support wenden (⁠ ⁠support-bewerbungen ⁠einbürgerungen)

Schreibe bitte noch dein Alter in das Ticket.

Wenn du die Regeln gelesen hast antworte mit „{selected_word}" um diese zu akzeptieren.

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
            # Überprüfen, ob der Nutzer die Berechtigung hat (Staff-Rolle)
            staff_role = interaction.guild.get_role(self.cog.staff_role_id)
            if staff_role not in interaction.user.roles:
                await interaction.response.send_message("❌ Nur Staff-Mitglieder können Tickets schließen!", ephemeral=True)
                return
            
            # Das ursprüngliche Ticket und den Ticketersteller finden
            ticket_info = self.cog.tickets.get(interaction.channel.id)
            if not ticket_info:
                await interaction.response.send_message("❌ Fehler: Ticket-Informationen nicht gefunden.", ephemeral=True)
                return
                
            ticket_creator_id = ticket_info["user_id"]
            ticket_creator = interaction.guild.get_member(ticket_creator_id)
            
            # Genehmigungsabfrage senden - öffentlich im Channel
            confirm_view = self.cog.TicketCloseConfirmView(self.cog, ticket_creator)
            await interaction.response.send_message(
                f"Möchtest du die Einbürgerung genehmigen oder ablehnen für {ticket_creator.mention}?", 
                view=confirm_view,
                ephemeral=False  # Sichtbar für alle im Channel
            )

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.ticket_channel_id)
        if channel:
            await self._update_ticket_message(channel)
        print("✅ Ticket-System erfolgreich gestartet!")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Überprüfen ob die Nachricht in einem Ticket-Channel ist
        if message.channel.id in self.ticket_keywords:
            # Nachricht vom Bot ignorieren
            if message.author.bot:
                return
                
            expected_word = self.ticket_keywords[message.channel.id]
            
            # Überprüfen, ob das erwartete Wort in der Nachricht ist
            if expected_word.lower() in message.content.lower():
                # Bestätigung senden
                await message.channel.send(f"✅ Danke, {message.author.mention}! Du hast die Regeln akzeptiert. Ein Teammitglied wird sich um deine Einbürgerung kümmern.")
                
                # Optional: Den Keyword-Check für dieses Ticket deaktivieren
                del self.ticket_keywords[message.channel.id]

    class TicketCloseConfirmView(ui.View):
        """View mit Bestätigungsbuttons zum Schließen eines Tickets"""
        def __init__(self, cog, ticket_creator):
            super().__init__(timeout=60)  # Timeout nach 60 Sekunden
            self.cog = cog
            self.ticket_creator = ticket_creator

        @ui.button(label="Genehmigen", style=discord.ButtonStyle.green, emoji="✅")
        async def approve_ticket(self, interaction: discord.Interaction, button: ui.Button):
            channel_id = interaction.channel.id
            
            try:
                # Bürgerrolle vergeben
                citizen_role = interaction.guild.get_role(self.cog.citizen_role_id)
                if citizen_role:
                    await self.ticket_creator.add_roles(citizen_role, reason="Einbürgerung genehmigt")
                    
                    # DM an den Benutzer senden
                    try:
                        await self.ticket_creator.send(f"🎉 Deine Einbürgerung in {interaction.guild.name} wurde genehmigt! Du hast nun Zugriff auf alle Bürger-Bereiche.")
                    except discord.Forbidden:
                        pass  # DM konnte nicht gesendet werden
                
                # Aufräumen
                if channel_id in self.cog.ticket_keywords:
                    del self.cog.ticket_keywords[channel_id]
                
                self.cog.tickets.pop(channel_id, None)
                
                # Bestätigung und Channel löschen
                await interaction.response.send_message("✅ Einbürgerung genehmigt! Der Channel wird gelöscht.", ephemeral=True)
                await asyncio.sleep(3)  # Kurze Verzögerung
                await interaction.channel.delete()
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Fehler: {str(e)}", ephemeral=True)

        @ui.button(label="Ablehnen", style=discord.ButtonStyle.red, emoji="❌")
        async def reject_ticket(self, interaction: discord.Interaction, button: ui.Button):
            channel_id = interaction.channel.id
            
            try:
                # Benutzer kicken
                try:
                    await self.ticket_creator.send(f"❌ Deine Einbürgerung in {interaction.guild.name} wurde abgelehnt und du wurdest vom Server entfernt.")
                except discord.Forbidden:
                    pass  # DM konnte nicht gesendet werden
                
                await interaction.guild.kick(self.ticket_creator, reason="Einbürgerung abgelehnt")
                
                # Aufräumen
                if channel_id in self.cog.ticket_keywords:
                    del self.cog.ticket_keywords[channel_id]
                
                self.cog.tickets.pop(channel_id, None)
                
                # Bestätigung und Channel löschen
                await interaction.response.send_message("❌ Einbürgerung abgelehnt! Der Benutzer wurde gekickt und der Channel wird gelöscht.", ephemeral=True)
                await asyncio.sleep(3)  # Kurze Verzögerung
                await interaction.channel.delete()
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Fehler: {str(e)}", ephemeral=True)

async def setup(bot):
    cog = TicketSystem(bot)
    await bot.add_cog(cog)
    bot.add_view(cog.TicketButtonView(cog))
    bot.add_view(cog.TicketManagementView(cog))
