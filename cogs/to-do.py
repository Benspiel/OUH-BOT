import discord
from discord.ext import commands
from discord import app_commands

class TodoModal(discord.ui.Modal, title="Neue To-Do Aufgabe"):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    title_input = discord.ui.TextInput(
        label="Titel der Aufgabe",
        placeholder="Was soll getan werden?",
        max_length=100,
    )

    description_input = discord.ui.TextInput(
        label="Beschreibung",
        style=discord.TextStyle.paragraph,
        placeholder="Details zur Aufgabe...",
        required=False,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=discord.Color.light_grey(),  # Standard: grau
        )
        embed.set_footer(text="Status: Offen")

        msg = await self.channel.send(embed=embed)

        # Emojis hinzufügen
        await msg.add_reaction("⏰")  # Bearbeitung
        await msg.add_reaction("✅")  # Fertig
        await msg.add_reaction("❌")  # Abgelehnt

        await interaction.response.send_message("To-Do wurde erstellt!", ephemeral=True)


class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="to-do", description="Erstelle eine neue To-Do Aufgabe")
    async def todo(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(1358379269016780890)
        if channel is None:
            await interaction.response.send_message("Konnte den To-Do Channel nicht finden.", ephemeral=True)
            return

        await interaction.response.send_modal(TodoModal(channel))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if not message.embeds:
            return

        embed = message.embeds[0]
        updated_embed = discord.Embed(
            title=embed.title,
            description=embed.description
        )

        emoji = str(payload.emoji)
        if emoji == "⏰":
            updated_embed.color = discord.Color.gold()
            updated_embed.set_footer(text="Status: In Bearbeitung")
        elif emoji == "✅":
            updated_embed.color = discord.Color.green()
            updated_embed.set_footer(text="Status: Erledigt")
        elif emoji == "❌":
            updated_embed.color = discord.Color.red()
            updated_embed.set_footer(text="Status: Abgelehnt")
        else:
            return  # Ignoriere andere Reaktionen

        await message.edit(embed=updated_embed)


async def setup(bot):
    await bot.add_cog(Todo(bot))
