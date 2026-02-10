import discord
from discord.ext import commands, tasks
from utils.database import execute_query
import asyncio
import json
from datetime import datetime, time
import re

class CustomCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands_cache = {}
        self.scheduled_messages = []
        
        # Create table if not exists
        self.create_scheduled_table()
        
        # Start scheduler
        self.scheduler.start()
    
    def create_scheduled_table(self):
        """Create scheduled messages table if not exists"""
        execute_query('''
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            schedule_id TEXT PRIMARY KEY,
            guild_id TEXT,
            channel_id TEXT,
            hour INTEGER,
            minute INTEGER,
            message TEXT,
            enabled INTEGER DEFAULT 1
        )
        ''')
    
    async def load_custom_commands(self, guild_id):
        """Load custom commands from database"""
        results = execute_query(
            "SELECT cmd_name, response FROM custom_commands WHERE guild_id = ?",
            (str(guild_id),),
            fetchall=True
        )
        
        if not results:
            self.custom_commands_cache[str(guild_id)] = {}
            return {}
        
        commands_dict = {name: response for name, response in results}
        self.custom_commands_cache[str(guild_id)] = commands_dict
        return commands_dict
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for custom commands"""
        if message.author.bot or not message.guild:
            return
        
        # Check if message starts with bot prefix
        if not message.content.startswith(self.bot.command_prefix):
            return
        
        # Get command name
        content = message.content[len(self.bot.command_prefix):].strip()
        if not content:
            return
        
        # Get first word as command name
        cmd_name = content.split()[0].lower()
        
        # Load commands if not cached
        guild_id = str(message.guild.id)
        if guild_id not in self.custom_commands_cache:
            await self.load_custom_commands(guild_id)
        
        # Check if command exists
        if cmd_name in self.custom_commands_cache.get(guild_id, {}):
            response = self.custom_commands_cache[guild_id][cmd_name]
            await message.channel.send(response)
    
    @commands.hybrid_command(name="addcommand", description="Add custom command (Admin only)")
    @commands.has_permissions(administrator=True)
    async def add_command(self, ctx, name: str, *, response: str):
        """Add custom command"""
        name = name.lower().strip()
        
        # Validate command name
        if not re.match(r'^[a-z0-9_]+$', name):
            await ctx.send("❌ Command name can only contain letters, numbers, and underscores!")
            return
        
        # Check if command exists as built-in
        if self.bot.get_command(name):
            await ctx.send("❌ This command name is reserved for built-in commands!")
            return
        
        # Check length
        if len(response) > 2000:
            await ctx.send("❌ Response too long! Max 2000 characters.")
            return
        
        # Save to database
        execute_query(
            """INSERT OR REPLACE INTO custom_commands 
               (guild_id, cmd_name, response, created_by) 
               VALUES (?, ?, ?, ?)""",
            (str(ctx.guild.id), name, response, str(ctx.author.id))
        )
        
        # Update cache
        if str(ctx.guild.id) not in self.custom_commands_cache:
            self.custom_commands_cache[str(ctx.guild.id)] = {}
        
        self.custom_commands_cache[str(ctx.guild.id)][name] = response
        
        embed = discord.Embed(
            title="✅ Custom Command Added",
            description=f"Command `{self.bot.command_prefix}{name}` created successfully!",
            color=self.bot.color
        )
        embed.add_field(name="Response", value=response[:500] + ("..." if len(response) > 500 else ""), inline=False)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="removecommand", description="Remove custom command (Admin only)")
    @commands.has_permissions(administrator=True)
    async def remove_command(self, ctx, name: str):
        """Remove custom command"""
        name = name.lower().strip()
        
        # Delete from database
        deleted = execute_query(
            "DELETE FROM custom_commands WHERE guild_id = ? AND cmd_name = ?",
            (str(ctx.guild.id), name)
        )
        
        if deleted > 0:
            # Remove from cache
            if str(ctx.guild.id) in self.custom_commands_cache:
                if name in self.custom_commands_cache[str(ctx.guild.id)]:
                    del self.custom_commands_cache[str(ctx.guild.id)][name]
            
            await ctx.send(f"✅ Command `{self.bot.command_prefix}{name}` removed!")
        else:
            await ctx.send(f"❌ Command `{name}` not found!")
    
    @commands.hybrid_command(name="listcommands", description="List all custom commands")
    async def list_commands(self, ctx):
        """List all custom commands"""
        commands_dict = await self.load_custom_commands(ctx.guild.id)
        
        if not commands_dict:
            await ctx.send("📭 No custom commands set yet!")
            return
        
        embed = discord.Embed(
            title="📋 Custom Commands",
            description=f"Total: {len(commands_dict)} commands",
            color=self.bot.color
        )
        
        # Group commands for better display
        commands_list = ""
        for i, (cmd, response) in enumerate(commands_dict.items(), 1):
            preview = response[:50] + ("..." if len(response) > 50 else "")
            commands_list += f"`{self.bot.command_prefix}{cmd}`: {preview}\n"
            
            # Split into multiple fields if too long
            if i % 10 == 0:
                embed.add_field(name=f"Commands {i-9}-{i}", value=commands_list, inline=False)
                commands_list = ""
        
        if commands_list:
            embed.add_field(name=f"Commands {len(commands_dict)-len(commands_dict)%10+1}-{len(commands_dict)}", 
                          value=commands_list, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="schedulemessage", description="Schedule recurring message (Admin only)")
    @commands.has_permissions(administrator=True)
    async def schedule_message(self, ctx, channel: discord.TextChannel, time_str: str, *, message: str):
        """
        Schedule daily message
        Format: HH:MM (24-hour)
        Example: !schedulemessage #general 09:00 Good morning!
        """
        try:
            # Parse time
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            
            # Create scheduled message entry
            schedule_id = f"{ctx.guild.id}_{channel.id}_{hour:02d}{minute:02d}"
            
            # Save to database (create table if not exists)
            execute_query('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                schedule_id TEXT PRIMARY KEY,
                guild_id TEXT,
                channel_id TEXT,
                hour INTEGER,
                minute INTEGER,
                message TEXT,
                enabled INTEGER DEFAULT 1
            )
            ''')
            
            execute_query(
                """INSERT OR REPLACE INTO scheduled_messages 
                   (schedule_id, guild_id, channel_id, hour, minute, message) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (schedule_id, str(ctx.guild.id), str(channel.id), hour, minute, message)
            )
            
            embed = discord.Embed(
                title="✅ Message Scheduled",
                description=f"Message will be sent daily at **{hour:02d}:{minute:02d}** to {channel.mention}",
                color=self.bot.color
            )
            embed.add_field(name="Message", value=message[:500], inline=False)
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Invalid time format! Use HH:MM (24-hour)")
    
    @tasks.loop(seconds=60)
    async def scheduler(self):
        """Check and send scheduled messages every minute"""
        now = datetime.now()
        
        # Get all scheduled messages
        results = execute_query(
            "SELECT guild_id, channel_id, hour, minute, message FROM scheduled_messages WHERE enabled = 1",
            fetchall=True
        )
        
        if not results:
            return
        
        for guild_id, channel_id, hour, minute, message in results:
            if now.hour == hour and now.minute == minute:
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    
                    channel = guild.get_channel(int(channel_id))
                    if not channel:
                        continue
                    
                    # Send message
                    embed = discord.Embed(
                        title="📅 Scheduled Message",
                        description=message,
                        color=self.bot.color,
                        timestamp=now
                    )
                    embed.set_footer(text="Daily scheduled message")
                    
                    await channel.send(embed=embed)
                    
                    # Wait a second to avoid rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Failed to send scheduled message: {e}")
    
    @scheduler.before_loop
    async def before_scheduler(self):
        """Wait until bot is ready"""
        await self.bot.wait_until_ready()
    
    @commands.hybrid_command(name="listscheduled", description="List all scheduled messages (Admin only)")
    @commands.has_permissions(administrator=True)
    async def list_scheduled(self, ctx):
        """List all scheduled messages"""
        results = execute_query(
            "SELECT channel_id, hour, minute, message FROM scheduled_messages WHERE guild_id = ?",
            (str(ctx.guild.id),),
            fetchall=True
        )
        
        if not results:
            await ctx.send("📭 No scheduled messages!")
            return
        
        embed = discord.Embed(
            title="📅 Scheduled Messages",
            color=self.bot.color
        )
        
        for channel_id, hour, minute, message in results:
            channel = ctx.guild.get_channel(int(channel_id))
            channel_name = channel.mention if channel else f"Channel {channel_id}"
            
            embed.add_field(
                name=f"⏰ {hour:02d}:{minute:02d} in {channel_name}",
                value=message[:200] + ("..." if len(message) > 200 else ""),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clearscheduled", description="Clear all scheduled messages (Admin only)")
    @commands.has_permissions(administrator=True)
    async def clear_scheduled(self, ctx):
        """Clear all scheduled messages"""
        deleted = execute_query(
            "DELETE FROM scheduled_messages WHERE guild_id = ?",
            (str(ctx.guild.id),)
        )
        
        await ctx.send(f"✅ Removed {deleted} scheduled messages!")

async def setup(bot):
    cog = CustomCommand(bot)
    await bot.add_cog(cog)