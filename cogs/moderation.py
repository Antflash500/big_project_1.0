import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_cache = {}  # {user_id: [messages, timestamp]}

    @commands.hybrid_command(name="kick", description="Kick a member")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if ctx.author.top_role <= member.top_role:
            await ctx.send("❌ You cannot kick someone with equal or higher role!")
            return
        
        await member.kick(reason=reason)
        
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"**{member}** has been kicked from the server.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        
        # Try to DM the kicked user
        try:
            dm_embed = discord.Embed(
                title="👢 You have been kicked",
                description=f"From: **{ctx.guild.name}**",
                color=discord.Color.orange()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            await member.send(embed=dm_embed)
        except:
            pass

    @commands.hybrid_command(name="ban", description="Ban a member")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if ctx.author.top_role <= member.top_role:
            await ctx.send("❌ You cannot ban someone with equal or higher role!")
            return
        
        await member.ban(reason=reason, delete_message_days=0)
        
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**{member}** has been banned from the server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="timeout", description="Timeout a member (in minutes)")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
        if minutes <= 0 or minutes > 40320:  # Max 28 days in minutes
            await ctx.send("❌ Please provide minutes between 1 and 40320 (28 days)")
            return
        
        if ctx.author.top_role <= member.top_role:
            await ctx.send("❌ You cannot timeout someone with equal or higher role!")
            return
        
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        
        embed = discord.Embed(
            title="⏰ Member Timed Out",
            description=f"**{member}** has been timed out for **{minutes} minutes**.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="untimeout", description="Remove timeout from member")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        if not member.is_timed_out():
            await ctx.send("❌ This member is not timed out!")
            return
        
        await member.timeout(None)
        await ctx.send(f"✅ Timeout removed from {member.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Anti-spam system
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        current_time = message.created_at.timestamp()
        
        if user_id not in self.spam_cache:
            self.spam_cache[user_id] = []
        
        # Simpan pesan (max 5 pesan terakhir)
        self.spam_cache[user_id].append((message.content, current_time))
        if len(self.spam_cache[user_id]) > 5:
            self.spam_cache[user_id].pop(0)
        
        # Cek spam: 5 pesan sama dalam 10 detik
        if len(self.spam_cache[user_id]) >= 5:
            messages = [msg[0] for msg in self.spam_cache[user_id]]
            times = [msg[1] for msg in self.spam_cache[user_id]]
            
            # Cek jika semua pesan sama
            if all(msg == messages[0] for msg in messages):
                time_diff = times[-1] - times[0]
                if time_diff < 10:  # 5 pesan berulang dalam 10 detik
                    # Timeout user
                    try:
                        duration = timedelta(minutes=5)
                        await message.author.timeout(duration, reason="Anti-spam: 5 repeated messages")
                        
                        # Hapus pesan spam
                        await message.delete()
                        
                        # Kirim warning
                        warning = await message.channel.send(
                            f"⚠️ {message.author.mention} has been timed out for 5 minutes due to spam!"
                        )
                        await asyncio.sleep(5)
                        await warning.delete()
                        
                        # Reset cache untuk user ini
                        self.spam_cache[user_id] = []
                    except:
                        pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))