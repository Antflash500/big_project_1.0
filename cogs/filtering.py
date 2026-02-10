import discord
from discord.ext import commands
from utils.database import execute_query

class Filtering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.filter_cache = {}
        
    async def load_filtered_words(self, guild_id):
        results = execute_query(
            "SELECT word FROM filtered_words WHERE guild_id = ?",
            (str(guild_id),),
            fetchall=True
        )
        
        words = [row[0].lower() for row in results] if results else []
        self.filter_cache[str(guild_id)] = words
        return words
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # 🔥 PERBAIKAN: Skip jika user punya permission manage_messages
        if message.author.guild_permissions.manage_messages:
            return
        
        guild_id = str(message.guild.id)
        
        if guild_id not in self.filter_cache:
            await self.load_filtered_words(guild_id)
        
        words = self.filter_cache.get(guild_id, [])
        if not words:
            return
        
        content = message.content.lower()
        
        for word in words:
            if word in content:
                try:
                    await message.delete()
                    
                    # Log to console
                    print(f"⚠️ Filtered message from {message.author}: {word}")
                    
                    # Try to DM user
                    try:
                        warning = discord.Embed(
                            title="⚠️ Message Deleted",
                            description="Your message was deleted because it contained a filtered word.",
                            color=discord.Color.orange()
                        )
                        warning.add_field(name="Server", value=message.guild.name, inline=False)
                        warning.add_field(name="Filtered Word", value=f"`{word}`", inline=False)
                        await message.author.send(embed=warning)
                    except:
                        pass
                    
                except discord.Forbidden:
                    print(f"❌ No permission to delete message in {message.guild.name}")
                break
    
    @commands.hybrid_command(name="addfilter", description="Add word to filter (Admin only)")
    @commands.has_permissions(administrator=True)
    async def add_filter(self, ctx, *, word: str):
        """Add word to filter list"""
        word = word.lower().strip()
        guild_id = str(ctx.guild.id)
        
        execute_query(
            "INSERT OR IGNORE INTO filtered_words (guild_id, word, added_by) VALUES (?, ?, ?)",
            (guild_id, word, str(ctx.author.id))
        )
        
        # Update cache
        if guild_id in self.filter_cache:
            if word not in self.filter_cache[guild_id]:
                self.filter_cache[guild_id].append(word)
        else:
            self.filter_cache[guild_id] = [word]
        
        embed = discord.Embed(
            title="✅ Word Added to Filter",
            description=f"Word `{word}` has been added to the filter list.",
            color=self.bot.color
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="removefilter", description="Remove word from filter (Admin only)")
    @commands.has_permissions(administrator=True)
    async def remove_filter(self, ctx, *, word: str):
        word = word.lower().strip()
        guild_id = str(ctx.guild.id)
        
        execute_query(
            "DELETE FROM filtered_words WHERE guild_id = ? AND word = ?",
            (guild_id, word)
        )
        
        if guild_id in self.filter_cache and word in self.filter_cache[guild_id]:
            self.filter_cache[guild_id].remove(word)
        
        embed = discord.Embed(
            title="✅ Word Removed from Filter",
            description=f"Word `{word}` has been removed from the filter list.",
            color=self.bot.color
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="listfilter", description="Show all filtered words (Admin only)")
    @commands.has_permissions(administrator=True)
    async def list_filter(self, ctx):
        words = await self.load_filtered_words(ctx.guild.id)
        
        if not words:
            await ctx.send("📭 No words in filter list.")
            return
        
        embed = discord.Embed(
            title="🚫 Filtered Words",
            description=f"Total: {len(words)} words",
            color=self.bot.color
        )
        
        # Show in chunks of 15
        for i in range(0, len(words), 15):
            chunk = words[i:i + 15]
            embed.add_field(
                name=f"Words {i+1}-{min(i+15, len(words))}",
                value="\n".join(f"• `{w}`" for w in chunk),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clearfilter", description="Clear all filtered words (Admin only)")
    @commands.has_permissions(administrator=True)
    async def clear_filter(self, ctx):
        guild_id = str(ctx.guild.id)
        
        execute_query(
            "DELETE FROM filtered_words WHERE guild_id = ?",
            (guild_id,)
        )
        
        if guild_id in self.filter_cache:
            del self.filter_cache[guild_id]
        
        embed = discord.Embed(
            title="✅ Filter Cleared",
            description="All filtered words have been removed.",
            color=self.bot.color
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Filtering(bot))