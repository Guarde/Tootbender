from random import choice
from Helpers import globals
from Helpers.globals import botLog
import disnake, os, asyncio
from disnake.ext import commands
from Helpers import tbender_extras as extras
from Helpers import tbender_commands
from Helpers import tbender_moderation
from Helpers.tbender_googleapi import GoogleAPI
from Helpers.tbender_mysql import DatabaseConnection
import Helpers.tbender_logparser as logparser
import Helpers.tbender_ttsearch as tt_search
from Helpers.tbender_status import StatusLoop
from Curation import packs_commands

class Trombot(commands.InteractionBot):
    permits = []
    async def on_ready(self):
        botLog("info", self.user.name + " is up and running!")
        asyncio.create_task(StatusLoop(self))

    async def on_message(self, message:disnake.Message):
        if message.author.bot:
            return
        
        if not await tbender_moderation.handle_incoming_message(message):
            return
        
        if message.channel.id == int(globals.settings.general.submissions_channel):
            if not message.thread == None:
                return
            await extras.handle_submission(self, message, db, globals.googleapi)

        if len(message.attachments) > 0:
            att = logparser.find_attachment(message)
            if att and att.filename in ["LogOutput.log", "LogOutput.log.1"]:
                emb, paste = await logparser.parse_log(message, att.url)
                botLog("info", f"Parsed {message.author.display_name}'s LogOutput.log") 
                if paste:
                    button = [disnake.ui.Button(label="Open Log Hastebin", url = paste)]
                    await message.reply(embed=emb, components=button, mention_author=False)
                else:
                    await message.reply(embed=emb, mention_author=False)


            if att and att.filename == "song.tmb":
                emb = await tbender_commands.analyze(message, att.url, globals.settings.upload.tt_api_key)
                if emb:
                    await message.reply(embed=emb, mention_author=False)

globals.googleapi = GoogleAPI()
level, message = globals.googleapi.connect()
botLog(level, message)

db = DatabaseConnection()

bot = Trombot(intents=disnake.Intents.all(), activity=disnake.CustomActivity("/help"))
@bot.event
async def on_interaction(inter:disnake.ApplicationCommandInteraction):
    if str(inter.type) == "InteractionType.application_command":
        botLog("info", f"{inter.user.display_name} executed /{inter.application_command.name}") 
        
@bot.slash_command()
async def wiki(inter:disnake.ApplicationCommandInteraction):
    """Links to the Wiki page"""
    await tbender_commands.wiki(inter)
            
@bot.slash_command()
async def trombloader(inter:disnake.ApplicationCommandInteraction):
    """Get a link to download Trombloader"""
    await tbender_commands.trombloader(inter)
            
@bot.slash_command()
async def r2modman(inter:disnake.ApplicationCommandInteraction):
    """Download r2modman!"""
    await tbender_commands.r2modman(inter)
            
@bot.slash_command()
async def spreadsheet(inter:disnake.ApplicationCommandInteraction):
    """Get a Spreadsheet Link"""
    await tbender_commands.spreadsheet(inter)
            
@bot.slash_command()
async def howtomod(inter:disnake.ApplicationCommandInteraction):
    """A quick overview on how to mod the game"""
    await tbender_commands.howtomod(inter)

@bot.slash_command()
async def howtoaddcharts(inter:disnake.ApplicationCommandInteraction):
    """So you already modded the game and want to add songs?"""
    await tbender_commands.howtoaddcharts(inter)

@bot.slash_command()
async def howtochart(inter:disnake.ApplicationCommandInteraction):
    """Learn how to create charts yourself!"""
    await tbender_commands.howtochart(inter)@bot.slash_command()
    
@bot.slash_command()
async def howtomigrate(inter:disnake.ApplicationCommandInteraction):
    """Learn how to migrate if you have already modded the game manually!"""
    await tbender_commands.howtomigrate(inter)

@bot.slash_command()
async def modsearch(inter:disnake.ApplicationCommandInteraction, search:str=commands.Param(default="LIST", autocomplete=tbender_commands.modsearch_autocomplete)):
    """Search for mods on Thunderstore!"""
    await tbender_commands.modsearch(inter, search)
    tbender_commands.fullmodlist = tbender_commands.modsearch_update_list()

@bot.slash_command()
async def search(inter:disnake.ApplicationCommandInteraction, search:str=commands.Param(description="The name, artist or other info of the chart you want to search for.", autocomplete=tt_search.chart_search_autocomplete)):
    """Search for charts by name or artist!"""
    await tt_search.command(bot, inter, search)

@bot.slash_command()
async def randomchart(inter:disnake.ApplicationCommandInteraction, rated:str=commands.Param(description="Rated Status", choices=["Rated", "Unrated", "Unspecified"])):
    """Get a random chart!"""
    status = None
    if rated == "Rated":
        status = True
    if rated == "Unrated":
        status = False        
    await tbender_commands.randomchart(inter, status)
    
@bot.slash_command()
async def tootbender(inter:disnake.ApplicationCommandInteraction):
    """Learn more about the bot"""
    await tbender_commands.tootbender_command(inter)

@bot.slash_command()
async def paths(inter:disnake.ApplicationCommandInteraction, platform: str = commands.Param(choices=["Windows", "Linux", "MacOS", "All"])):
    """Get a list relevant paths and how to find them"""
    await tbender_commands.paths(inter, platform)

@bot.slash_command()
async def pirate(inter:disnake.ApplicationCommandInteraction):
    """Show information about pirated versions of Trombone Champ."""
    await tbender_commands.pirate(inter)
@bot.slash_command()
async def sale(inter:disnake.ApplicationCommandInteraction):
    """Check the current price of the Trombone Champ."""
    await tbender_commands.sale(inter)

@bot.slash_command()
async def help(inter:disnake.ApplicationCommandInteraction):
    """Get a list of Tootbender's commands"""
    await tbender_commands.help(inter)

@bot.slash_command()
async def rank(inter:disnake.ApplicationCommandInteraction, search:disnake.Member=None):
    """View a user's TootTally profile"""
    if search == None:
        search = inter.user
    await tbender_commands.toottally_rank(inter, search)

@bot.slash_command()
async def pack(inter:disnake.ApplicationCommandInteraction):
    pass

@pack.sub_command()
async def create(inter:disnake.ApplicationCommandInteraction, name:str):
    """Create a new chart pack from this forum post"""
    await packs_commands.create_pack(inter, name)

@pack.sub_command()
async def delete(inter:disnake.ApplicationCommandInteraction):
    """Create a new chart pack from this forum post"""
    await packs_commands.delete_pack(inter)
 
@pack.sub_command()
async def add(inter:disnake.ApplicationCommandInteraction, ids:str):
    """Add charts to the current pack"""
    await packs_commands.add_chart(inter, ids)
 
@pack.sub_command()
async def remove(inter:disnake.ApplicationCommandInteraction, ids:str):
    """Remove charts from the current pack"""
    await packs_commands.remove_chart(inter, ids)

@pack.sub_command()
async def update_message(inter:disnake.ApplicationCommandInteraction):
    """Manually update the chart pack message"""

@bot.slash_command()
async def updatechartlist(inter:disnake.ApplicationCommandInteraction):
    """Manually fetch a full list of charts from TootTally"""
    if not tbender_commands.is_mod(inter.author):
        await tbender_commands.permission_denied(inter)
    else:
        await globals.all_charts.get_songs(inter)

@bot.slash_command()
async def setchartowner(inter:disnake.ApplicationCommandInteraction, user:disnake.User, trackref:str):
    """Manually set the owner of a chart in the bot's database"""
    if not tbender_commands.is_mod(inter.author):
        await tbender_commands.permission_denied(inter)
    else:
        await tbender_commands.update_chart_owner(inter, user, trackref, db)

@bot.slash_command()
async def permit(inter:disnake.ApplicationCommandInteraction, user:disnake.User=commands.Param(description="Target user"), size:int=commands.Param(description="Maximum file size in MB"), duration:int=commands.Param(description="Timeout in minutes")):
    """Get a list of Tootbender's commands"""
    response = await tbender_commands.permit(inter, user, size, duration*60)
    if not tbender_commands.is_mod(inter.author):
        await tbender_commands.permission_denied(inter)
    else:
        if response:
            bot.permits.append(response)
            await asyncio.sleep(duration*60)
            try:
                bot.permits.remove(response)
            except ValueError:
                pass

bot.run(globals.settings.general.bot_token)