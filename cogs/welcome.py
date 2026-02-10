import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os
from config import BACKGROUND_IMAGE, FONT_PATH
from utils.database import execute_query

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_welcome_channel(self, guild_id):
        """Get welcome channel from database"""
        try:
            result = execute_query(
                "SELECT channel_id FROM welcome_config WHERE guild_id = ?",
                (str(guild_id),),
                fetch=True
            )
            if result and result[0]:
                return int(result[0])
            return None
        except Exception as e:
            print(f"⚠️ Welcome config error: {e}")
            return None
    
    async def set_welcome_channel(self, guild_id, channel_id):
        """Set welcome channel in database"""
        execute_query(
            """INSERT OR REPLACE INTO welcome_config (guild_id, channel_id) 
               VALUES (?, ?)""",
            (str(guild_id), str(channel_id))
        )
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        channel_id = await self.get_welcome_channel(guild_id)
        
        if not channel_id:
            return
        
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        
        # Create welcome embed
        embed = discord.Embed(
            title=f"🌟 Welcome to {member.guild.name}!",
            description=f"Hello {member.mention}! Welcome to our server.\n"
                       f"You are member #{member.guild.member_count}",
            color=self.bot.color
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.add_field(name="📅 Account Created", 
                       value=f"<t:{int(member.created_at.timestamp())}:R>", 
                       inline=True)
        embed.add_field(name="📥 Joined Server", 
                       value=f"<t:{int(member.joined_at.timestamp())}:R>", 
                       inline=True)
        
        embed.set_footer(text=f"ID: {member.id}")
        
        # Try to send with image
        try:
            image_bytes = await self.create_welcome_image(member)
            if image_bytes:
                file = discord.File(image_bytes, filename="welcome.png")
                embed.set_image(url="attachment://welcome.png")
                await channel.send(file=file, embed=embed)
            else:
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Welcome image error: {e}")
            await channel.send(embed=embed)
    
    async def create_welcome_image(self, member):
        """Create simple welcome image"""
        try:
            # Create basic image
            img = Image.new('RGB', (800, 300), color=(26, 26, 46))
            draw = ImageDraw.Draw(img)
            
            # Try to load font
            try:
                if os.path.exists(FONT_PATH):
                    font_large = ImageFont.truetype(FONT_PATH, 40)
                    font_small = ImageFont.truetype(FONT_PATH, 30)
                else:
                    font_large = ImageFont.load_default(size=40)
                    font_small = ImageFont.load_default(size=30)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw text
            draw.text((400, 100), f"Welcome {member.name}!", 
                     fill=(255, 255, 255), font=font_large, anchor="mm")
            draw.text((400, 160), f"to {member.guild.name}", 
                     fill=(200, 200, 255), font=font_small, anchor="mm")
            draw.text((400, 220), f"Member #{member.guild.member_count}", 
                     fill=(170, 170, 255), font=font_small, anchor="mm")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
            
        except Exception as e:
            print(f"Image creation failed: {e}")
            return None
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        channel_id = await self.get_welcome_channel(guild_id)
        
        if not channel_id:
            return
        
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title="👋 Goodbye",
            description=f"**{member}** has left the server.",
            color=discord.Color.dark_gray()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.add_field(name="📅 Joined", 
                       value=f"<t:{int(member.joined_at.timestamp())}:R>", 
                       inline=True)
        embed.add_field(name="👥 Members Left", 
                       value=f"{member.guild.member_count}", 
                       inline=True)
        
        await channel.send(embed=embed)
    
    @commands.hybrid_command(name="setwelcome", description="Set welcome channel (Admin only)")
    @commands.has_permissions(administrator=True)
    async def set_welcome(self, ctx, channel: discord.TextChannel):
        """Set channel for welcome/goodbye messages"""
        await self.set_welcome_channel(ctx.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Welcome Channel Set",
            description=f"Welcome and goodbye messages will be sent to {channel.mention}",
            color=self.bot.color
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="testwelcome", description="Test welcome message (Admin only)")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        """Test welcome message with current user"""
        await self.on_member_join(ctx.author)

async def setup(bot):
    await bot.add_cog(Welcome(bot))