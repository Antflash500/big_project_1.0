import discord
from discord.ext import commands
from discord import app_commands
import time
from datetime import datetime

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="ping", description="Cek latency bot")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** `{latency}ms`",
            color=self.bot.color
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Info server")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        
        # Hitung berbagai stats
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        total_members = guild.member_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)
        boosts = guild.premium_subscription_count
        
        # Buat embed
        embed = discord.Embed(
            title=f"📊 Server Info: {guild.name}",
            color=self.bot.color,
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        embed.add_field(name="👥 Members", value=f"Total: `{total_members}`\nOnline: `{online}`", inline=True)
        embed.add_field(name="📁 Channels", value=f"Text: `{text_channels}`\nVoice: `{voice_channels}`", inline=True)
        embed.add_field(name="✨ Boosts", value=f"Level: `{guild.premium_tier}`\nBoosts: `{boosts}`", inline=True)
        
        embed.add_field(name="📜 Roles", value=f"`{roles}` roles", inline=True)
        embed.add_field(name="🔐 Verification", value=f"`{str(guild.verification_level).title()}`", inline=True)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Show all commands")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🌟 Star Family Bot - Help Menu",
            description="Prefix: `!`\nUse `!help <category>` for more info",
            color=self.bot.color
        )
        
        # Categories
        categories = {
            "📚 Basic": "`ping`, `serverinfo`, `help`",
            "⚙️ Moderation": "`kick`, `ban`, `timeout`",
            "📈 Leveling": "`level`, `leaderboard`",
            "🛡️ Filter": "`addfilter`, `listfilter`",
            "📨 Confession": "`confess`",
            "🎭 Custom": "`addcmd`, `delcmd`"
        }
        
        for category, commands in categories.items():
            embed.add_field(name=category, value=commands, inline=False)
        
        embed.add_field(
            name="ℹ️ Note", 
            value="🔸 Use slash commands for easier access!\n🔸 Admin commands require permissions.",
            inline=False
        )
        
        embed.set_footer(text="Bot made with ❤️ for Star Family")
        
        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        current_time = time.time()
        uptime_seconds = int(current_time - self.start_time)
        
        # Konversi ke hari, jam, menit
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            description=f"**{days}d {hours}h {minutes}m {seconds}s**",
            color=self.bot.color
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Basic(bot))