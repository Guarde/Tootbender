import disnake, random
from disnake.ext import commands
import asyncio
from Helpers.globals import settings

async def StatusLoop(bot:commands.InteractionBot):
    while True:
        facts_channel = await bot.fetch_channel(settings.general.facts_channel)
        choices = []
        async for message in facts_channel.history(limit = 500):
            if len(message.clean_content) > 128:
                continue
            reactions = message.reactions
            up = 0
            down = 0
            for reaction in reactions:
                if reaction.emoji == "👍":
                    up = reaction.count
                elif reaction.emoji == "👎":
                    down = reaction.count

            if up - down > 3:                
                choices.append(message.clean_content)
        if len(choices) > 0:
            status = random.choice(choices)
            await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.playing, name=status))
        await asyncio.sleep(300)