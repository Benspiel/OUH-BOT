import discord
from discord.ext import commands

class LogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild):
        # Hole den Kanal mit der ID 1353810348477517884
        return guild.get_channel(1353810348477517884)

    # Nachricht erstellt
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        embed = discord.Embed(title="Nachricht erstellt", color=discord.Color.blue())
        embed.add_field(name="Autor", value=message.author.mention, inline=False)
        embed.add_field(name="Inhalt", value=message.content or "(Kein Inhalt)", inline=False)
        embed.add_field(name="Kanal", value=f"<#{message.channel.id}>", inline=False)  # Klickbarer Link
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        log_channel = await self.get_log_channel(message.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Nachricht bearbeitet
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            embed = discord.Embed(title="Nachricht bearbeitet", color=discord.Color.blue())
            embed.add_field(name="Autor", value=before.author.mention, inline=False)
            embed.add_field(name="Kanal", value=f"<#{before.channel.id}>", inline=False)  # Klickbar
            embed.add_field(name="Vorher", value=before.content or "(Kein Inhalt)", inline=False)
            embed.add_field(name="Nachher", value=after.content or "(Kein Inhalt)", inline=False)
            embed.set_author(name=before.author.name, icon_url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
            log_channel = await self.get_log_channel(before.guild)
            if log_channel:
                await log_channel.send(embed=embed)

    # Nachricht gelöscht
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        embed = discord.Embed(title="Nachricht gelöscht", color=discord.Color.blue())
        embed.add_field(name="Autor", value=message.author.mention, inline=False)
        embed.add_field(name="Inhalt", value=message.content or "(Kein Inhalt)", inline=False)
        embed.add_field(name="Kanal", value=f"<#{message.channel.id}>", inline=False)  # Klickbar
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        log_channel = await self.get_log_channel(message.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Mitglied tritt bei
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="Mitglied beigetreten", color=discord.Color.blue())
        embed.add_field(name="Benutzer", value=member.mention, inline=False)
        embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        log_channel = await self.get_log_channel(member.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Mitglied verlässt den Server
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Mitglied verlassen", color=discord.Color.blue())
        embed.add_field(name="Benutzer", value=member.mention, inline=False)
        embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        log_channel = await self.get_log_channel(member.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Mitglied gekickt
    @commands.Cog.listener()
    async def on_member_kick(self, member):
        embed = discord.Embed(title="Mitglied gekickt", color=discord.Color.red())
        embed.add_field(name="Benutzer", value=member.mention, inline=False)
        embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        log_channel = await self.get_log_channel(member.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Mitglied gebannt
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(title="Mitglied gebannt", color=discord.Color.red())
        embed.add_field(name="Benutzer", value=user.mention, inline=False)
        embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
        log_channel = await self.get_log_channel(guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Voice-Channel betritt/verlassen
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            embed = discord.Embed(title="Voice-Channel Beitritt/Verlassen", color=discord.Color.orange())
            embed.add_field(name="Benutzer", value=member.mention, inline=False)
            if after.channel:
                embed.add_field(name="Beigetreten", value=after.channel.name, inline=False)
            if before.channel:
                embed.add_field(name="Verlassen", value=before.channel.name, inline=False)
            embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
            log_channel = await self.get_log_channel(member.guild)
            if log_channel:
                await log_channel.send(embed=embed)

    # Reaktion hinzugefügt
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        embed = discord.Embed(title="Reaktion hinzugefügt", color=discord.Color.blue())
        embed.add_field(name="Benutzer", value=user.mention, inline=False)
        embed.add_field(name="Reaktion", value=str(reaction.emoji), inline=False)
        embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
        log_channel = await self.get_log_channel(reaction.message.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Reaktion entfernt
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        embed = discord.Embed(title="Reaktion entfernt", color=discord.Color.blue())
        embed.add_field(name="Benutzer", value=user.mention, inline=False)
        embed.add_field(name="Reaktion", value=str(reaction.emoji), inline=False)
        embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
        log_channel = await self.get_log_channel(reaction.message.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Rolle zugewiesen
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            embed = discord.Embed(title="Rolle geändert", color=discord.Color.orange())
            embed.add_field(name="Benutzer", value=after.mention, inline=False)
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            if added_roles:
                embed.add_field(name="Hinzufügte Rollen", value=", ".join([role.name for role in added_roles]), inline=False)
            if removed_roles:
                embed.add_field(name="Entfernte Rollen", value=", ".join([role.name for role in removed_roles]), inline=False)
            embed.set_author(name=after.name, icon_url=after.avatar.url if after.avatar else after.default_avatar.url)
            log_channel = await self.get_log_channel(after.guild)
            if log_channel:
                await log_channel.send(embed=embed)

    # Channel erstellt
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="Channel erstellt", color=discord.Color.blue())
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Typ", value=channel.type, inline=False)
        log_channel = await self.get_log_channel(channel.guild)
        if log_channel:
            await log_channel.send(embed=embed)

    # Channel gelöscht
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="Channel gelöscht", color=discord.Color.blue())
        embed.add_field(name="Channel", value=channel.name, inline=False)
        embed.add_field(name="Typ", value=channel.type, inline=False)
        log_channel = await self.get_log_channel(channel.guild)
        if log_channel:
            await log_channel.send(embed=embed)

# LogCog in den Bot laden
async def setup(bot):
    await bot.add_cog(LogCog(bot))
