import discord
from discord.ext import commands
import traceback
from config import TOKEN, PREFIX, BOT_COLOR

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class StarFamilyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the stars 🌟"
            )
        )
        self.color = BOT_COLOR
    
    async def setup_hook(self):
        print("📦 Loading cogs...")
        
        cogs = [
            'cogs.basic',
            'cogs.moderation', 
            'cogs.leveling',
            'cogs.welcome',
            'cogs.filtering',
            'cogs.confession',      # 🔥 CLEAN VERSION
            'cogs.custom_command'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        # Add persistent views AFTER loading cogs
        from cogs.confession import ConfessionStarterView, ConfessionMessageView, ThreadReplyView
        self.add_view(ConfessionStarterView())
        self.add_view(ConfessionMessageView())
        self.add_view(ThreadReplyView())
        print("✅ Persistent views registered")
    
    async def on_ready(self):
        print(f"✅ Logged in as {self.user.name} ({self.user.id})")
        print(f"🌟 Star Family Bot is ready!")
        print(f"📊 Serving {len(self.guilds)} guilds")
        
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")

bot = StarFamilyBot()

if __name__ == "__main__":
    # Initialize database
    from utils.database import init_db
    init_db()
    
    print("🚀 Starting bot...")
    bot.run(TOKEN)