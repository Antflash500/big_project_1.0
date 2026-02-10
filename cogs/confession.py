import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
from datetime import datetime
from utils.database import execute_query

# ========== VIEWS & MODALS ==========

class ConfessionModal(Modal):
    """Modal for confession input"""
    def __init__(self, cog, is_reply=False, target_confession=None):
        title = "💬 Reply to Confession" if is_reply else "📨 Send Anonymous Confession"
        super().__init__(title=title, timeout=300)
        self.cog = cog
        self.is_reply = is_reply
        self.target_confession = target_confession
        
        label = "Your Reply" if is_reply else "Your Confession"
        placeholder = f"Type your {'reply' if is_reply else 'confession'} here..."
        
        self.confession_input = TextInput(
            label=label,
            style=discord.TextStyle.paragraph,
            placeholder=placeholder,
            max_length=2000,
            required=True
        )
        
        self.add_item(self.confession_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self.cog.process_confession(
            interaction, 
            self.confession_input.value, 
            self.is_reply, 
            self.target_confession
        )

class ConfessionStarterView(View):
    """View for starter message - PERSISTENT"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📨 Confess", style=discord.ButtonStyle.primary, custom_id="persistent:confess_start", emoji="📨")
    async def confess_button(self, interaction: discord.Interaction, button: Button):
        cog = interaction.client.get_cog("ConfessionSystem")
        if cog:
            modal = ConfessionModal(cog, is_reply=False)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("❌ Confession system not loaded!", ephemeral=True)

class ConfessionMessageView(View):
    """View for each confession message - PERSISTENT"""
    def __init__(self, confession_number=None, message_id=None):
        super().__init__(timeout=None)
        self.confession_number = confession_number
        self.message_id = message_id
    
    @discord.ui.button(label="📨 Confess", style=discord.ButtonStyle.primary, custom_id="persistent:confess_new", emoji="📨")
    async def confess_button(self, interaction: discord.Interaction, button: Button):
        cog = interaction.client.get_cog("ConfessionSystem")
        if cog:
            modal = ConfessionModal(cog, is_reply=False)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("❌ Confession system not loaded!", ephemeral=True)
    
    @discord.ui.button(label="💬 Reply", style=discord.ButtonStyle.secondary, custom_id="persistent:reply_confess", emoji="💬")
    async def reply_button(self, interaction: discord.Interaction, button: Button):
        cog = interaction.client.get_cog("ConfessionSystem")
        if cog and self.confession_number and self.message_id:
            modal = ConfessionModal(
                cog, 
                is_reply=True, 
                target_confession=(self.confession_number, self.message_id)
            )
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("❌ Could not get confession info!", ephemeral=True)

class ThreadReplyView(View):
    """View for replies inside thread - PERSISTENT"""
    def __init__(self, confession_number=None, message_id=None):
        super().__init__(timeout=None)
        self.confession_number = confession_number
        self.message_id = message_id
    
    @discord.ui.button(label="↩️ Reply", style=discord.ButtonStyle.secondary, custom_id="persistent:thread_reply", emoji="↩️")
    async def reply_button(self, interaction: discord.Interaction, button: Button):
        cog = interaction.client.get_cog("ConfessionSystem")
        if cog and self.confession_number and self.message_id:
            modal = ConfessionModal(
                cog, 
                is_reply=True, 
                target_confession=(self.confession_number, self.message_id)
            )
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("❌ Could not get confession info!", ephemeral=True)

# ========== MAIN COG ==========

class ConfessionSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ========== DATABASE HELPERS ==========
    
    def get_setup(self, guild_id):
        """Get confession setup"""
        result = execute_query(
            "SELECT confession_channel_id, current_number FROM confession_setup WHERE guild_id = ?",
            (str(guild_id),),
            fetch=True
        )
        return result
    
    def save_setup(self, guild_id, channel_id, message_id=None):
        """Save confession setup"""
        execute_query(
            """INSERT OR REPLACE INTO confession_setup 
               (guild_id, confession_channel_id, current_number, setup_message_id) 
               VALUES (?, ?, 0, ?)""",
            (str(guild_id), str(channel_id), str(message_id) if message_id else None)
        )
    
    def get_next_number(self, guild_id):
        """Get next confession number"""
        result = execute_query(
            "SELECT current_number FROM confession_setup WHERE guild_id = ?",
            (str(guild_id),),
            fetch=True
        )
        
        if result:
            next_num = result[0] + 1
            execute_query(
                "UPDATE confession_setup SET current_number = ? WHERE guild_id = ?",
                (next_num, str(guild_id))
            )
            return next_num
        
        return 1
    
    def save_confession(self, guild_id, user_id, message, number, thread_id, message_id, is_reply=False, reply_to=None):
        """Save confession to database"""
        execute_query(
            """INSERT INTO confession_messages 
               (guild_id, user_id, message, confession_number, thread_id, message_id, is_reply, reply_to) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(guild_id), str(user_id), message, number, str(thread_id), str(message_id), 
             1 if is_reply else 0, str(reply_to) if reply_to else None)
        )
    
    def get_confession_info(self, guild_id, confession_number):
        """Get confession info by number"""
        result = execute_query(
            "SELECT message_id, thread_id FROM confession_messages WHERE guild_id = ? AND confession_number = ?",
            (str(guild_id), confession_number),
            fetch=True
        )
        return result
    
    # ========== COMMANDS ==========
    
    @commands.hybrid_command(name="setupconfess", description="Setup confession system")
    @commands.has_permissions(administrator=True)
    async def setup_confess(self, ctx, channel: discord.TextChannel):
        """Setup confession channel"""
        # Send confirmation (ephemeral)
        embed = discord.Embed(
            title="✅ Confession System Setup",
            description=f"Confession channel set to {channel.mention}\n\n"
                       "**How it works:**\n"
                       "• **📨 Confess** = New anonymous confession\n"
                       "• **💬 Reply** = Reply to specific confession\n"
                       "• All replies go to confession thread\n"
                       "• **↩️ Reply** in thread = Chain reply system",
            color=self.bot.color
        )
        embed.set_footer(text="This message is only visible to you")
        await ctx.send(embed=embed, ephemeral=True)
        
        # Send starter message to confession channel
        starter_embed = discord.Embed(
            title="📨 Anonymous Confessions",
            description="**Click buttons below:**\n\n"
                       "• **📨 Confess** - Send new anonymous confession\n"
                       "• **💬 Reply** - Reply to specific confession\n\n"
                       "**Features:**\n"
                       "✅ Completely anonymous\n"
                       "✅ Thread for each confession\n"
                       "✅ Chain reply system\n"
                       "✅ Clean interface",
            color=self.bot.color
        )
        starter_embed.set_footer(text="Be respectful • Stay anonymous")
        
        view = ConfessionStarterView()
        starter_msg = await channel.send(embed=starter_embed, view=view)
        
        # Save setup
        self.save_setup(ctx.guild.id, channel.id, starter_msg.id)
        
        print(f"✅ Confession setup complete for guild {ctx.guild.id}")
        await ctx.send("✅ Confession system setup complete!", ephemeral=True)
    
    @commands.hybrid_command(name="logconfess", description="Set confession log channel")
    @commands.has_permissions(administrator=True)
    async def log_confess(self, ctx, channel: discord.TextChannel):
        """Set log channel"""
        execute_query(
            "UPDATE confession_setup SET log_channel_id = ? WHERE guild_id = ?",
            (str(channel.id), str(ctx.guild.id))
        )
        
        await ctx.send(f"✅ Log channel set to {channel.mention}", ephemeral=True)
    
    @commands.hybrid_command(name="loguserconfess", description="Set user confession log channel")
    @commands.has_permissions(administrator=True)
    async def log_user_confess(self, ctx, channel: discord.TextChannel):
        """Set user log channel"""
        execute_query(
            "UPDATE confession_setup SET user_log_channel_id = ? WHERE guild_id = ?",
            (str(channel.id), str(ctx.guild.id))
        )
        
        await ctx.send(f"✅ User log channel set to {channel.mention}", ephemeral=True)
    
    @commands.hybrid_command(name="confessinfo", description="Get info about a confession (Admin)")
    @commands.has_permissions(administrator=True)
    async def confess_info(self, ctx, confession_number: int):
        """Get confession info"""
        result = execute_query(
            """SELECT user_id, message, created_at, is_reply, reply_to 
               FROM confession_messages 
               WHERE guild_id = ? AND confession_number = ?""",
            (str(ctx.guild.id), confession_number),
            fetch=True
        )
        
        if not result:
            await ctx.send(f"❌ Confession #{confession_number} not found!", ephemeral=True)
            return
        
        user_id, message, created_at, is_reply, reply_to = result
        
        embed = discord.Embed(
            title=f"🔍 Confession #{confession_number} Info",
            color=discord.Color.blue()
        )
        
        member = ctx.guild.get_member(int(user_id))
        user_info = f"{member.mention} ({member})" if member else f"User ID: {user_id}"
        
        embed.add_field(name="Author", value=user_info, inline=False)
        embed.add_field(name="Type", value="Reply" if is_reply else "Confession", inline=True)
        
        if is_reply and reply_to:
            embed.add_field(name="Reply To", value=f"Confession #{reply_to}", inline=True)
        
        embed.add_field(name="Message", value=message[:500] + ("..." if len(message) > 500 else ""), inline=False)
        
        if created_at:
            try:
                timestamp = int(datetime.fromisoformat(created_at).timestamp())
                embed.add_field(name="Time", value=f"<t:{timestamp}:R>", inline=True)
            except:
                embed.add_field(name="Time", value=created_at, inline=True)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="confessstats", description="Show confession stats")
    async def confess_stats(self, ctx):
        """Show statistics"""
        setup = self.get_setup(ctx.guild.id)
        if not setup:
            await ctx.send("❌ Confession system not setup!", ephemeral=True)
            return
        
        # Get counts
        total_result = execute_query(
            "SELECT COUNT(*) FROM confession_messages WHERE guild_id = ?",
            (str(ctx.guild.id),),
            fetch=True
        )
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_result = execute_query(
            """SELECT COUNT(*) FROM confession_messages 
               WHERE guild_id = ? AND date(created_at) = ?""",
            (str(ctx.guild.id), today),
            fetch=True
        )
        
        replies_result = execute_query(
            "SELECT COUNT(*) FROM confession_messages WHERE guild_id = ? AND is_reply = 1",
            (str(ctx.guild.id),),
            fetch=True
        )
        
        total = total_result[0] if total_result else 0
        today_count = today_result[0] if today_result else 0
        replies = replies_result[0] if replies_result else 0
        
        embed = discord.Embed(
            title="📊 Confession Statistics",
            description=f"**Server:** {ctx.guild.name}",
            color=self.bot.color
        )
        
        embed.add_field(name="Total Confessions", value=f"**#{total}**", inline=True)
        embed.add_field(name="Today's", value=f"**{today_count}**", inline=True)
        embed.add_field(name="Replies", value=f"**{replies}**", inline=True)
        embed.add_field(name="Next Confession", value=f"**#{total + 1}**", inline=False)
        
        await ctx.send(embed=embed)
    
    # ========== CONFESSION PROCESSING ==========
    
    async def process_confession(self, interaction, text, is_reply=False, target_confession=None):
        """Process confession submission - FINAL CLEAN VERSION"""
        # Validation
        if not text or len(text.strip()) < 2:
            await interaction.followup.send(
                "❌ Message must be at least 2 characters!", 
                ephemeral=True
            )
            return
        
        if len(text) > 2000:
            await interaction.followup.send(
                "❌ Message too long! Max 2000 characters.", 
                ephemeral=True
            )
            return
        
        # Get setup
        setup = self.get_setup(interaction.guild.id)
        if not setup or not setup[0]:
            await interaction.followup.send(
                "❌ Confession system not setup! Contact admin.", 
                ephemeral=True
            )
            return
        
        # Get confession channel
        confession_channel = interaction.guild.get_channel(int(setup[0]))
        if not confession_channel:
            await interaction.followup.send(
                "❌ Confession channel not found!", 
                ephemeral=True
            )
            return
        
        # Get next confession number
        confession_number = self.get_next_number(interaction.guild.id)
        
        # ========== HANDLE REPLY ==========
        if is_reply and target_confession:
            target_number, target_message_id = target_confession
            
            # Get target confession info
            target_info = self.get_confession_info(interaction.guild.id, target_number)
            if not target_info:
                await interaction.followup.send(
                    f"❌ Confession #{target_number} not found!", 
                    ephemeral=True
                )
                return
            
            target_msg_id, thread_id = target_info
            
            # Get target message
            try:
                target_msg = await confession_channel.fetch_message(int(target_msg_id))
            except:
                await interaction.followup.send(
                    f"❌ Could not find confession #{target_number} message!", 
                    ephemeral=True
                )
                return
            
            # Get or create thread
            thread = None
            if thread_id:
                thread = interaction.guild.get_thread(int(thread_id))
            
            if not thread:
                # Create thread if doesn't exist
                try:
                    thread = await target_msg.create_thread(
                        name=f"Confession #{target_number} - Discussion",
                        auto_archive_duration=1440,
                        reason="Confession thread created"
                    )
                    # Update database with thread ID
                    execute_query(
                        "UPDATE confession_messages SET thread_id = ? WHERE guild_id = ? AND confession_number = ?",
                        (str(thread.id), str(interaction.guild.id), target_number)
                    )
                except Exception as e:
                    print(f"⚠️ Thread creation failed: {e}")
                    await interaction.followup.send(
                        "❌ Failed to create thread!", 
                        ephemeral=True
                    )
                    return
            
            # Create SIMPLE confession embed (SAME FORMAT AS CONFESSION)
            # NO "(Reply to #1)" in title, NO "Anonymous reply" in footer
            reply_embed = discord.Embed(
                title=f"📨 Confession #{confession_number}",  # SAMA PERSIS
                description=text,
                color=discord.Color.from_rgb(147, 112, 219)  # WARNA SAMA
            )
            reply_embed.timestamp = datetime.now()
            reply_embed.set_footer(text="Anonymous confession")  # FOOTER SAMA
            
            # Send reply to thread
            reply_msg = await thread.send(embed=reply_embed)
            
            # Add reply button to this reply (CHAIN REPLY SYSTEM)
            reply_view = ThreadReplyView(target_number, target_msg_id)
            await reply_msg.edit(view=reply_view)
            
            # Update reply count in original confession
            execute_query(
                """UPDATE confession_messages 
                   SET replies_count = replies_count + 1 
                   WHERE guild_id = ? AND confession_number = ?""",
                (str(interaction.guild.id), target_number)
            )
            
            # Save to database
            self.save_confession(
                interaction.guild.id,
                interaction.user.id,
                text,
                confession_number,
                thread.id,
                reply_msg.id,
                is_reply=True,
                reply_to=target_number
            )
            
            # Send confirmation to user (EPHEMERAL ONLY)
            await interaction.followup.send(
                f"✅ Confession #{confession_number} sent in {thread.mention}", 
                ephemeral=True
            )
            
            # Send logs (silent)
            await self.send_logs(interaction, confession_number, text, thread, is_reply=True, reply_to=target_number)
            
            return
        
        # ========== HANDLE NEW CONFESSION ==========
        # Create confession embed
        embed = discord.Embed(
            title=f"📨 Confession #{confession_number}",
            description=text,
            color=discord.Color.from_rgb(147, 112, 219)  # Purple
        )
        embed.timestamp = datetime.now()
        embed.set_footer(text="Anonymous confession")
        
        # Send confession
        confession_msg = await confession_channel.send(embed=embed)
        
        # Create thread for discussion (NO WELCOME MESSAGE)
        thread = None
        try:
            thread = await confession_msg.create_thread(
                name=f"Confession #{confession_number} - Discussion",
                auto_archive_duration=1440,
                reason="Confession thread created"
            )
            # TIDAK ADA WELCOME MESSAGE DI THREAD
        except Exception as e:
            print(f"⚠️ Thread creation failed: {e}")
            thread = None
        
        # Add buttons to confession message
        view = ConfessionMessageView(confession_number, confession_msg.id)
        await confession_msg.edit(view=view)
        
        # Save to database
        self.save_confession(
            interaction.guild.id,
            interaction.user.id,
            text,
            confession_number,
            thread.id if thread else None,
            confession_msg.id
        )
        
        # Send confirmation to user (EPHEMERAL ONLY)
        if thread:
            await interaction.followup.send(
                f"✅ Confession #{confession_number} sent\nJoin discussion: {thread.mention}", 
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ Confession #{confession_number} sent", 
                ephemeral=True
            )
        
        # Send logs (silent)
        await self.send_logs(interaction, confession_number, text, thread)
    
    async def send_logs(self, interaction, number, text, thread, is_reply=False, reply_to=None):
        """Send logs to configured channels - SILENT"""
        # Get log channels
        result = execute_query(
            "SELECT log_channel_id, user_log_channel_id FROM confession_setup WHERE guild_id = ?",
            (str(interaction.guild.id),),
            fetch=True
        )
        
        if not result:
            return
        
        log_id, user_log_id = result
        
        # Public log (if set)
        if log_id:
            channel = interaction.guild.get_channel(int(log_id))
            if channel:
                title = f"💬 Reply #{number}" if is_reply else f"📨 Confession #{number}"
                
                embed = discord.Embed(
                    title=title,
                    color=discord.Color.dark_gray()
                )
                
                if is_reply and reply_to:
                    embed.add_field(name="Reply To", value=f"Confession #{reply_to}", inline=True)
                
                embed.add_field(name="Preview", value=text[:150] + ("..." if len(text) > 150 else ""), inline=False)
                
                if thread:
                    embed.add_field(name="Thread", value=thread.mention, inline=True)
                
                embed.timestamp = datetime.now()
                
                try:
                    await channel.send(embed=embed)
                except:
                    pass
        
        # User log (admin only, if set)
        if user_log_id and interaction.user.guild_permissions.administrator:
            channel = interaction.guild.get_channel(int(user_log_id))
            if channel:
                title = f"👤 {'Reply' if is_reply else 'Confession'} #{number}"
                
                embed = discord.Embed(
                    title=title,
                    color=discord.Color.orange()
                )
                embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                
                if is_reply and reply_to:
                    embed.add_field(name="Reply To", value=f"Confession #{reply_to}", inline=True)
                
                embed.add_field(name="Message", value=text, inline=False)
                
                if thread:
                    embed.add_field(name="Thread", value=thread.mention, inline=True)
                
                embed.timestamp = datetime.now()
                
                try:
                    await channel.send(embed=embed)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(ConfessionSystem(bot))