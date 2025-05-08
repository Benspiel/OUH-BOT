import discord
from discord.ext import commands
from discord import ui
import time
import random

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = {}  # ticket_channel_id: {user_id, channel_id, codeword}
        self.cooldowns = {}
        self.codewords = ["Mango", "Laser", "Papierflieger", "Ananas", "Roboter", "Zebra", "Pixel", "Kaktus", "Vulkan", "Bücherwurm"]

        self.ticket_category_id = 1315353918913515611
        self.staff_role_id = 1315043449606635621
        self.ticket_channel_id = 1345112122442649761
        self.ticket_message_id = None

    async def _update_ticket_message(self, channel):
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
            user_id = interaction.user.id
            now = time.time()

            # Cooldown Check
            if user_id in self.cog.cooldowns:
                last_time = self.cog.cooldowns[user_id]
                if now - last_time < 600:
                    minutes = int((600 - (now - last_time)) / 60)
                    await interaction.response.send_message(
                        f"⏳ Bitte warte {minutes} Minuten, bevor du ein neues Ticket erstellst.", ephemeral=True
                    )
                    return

            # Duplikatprüfung anhand user_id in self.tickets
            for t_id, t_data in self.cog.tickets.items():
                if t_data["user_id"] == user_id:
                    existing_channel = interaction.guild.get_channel(t_id)
                    if existing_channel:
                        await interaction.response.send_message(
                            f"❗ Du hast bereits ein offenes Ticket: {existing_channel.mention}", ephemeral=True
                        )
                        return

            try:
                category = interaction.guild.get_channel(self.cog.ticket_category_id)
                if not category:
                    await interaction.response.send_message("❌ Ticket-Kategorie nicht gefunden!", ephemeral=True)
                    return

                chosen_word = random.choice(self.cog.codewords)

                ticket_channel = await interaction.guild.create_text_channel(
                    name=f"einbürgerung-{interaction.user.display_name}",
                    topic=f"user_id:{user_id}",
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

                rules_text = f"""
Hallo,
Bitte les dir die Regeln durch und akzeptiere sie,
Wer nicht mithilft, bzw. gegen Oberüberhausen arbeitet wird ausgeschlossen.

Ohne Discord, gibt es keine Teilnahme am Geschehen.

Wer sich nicht für alle mit verpflichtet und Aufgaben übernimmt muss auf Dauer gehen.

Auf dem Discord ist kein Platz für Hass und Rassismus und wird mit einem permanenten Bann und Ausschluss geandet.

Bitte schreibe deinen Minecraftnamen in das Ticket, damit wir wissen, wie du ingame heißt.

Wer Fragen oder Probleme hat, oder sich einbürgern möchte, kann sich in den entsprechenden Kanälen an den Support wenden (⁠ ⁠support-bewerbungen ⁠einbürgerungen)

Schreibe bitte noch dein Alter in das Ticket.

Wenn du die Regeln gelesen hast, antworte mit „{chosen_word}“ um diese zu akzeptieren.

-- Wenn du nicht innerhalb 48 Stunden antwortest, wird das Ticket geschlossen -

Der Oberattack Minecraft Server wurde geschlossen, es gibt zurzeit keine Möglichkeit darauf zu spielen!
Unser Discord wird dadurch aber in keiner Weise eingeschränkt.
"""
                await ticket_channel.send(rules_text)

                self.cog.tickets[ticket_channel.id] = {
                    "user_id": user_id,
                    "channel_id": ticket_channel.id,
                    "codeword": chosen_word
                }

                self.cog.cooldowns[user_id] = now

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

        # Bestehende Tickets laden (user_id aus topic lesen)
        guild = self.bot.get_guild(channel.guild.id)
        for ch in guild.text_channels:
            if ch.name.startswith("einbürgerung-") and ch.topic and "user_id:" in ch.topic:
                try:
                    uid = int(ch.topic.split("user_id:")[1])
                    self.tickets[ch.id] = {
                        "user_id": uid,
                        "channel_id": ch.id,
                        "codeword": None
                    }
                except ValueError:
                    pass

        print("✅ Ticket-System erfolgreich gestartet!")

async def setup(bot):
    cog = TicketSystem(bot)
    await bot.add_cog(cog)
    bot.add_view(cog.TicketButtonView(cog))
    bot.add_view(cog.TicketManagementView(cog))
