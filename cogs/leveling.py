import discord
from discord.ext import commands
import random
from datetime import datetime
from utils.database import execute_query

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = {}  # {(user_id, guild_id): last_message_time}
        self.xp_range = (10, 20)
        
    def calculate_level(self, xp):
        return max(1, xp // 1000 + 1)
    
    def calculate_xp_for_level(self, level):
        return (level - 1) * 1000
    
    async def get_user_data(self, user_id, guild_id):
        result = execute_query(
            "SELECT xp, level, messages FROM users WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id)),
            fetch=True
        )
        
        if result:
            xp, level, messages = result
            return {"xp": xp, "level": level, "messages": messages}
        else:
            # 🔥 PERBAIKAN: Insert dengan kedua primary key
            execute_query(
                "INSERT INTO users (user_id, guild_id, xp, level, messages) VALUES (?, ?, 0, 1, 0)",
                (str(user_id), str(guild_id))
            )
            return {"xp": 0, "level": 1, "messages": 0}
    
    async def add_xp(self, user_id, guild_id, xp_to_add):
        user_data = await self.get_user_data(user_id, guild_id)
        new_xp = user_data["xp"] + xp_to_add
        new_level = self.calculate_level(new_xp)
        
        # 🔥 PERBAIKAN: Update dengan kedua primary key
        execute_query(
            """UPDATE users 
               SET xp = ?, level = ?, messages = messages + 1 
               WHERE user_id = ? AND guild_id = ?""",
            (new_xp, new_level, str(user_id), str(guild_id))
        )
        
        if new_level > user_data["level"]:
            return True, new_level, new_xp
        return False, new_level, new_xp
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.bot or not message.guild or 
            message.content.startswith(tuple([self.bot.command_prefix, '/']))):
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Cooldown key dengan guild_id
        cooldown_key = (user_id, guild_id)
        current_time = datetime.now().timestamp()
        
        if cooldown_key in self.xp_cooldown:
            if current_time - self.xp_cooldown[cooldown_key] < 60:
                return
        
        self.xp_cooldown[cooldown_key] = current_time
        
        xp_gain = random.randint(*self.xp_range)
        leveled_up, new_level, new_xp = await self.add_xp(user_id, guild_id, xp_gain)
        
        if leveled_up:
            await self.handle_level_up(message.author, guild_id, new_level, message.channel)
    
    async def handle_level_up(self, member, guild_id, new_level, channel):
        result = execute_query(
            "SELECT role_id FROM level_roles WHERE guild_id = ? AND level = ?",
            (str(guild_id), new_level),
            fetch=True
        )
        
        if result:
            role_id = int(result[0])
            role = member.guild.get_role(role_id)
            
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                    
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"{member.mention} has reached **Level {new_level}**!",
                        color=self.bot.color
                    )
                    embed.add_field(name="🎁 Reward", value=f"Role {role.mention} has been given!", inline=False)
                    
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass
        else:
            # Simple notification without role
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{member.mention} has reached **Level {new_level}**!",
                color=self.bot.color
            )
            await channel.send(embed=embed, delete_after=10)
    
    @commands.hybrid_command(name="level", description="Check your level or someone else's")
    async def level(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_data = await self.get_user_data(target.id, ctx.guild.id)
        
        xp = user_data["xp"]
        level = user_data["level"]
        messages = user_data["messages"]
        
        current_level_xp = self.calculate_xp_for_level(level)
        next_level_xp = self.calculate_xp_for_level(level + 1)
        xp_needed = next_level_xp - xp
        progress = xp - current_level_xp
        total_needed = next_level_xp - current_level_xp
        
        # Progress bar
        bar_length = 10
        filled = int((progress / total_needed) * bar_length) if total_needed > 0 else bar_length
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        
        embed = discord.Embed(
            title=f"📊 Level Stats - {target.display_name}",
            color=self.bot.color
        )
        
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp:,}** / {next_level_xp:,}", inline=True)
        embed.add_field(name="Messages", value=f"**{messages}**", inline=True)
        embed.add_field(name="Progress", value=f"{progress_bar} **{progress}/{total_needed}** XP", inline=False)
        embed.add_field(name="XP Needed", value=f"**{xp_needed:,}** XP to next level", inline=False)
        
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        embed.set_footer(text=f"User ID: {target.id}")
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard", description="Show server level leaderboard")
    async def leaderboard(self, ctx):
        results = execute_query(
            """SELECT user_id, xp, level, messages 
               FROM users 
               WHERE guild_id = ? 
               ORDER BY xp DESC 
               LIMIT 10""",
            (str(ctx.guild.id),),
            fetchall=True
        )
        
        if not results:
            await ctx.send("📭 No level data available yet!")
            return
        
        embed = discord.Embed(
            title="🏆 Level Leaderboard",
            description=f"Top {len(results)} members in {ctx.guild.name}",
            color=self.bot.color
        )
        
        leaderboard_text = ""
        for i, (user_id, xp, level, messages) in enumerate(results, 1):
            member = ctx.guild.get_member(int(user_id))
            name = member.mention if member else f"User ({user_id})"
            
            medal = ""
            if i == 1: medal = "🥇 "
            elif i == 2: medal = "🥈 "
            elif i == 3: medal = "🥉 "
            
            leaderboard_text += f"**{medal}{i}. {name}**\n"
            leaderboard_text += f"   Level: `{level}` | XP: `{xp:,}` | Messages: `{messages}`\n\n"
        
        embed.description = leaderboard_text
        
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="setlevelrole", description="Set a role for specific level (Admin only)")
    @commands.has_permissions(administrator=True)
    async def set_level_role(self, ctx, level: int, role: discord.Role):
        if level < 1:
            await ctx.send("❌ Level must be at least 1!")
            return
        
        execute_query(
            """INSERT OR REPLACE INTO level_roles (guild_id, level, role_id) 
               VALUES (?, ?, ?)""",
            (str(ctx.guild.id), level, str(role.id))
        )
        
        embed = discord.Embed(
            title="✅ Level Role Set",
            description=f"Role {role.mention} will be given at **Level {level}**",
            color=self.bot.color
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="levelroles", description="Show all configured level roles")
    async def show_level_roles(self, ctx):
        results = execute_query(
            "SELECT level, role_id FROM level_roles WHERE guild_id = ? ORDER BY level",
            (str(ctx.guild.id),),
            fetchall=True
        )
        
        if not results:
            await ctx.send("📭 No level roles configured yet!")
            return
        
        embed = discord.Embed(
            title="🎭 Level Roles Configuration",
            color=self.bot.color
        )
        
        roles_list = ""
        for level, role_id in results:
            role = ctx.guild.get_role(int(role_id))
            role_name = role.mention if role else f"Role not found ({role_id})"
            roles_list += f"**Level {level}** → {role_name}\n"
        
        embed.description = roles_list
        embed.set_footer(text=f"Use {ctx.prefix}setlevelrole <level> <role> to add more")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))