import disnake, json, math, datetime, requests
from os import path
from Helpers.globals import botLog
from Helpers.tbender_song import Song
from Helpers.tbender_settings import botset
from Helpers import globals

def embed_builder(header:str, description:str, content:list(tuple(str()))=None):
    if header == None or header.strip() == "":
        botLog("warning", "Embed Builder received an empty header")
        return False
        
    emb = disnake.Embed(title = header, description = description, colour = disnake.Colour.orange())

    if content == None:
        return emb
            
    for field in content:
        title, value = field
        if value == None or value.strip == "":
            botLog("warning", "Embed Builder received an empty field")
            return False
        if title == None or title.strip == "":
            title == "\u200c"
        emb.add_field(title, value, inline = False)    
    return emb

def is_mod(user:disnake.Member):
    if str(user.id) in globals.settings.general.owners:
        return True

    roles = []
    for r in user.roles:
        roles.append(str(r.id))
    res = list(set(globals.settings.general.mod_roles) & set(roles))
    if len(res) > 0:
        return True
    return False
    

async def help(inter:disnake.ApplicationCommandInteraction):
    emb = disnake.Embed(title="Tootbender's Commands", description="This bot is equipped with some useful commands!\nDon't be afraid to use them!")
    # /help
    emb.add_field("/help", "Show this list of commands", inline = False)
    # /tootbender
    emb.add_field("/tootbender", "Learn more about this bot", inline = False)
    # /wiki
    emb.add_field("/wiki", "Get a link to the Trombone Champ Wiki", inline = False)
    # /spreadsheet
    emb.add_field("/spreadsheet", "Get a link to the Custom Chart Spreadsheet", inline = False)
    # /trombloader
    emb.add_field("/trombloader", "Shows information about TrombLoader", inline = False)
    # /r2modman
    emb.add_field("/r2modman", "Shows information about r2modman", inline = False)
    # /howtomod
    emb.add_field("/howtomod", "Learn how to mod the game!", inline = False)
    # /howtoaddcharts
    emb.add_field("/howtoaddcharts", "Learn how to add charts to your game!", inline = False)
    # /howtochart
    emb.add_field("/howtomigrate", "Find out how to migrate your charts if you've already modded your game manually.", inline = False)
    # /howtochart
    emb.add_field("/howtochart", "Learn how to make awesome charts yourself!", inline = False)
    # /paths
    emb.add_field("/paths <platform>", "Get a list of relevant game paths.", inline = False)
    # /modsearch
    emb.add_field("/modsearch [Mod Name]", "Search for mods on Thunderstore.\n`Mod Name (Optional)`: Name of the mod you wish to look up.\n*Use without parameters to show a list of availble mods*", inline = False)
    # /rank
    emb.add_field("/rank <user>", "Shows a user's TootTally profile, if available. Use without arguments to show own profile", inline = False)
    # /randomchart
    emb.add_field("/randomchart", "Don't know what to play? Get a random chart", inline = False)
    # /search
    emb.add_field("/search [query]", "Search for charts on TootTally.", inline = False)
    # /search
    emb.add_field("/pirate", "Show information about pirated versions of Trombone Champ.", inline = False)
    # /search
    emb.add_field("/sale", "Check the current price of the Trombone Champ.", inline = False)
    if is_mod(inter.author):
        # /permit
        emb.add_field("/permit <user> [size]", "Allow a user to upload a bigger file for 30 minutes. (Size in megabytes)", inline = False)
        # /updatechartlist
        emb.add_field("/updatechartlist", "Manually fetch all charts from TootTally (used for /randomchart and search autocompletion)", inline = False)
    await inter.send(embed=emb)

async def permission_denied(inter:disnake.ApplicationCommandInteraction):
    emb = disnake.Embed(title="Permission denied!", description=f"You are not allowed to do this...", color=disnake.Color.red())
    await inter.send(embed=emb)

async def toottally_rank(inter:disnake.ApplicationCommandInteraction, target_user:disnake.User):
    emb = disnake.Embed(title="TootTally Rank", description= "Obtaining information...")
    await inter.send(embed=emb)
    discord_id = target_user.id
    emb = disnake.Embed()
    #https://toottally.com/api/users/search/?discordID=153045798324535296
    r = await globals.session.get(f"https://toottally.com/api/users/search/?discordID={discord_id}", allow_redirects=True)
    if not r.ok:
        emb = disnake.Embed(title="API Request Failed", description=f"API request failed with status:\n```[{r.status}] {r.reason}```\n\nPlease try again later")
        emb.color = disnake.Color.brand_red()
        await inter.edit_original_message(embed=emb)
        return
    userinfo = json.loads(await r.read())
    if userinfo["count"] == 0:
        emb = disnake.Embed(title="No profile found", description=f"Couldn't find a TootTally profile for selected user. It is likely that they haven't linked their TootTally profiles to Discord yet")
        emb.color = disnake.Color.brand_red()
        await inter.edit_original_message(embed=emb)
        return
    userinfo = userinfo["results"][0]
    emb = disnake.Embed(title=f"", description=f"# [{userinfo['username']}](https://toottally.com/profile/{userinfo['id']})\n## Rank #{userinfo['rank']} - TT: {round(userinfo['tt'], ndigits=2)}")
    if userinfo['picture'] == None:
        userinfo['picture'] = "https://cdn.toottally.com/assets/icon.png"
    emb.set_thumbnail(userinfo['picture'])

    #https://toottally.com/api/profile/USER_ID/best_scores/
    r_2 = await globals.session.get(f"https://toottally.com/api/profile/{userinfo['id']}/best_scores", allow_redirects=True)
    if r_2.ok:
        bestplays = json.loads(await r_2.read())["results"]
        bestplays = bestplays[:min(len(bestplays), 3)]
        emb.add_field(name = "> **Best Plays:**", value = "", inline=False)
        for bestplay in bestplays:
            emb.add_field(name = f"`{bestplay['song_name']}`", value = f"**Grade:** {bestplay['grade']} ({round(bestplay['percentage'], ndigits=2)}%)\n**Points:** {bestplay['score']} ({round(bestplay['tt'], ndigits=2)} TT)\n[Leaderboard](https://toottally.com/song/{bestplay['song_id']})", inline=True)
    
    #https://toottally.com/api/profile/USER_ID/recent_scores/
    r_3 = await globals.session.get(f"https://toottally.com/api/profile/{userinfo['id']}/recent_scores", allow_redirects=True)
    if r_3.ok:
        recentplays = json.loads(await r_3.read())["results"]
        recentplays = recentplays[:min(len(recentplays), 3)]
        emb.add_field(name = "> **Recent Plays:**", value = "", inline=False)
        for recentplay in recentplays:
            emb.add_field(name = f"`{recentplay['song_name']}`", value = f"**Grade:** {recentplay['grade']} ({round(recentplay['percentage'], ndigits=2)}%)\n**Points:** {recentplay['score']} ({round(recentplay['tt'], ndigits=2)} TT)\n[Leaderboard](https://toottally.com/song/{recentplay['song_id']})", inline=True)

    emb.color = disnake.Colour.brand_green()
    emb.set_footer(text="Powered by TootTally")
    await inter.edit_original_message(embed=emb)

async def permit(inter:disnake.ApplicationCommandInteraction, user:disnake.User, size:int, duration:int):
    author = inter.author
    if not is_mod(author):
        await inter.send(embed=disnake.Embed(title="No Permissions!", description="Sorry, but you are not allowed to do this...", color=disnake.Color.red()))
        return
    t = f"<t:{round(datetime.datetime.now().timestamp()) + duration}:R>"
    if size >= 1000:
        s = round(size/1000, ndigits=2)
        unit = "Gigabyte"
    else:
        s = size
        unit = "Megabyte"
    await inter.send(content =  user.mention, embed = disnake.Embed(title="File size permission", description=f"You have been given permission to upload a song of **up to {s} {unit}**!\n\nThis permission expires {t}"), delete_after=duration)
    message = await inter.original_response()
    return (user, size, message)

async def pirate(inter:disnake.ApplicationCommandInteraction):
    appid=1059990
    price = ""
    req = await globals.session.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=price_overview&cc=US")
    if not req.ok:
        price = "Unable to obtain pricing information."
        message = f"POST request returned error [{req.status}] {req.reason}"
        botLog("warning", message)
    else:
        req = json.loads(await req.read())
        po = req[str(appid)]["data"]["price_overview"]
        if po["discount_percent"] > 0:
            price = f'[Trombone Champ](https://store.steampowered.com/app/1059990/Trombone_Champ/) is **currently on sale** for {po["final_formatted"]} ({po["discount_percent"]}% off)'
        else:
            price = f'[Trombone Champ](https://store.steampowered.com/app/1059990/Trombone_Champ/) is** currently not on sale**, but you can keep track of past and current sales [here](https://isthereanydeal.com/game/trombonechamp/info/)!'
    emb = disnake.Embed(title= "If you are using a pirated version of the game:", description=f"- This community does not support Piracy and discussing it is against Discord's Terms of Service!\n- Only the **Steam Version** of the game may be modded, you will not receive any modding support for a pirated version.\n- Consider purchasing the game before asking for any further help.\n{price}")
    await inter.send(embed=emb)


async def sale(inter:disnake.ApplicationCommandInteraction):
    appid=1059990
    price = ""
    req = await globals.session.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=price_overview&cc=US")
    if not req.ok:
        price = "Unable to obtain pricing information."
        message = f"POST request returned error [{req.status}] {req.reason}"
        botLog("warning", message)
    else:
        req = json.loads(await req.read())
        po = req[str(appid)]["data"]["price_overview"]
        if po["discount_percent"] > 0:
            price = f'[Trombone Champ](https://store.steampowered.com/app/1059990/Trombone_Champ/) is **currently on sale** for {po["final_formatted"]} ({po["discount_percent"]}% off)'
        else:
            price = f'[Trombone Champ](https://store.steampowered.com/app/1059990/Trombone_Champ/) is** currently not on sale**! (Price: {po["final_formatted"]})'
    emb = disnake.Embed(title= "Current sale:", description=f"{price}")
    await inter.send(embed=emb)

async def paths(inter:disnake.ApplicationCommandInteraction, platform:str):
    emb = disnake.Embed(title="Path Info", description="Here's some paths you might need when adding mods or custom charts!")
    game = ""
    data = ""
    bep = ""
    if platform.lower() in ["windows", "all"]:
        game = game + "\n**- Windows:**`C:\\Program Files (x86)\\Steam\\steamapps\\common\\TromboneChamp`"
        data = data + "\n**- Windows:**`%AppData%\\..\\LocalLow\\Holy Wow\\TromboneChamp`"
        bep = bep + "\n**Windows:**   - `%AppData%\\r2modmanPlus-local\\TromboneChamp\\profiles\\Default\\BepInEx`\*"
    if platform.lower() in ["linux", "all"]:
        game = game + "\n**- Linux:**`~/.local/share/Steam/steamapps/common/TromboneChamp`"
        data = data + "\n**- Linux:**`~/.local/share/Steam/steamapps/compatdata/1059990/pfx/drive_c/users/steamuser/AppData/LocalLow/Holy Wow/TromboneChamp`"
        bep = bep + "\n**- Linux:**`~/.config/r2modmanPlus-local/TromboneChamp/profiles/Default/BepInEx`\*"
    if platform.lower() in ["windows","linux", "all"]:
        bep = bep + "\n\n\**You might need to replace 'Default' with your custom profile name.* \n*In r2modman you can open this folder by clicking `Settings -> Browse Profile Folder`"
    if platform.lower() in ["macos", "all"]:
        game = game + "\n**- MacOS:**`~/Library/Application Support/Steam/steamapps/common/TromboneChamp`"
        data = data + "\n**- MacOS:***'Player.log':* `~/Library/Logs/Holy Wow/TromboneChamp`\n*Saves:* `~/Library/Application Support/com.holywowstudios.trombonechamp`"
        bep = bep + "\n\n*On MacOS this folder is located inside of your game folder.*"
    emb.add_field("__Game Folder__", f"This folder contains all files of your game installation{game}\n\n*You can easily reach this through `Steam -> Right Click the Game -> Manage -> Browse Local Files`*", inline = False)
    emb.add_field("__Game Data Folder__ (Player.log, Save Data)", data, inline = False)
    emb.add_field("__BepInEx Folder__ (CustomSongs, Plugins, LogOutput.log)", bep, inline = False)
    await inter.send(embed=emb)

async def analyze(message:disnake.Message, url:str, tt_key:str):
    if len(message.attachments) == 0:
        return
    attachment = None
    for att in message.attachments:
        if ".tmb" in att.filename:
            attachment = att
            break
    if attachment == None:
        return
    if attachment.size > 50000000:
        return embed_builder("Download rejected", "Your file is larger than 50MB\n\n(LITERALLY HOW!?)")
        
    req = await globals.session.get(attachment.url)
    if not req.ok:
        return False
    try:
        text = await req.text()
        tmb = json.loads(text)
    except Exception as e:
        return embed_builder("Error", f"Unable to load json from file\nExited with:\n{e.name}: {e.reason}")
    try:
        song = Song(tmb, None, None, None, None, "e")
    except Exception as e:
        name, reason = e
        if name == "MissingKeys":
            return embed_builder("Error", f"Your TMB is missing the following mandatory keys:\n" + '\n- '.join(reason))
        else:
            botLog("error", f"The following error occured when trying to create the song object: [{name} {reason}]")
            return embed_builder("Error", f"The following error occured when trying to create the song object: [{name} {reason}]")
    song = song.as_dict()
    url = "https://toottally.com/api/upload/"
    data = {"song": json.dumps(song), "skip_save": True, "api_key": tt_key}
    tt_error = ""
    tt = await globals.session.post(url, data=data)
    if not tt.ok:
        tt_error = f"\n\n*Encountered the following API error when processing your chart via TootTally:* \n*`[{tt.status}] {tt.reason}`*"
    ttext = await tt.text()
    if "Request Entity Too Large" in ttext:
        tt_error = f"\n\n*Encountered the following API error when processing your chart via TootTally:* \n*`TMB was too large to be analyzed`*"
    name = tmb["name"]
    desc = tmb["description"]
    set_difficulty = tmb["difficulty"]
    bpm = tmb["tempo"]
    note_count = len(tmb["notes"])
    spacing = tmb["savednotespacing"]
    duration = song["duration_string"]
    filestats = f">>> **TMB Difficulty**: {set_difficulty}\n**Tempo**: {bpm}bpm\n**Duration**: {duration}\n**Note Count**: {note_count}\n**Note Spacing**: {spacing}"
    emb = disnake.Embed(title=f"Successfully analyzed \"{name}\"")
    emb.add_field("Description:", desc, inline=False)
    emb.add_field("File Stats:", filestats + tt_error)
    if tt_error == "":
        tt = json.loads(ttext)
        tt_difficulty = round(float(tt["difficulty"]), ndigits = 2)
        tap_rating = round(float(tt["tap"]), ndigits = 2)
        aim_rating = round(float(tt["aim"]), ndigits = 2)
        base_tt = round(float(tt["base_tt"]), ndigits = 2)
        ttstats = f">>> **TT Difficulty**: {tt_difficulty}\n**Tap Rating**: {tap_rating}\n**Aim Rating**: {aim_rating}\n**Base TT**: {base_tt}"
        emb.add_field("TootTally Stats:", ttstats)
    return emb


def modsearch_autocomplete(inter: disnake.ApplicationCommandInteraction, string: str):
    string = string.lower()
    return [mod for mod in fullmodlist if string in mod.lower()]

def modsearch_update_list():
    req = requests.get("https://thunderstore.io/api/experimental/frontend/c/trombone-champ/packages/")
    if req.ok:
        mods = ["LIST"]
        data = json.loads(req.text)
        skips = ["r2modman", "BepInExPack_TromboneChamp"]
        for mod in data["packages"]:
            if mod["is_deprecated"]:
                continue
            if mod["package_name"] in skips:
                continue
            mods.append(mod["package_name"])
        return mods
    return []

async def modsearch(inter:disnake.ApplicationCommandInteraction, search:str):
    req = await globals.session.get("https://thunderstore.io/api/experimental/frontend/c/trombone-champ/packages/")
    
    if not req.ok:
        emb = embed_builder("API Error", f"API Request exited with error [{req.status}] {req.reason}")
        await inter.send(embed=emb)
        return
    data = await req.text()
    data = json.loads(data)

    skips = ["r2modman", "BepInExPack_TromboneChamp"]
    mods = []

    for mod in data["packages"]:
        if mod["is_deprecated"]:
            continue
        if mod["package_name"] in skips:
            continue

        mods.append(mod["package_name"])

    if search.lower() == "list":
        await modsearch_empty(inter, mods)
        return

    await modsearch_notempty(inter, data, search)

async def modsearch_empty(inter:disnake.ApplicationCommandInteraction, mods:list):    
    emb = embed_builder("Trombone Champ Mods", f"The following {len(mods)} mods have been found on Thunderstore:\n*(Use /modsearch <modname> to view details)*")
    stop1 = math.ceil(len(mods)/3)
    stop2 = math.floor(len(mods)/1.5)
    emb.add_field("\u200c", "\n".join(mods[:stop1]))
    emb.add_field("\u200c", "\n".join(mods[stop1:stop2]))
    emb.add_field("\u200c", "\n".join(mods[stop2:]))
    await inter.send(embed=emb)

async def modsearch_notempty(inter:disnake.ApplicationCommandInteraction, data:dict, search:str):
    for mod in data["packages"]:
        if mod["package_name"].lower() == search.lower():
            name = mod["package_name"]
            namespace = mod["namespace"]
            await modsearch_getmod(inter, name, namespace)
            return
        continue
    emb = embed_builder("Trombone Champ Mods", f"Unable to find a mod matching \"{search}\"")
    await inter.send(embed=emb)

async def modsearch_getmod(inter:disnake.ApplicationCommandInteraction, name:str, namespace:str):
    req = await globals.session.get(f"https://thunderstore.io/api/experimental/package/{namespace}/{name}/")
    if not req.ok:
        emb = embed_builder("API Error", f"API Request exited with error [{req.status}] {req.reason}")
        await inter.send(embed=emb)
        return
    data = await req.text()
    data = json.loads(data)
    name = data["name"]
    author = data["owner"]
    description = data["latest"]["description"]
    version = data["latest"]["version_number"]
    download = data["package_url"].replace("thunderstore.io/", "trombone-champ.thunderstore.io/")
    icon = data["latest"]["icon"]
    website = data["latest"]["website_url"]
    categories = data["community_listings"][0]["categories"]
    dependencies = data["latest"]["dependencies"]
    emb = embed_builder(f"Modinfo for [{name}]", description, None)
    emb.add_field("Author", author)
    emb.add_field("Latest Version", version)
    emb.add_field("Categories", ", ".join(categories))
    emb.add_field("Dependencies", "\n".join(dependencies), inline = False)
    buttons = [disnake.ui.Button(style=disnake.ButtonStyle.link, label="Thunderstore", url = download)]
    if website != None and website.strip() != "":
        buttons.append(disnake.ui.Button(style=disnake.ButtonStyle.link, label="Website", url = website))
    emb.set_thumbnail(icon)
    await inter.send(embed=emb, components=buttons)

async def wiki(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("TromboneChamp Modding Wiki", "Find out everything you need to know for your Tromboning needs on the **[TromboneChamp Modding Wiki](https://trombone.wiki/)**!")
    await inter.send(embed=emb)

async def howtomod(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("How to mod the game", "Modding your game has become surprisingly easy by now with the help of a **mod manager**", [("Video Tutorial", "If you are on **Windows** or **Linux** you can follow [this Video Tutorial](https://www.youtube.com/watch?v=eSPaKN1cGmo&t=2s) by <@295658850454077443>!"), ("Windows", "Refer to this guide to install **r2modman on Windows**\n[Wiki Page](https://trombone.wiki/#/installing-r2modman)"), ("Linux", "Refer to this guide to install **r2modman on Linux**\n[Wiki Page](https://trombone.wiki/#/installing-r2modman-linux)"), ("MacOS", "As r2modman is not currently available on MacOS, please consider using **Candygoblen123's \"Trombone Champ Mod Manager\"** instead\nInstall instructions and the latest download can be found on this **[GitHub page](https://github.com/Candygoblen123/TromboneChampModManager/)"), ("", "Mods can be found on the **[Thunderstore Page](https://trombone-champ.thunderstore.io)**")])
    await inter.send(embed=emb)

async def howtomigrate(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("How to migrate your stuff", "If you have modded your game **manually** in the past, you will have to take a few steps before you can play", [("Once you have done that:", "- First follow the tutorial outlined in `/howtomod`\n- If you would like to keep your charts, navigate to your **game folder** and copy the **CustomSongs** folder into your **r2modman BepInEx folder**. (See `/paths` for more information)\n- If there are any **mod settings** you would like to keep, do the same with the **config folder**\n- Finally delete the **BepInEx folder, winhttp.dll and doorstop_config.ini** from your **GAME FOLDER**")])
    await inter.send(embed=emb)
    
async def tootbender_command(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("About me...", "This bot is made and maintained by <@898684533719842836>. Should you encounter any issues, please feel free to message him.", [("Features:", "Originally this bot's sole purpose was to parse and post custom charts in <#1024214552151347231>. However this scope has increased massively since then. Besides some small moderation features, Tootbender can now give you information about .tmb files you post, Parse your BepInEx logs, search custom charts, mods and more."), ("Help:", "You can find a full list of commands by typing `/help`"), ("Source Code", "The bot's source code can be found in this [GitHub Repository](https://github.com/Guarde/Tootbender)\n*Disclaimer: I am not a professional programmer, please don't judge me c:*"), ("Feedback", "If you have any feedback or new ideas, please don't hesitate to message me!")])
    await inter.send(embed=emb)

async def howtoaddcharts(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("How to add Custom Charts to your game", "These guides assume that you have **already modded your game**. If you haven't, please **follow the instructions** outlined in `/howtomod`\nCustom Charts can be found on the **[Spreadsheet](https://docs.google.com/spreadsheets/d/1xpoUnHdSJFqOQEK_637-HCECYtJsgK91oY4dRuDMtik)**", [("So how do I do this?", "• Go to your r2modman settings\n• Click 'Browse profile folder'\n• Navigate to ./BepInEx/CustomSongs\n• Unzip any downloaded songs in there. Make sure each song is in a separate folder\n\nIf you have modded your game manually, skip the first two steps and open your game folder instead\n\nFor a more detailed guide please refer to...\n...r2modman: [Wiki Page](https://trombone.wiki/#/installing-r2modman?id=installing-custom-songs-on-r2modman)\n...otherwise: [Wiki Page](https://trombone.wiki/#/installing-songs)")])
    await inter.send(embed=emb)

async def howtochart(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("How to create custom charts", "Making a chart yourself is surpisingly easy. Even more so if you are already familiar with any **Digital Audio Workstation.**", [("The Basics:", "In a nutshell, a chart consists of 3 parts: \n• The **'song.tmb'** which contains all the information about the chart as well as the notes so the game is able to use it. Try opening up a **'song.tmb'** file in a text editor (uses the JSON format)\n• The **'song.ogg'** is the **backing track** for your chart. **Make sure this is longer than the chart iself!**\n• A background. This is optional (but recommended) and can be a **'bg.mp4'**, **'bg.png'** or **'bg.trombackground'** (More on that further down..)"), ("How to make a chart using a **DAW**", "[Wiki Page](https://trombone.wiki/#/creating-charts)\n\n[Video Guide](https://www.youtube.com/watch?v=0k3-Mro8ToY) by <@108020351128104960>"), ("A who the what now?", "While using a **DAW** is very convenient, it can be **overwhelming to beginners** and users who have never used one before. If you feel overwhelmed, consider using **Trombone Charter** instead.\nWhile it might not offer the convenience of a full **DAW**, it's a very simple and **easy-to-use** piece of software if you just got into charting.\n[Github Page](https://github.com/towai/TromboneCharter)"), ("What now?", "Now that you've successfully created a chart it is **technically already playable** ingame, however it is recommended to **add a background**. This can be a **.png**, a **.mp4 **(short videos will loop) or if you feel really fancy you can create a **.trombackground** using Unity."), ("The Trombackground", "Trombackground is a type of **AssetBundle** used by **TrombLoader** to load a Unity scene as a background. \nThis is **entirely optional**, but a fun background can make your chart stand out! \n\nA detailed **guide** on creating a **custom background** can be found here:\n[Github Page](https://github.com/legoandmars/TrombLoaderBackgroundProject/)\n\n**Never be afraid to ask for help, if needed!**")])
    await inter.send(embed=emb)

async def spreadsheet(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("Custom Chart Spreadsheet", "A full **list of custom charts** with download links can be found on the **[Custom Chart Spreadsheet](https://docs.google.com/spreadsheets/d/1xpoUnHdSJFqOQEK_637-HCECYtJsgK91oY4dRuDMtik)**!", [("Search & Sort:", "Use **CTRL + F** to **search for charts** on the spreadsheet\nUse the different **TABS** below the spreadsheet to **sort** by name, creator, artist and more!")])
    file = disnake.File(path.join(globals.helpers_dir, "Images", "lookctrlf.png"), "lookctrlf.png")
    emb.set_image(f"attachment://lookctrlf.png")
    await inter.send(embed=emb, file=file)

async def trombloader(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("The Trombloader Mod", "This mod is required to add custom songs to your game.")
    req = await globals.session.get("https://thunderstore.io/api/experimental/package/TromboneChamps/TrombLoader/")
    if req.ok:
        data = await req.text()
        tromb = json.loads(data)
        emb.add_field("Latest Version:", tromb['latest']['version_number'], inline=False)
        emb.set_thumbnail(tromb['latest']['icon'])
    emb.add_field("Download it here:", "(Installation via **r2modman** recommended)\n[Thunderstore Page](https://trombone-champ.thunderstore.io/package/TromboneChamps/TrombLoader/)", inline=False)
    emb.add_field("Dependencies:", "(Installed automatically with **r2modman**)\n[BaboonAPI](https://trombone-champ.thunderstore.io/package/TromboneChamps/BaboonAPI) | [FSharp Core](https://trombone-champ.thunderstore.io/package/TromboneChamps/FSharp_Core/) | [Newtonsoft JSON](https://trombone-champ.thunderstore.io/package/TromboneChamps/Newtonsoft_Json/)", inline=False)
    await inter.send(embed=emb)

async def r2modman(inter:disnake.ApplicationCommandInteraction):
    emb = embed_builder("r2modman", "The mod manager used to install mods from Thunderstore")
    req = await globals.session.get("https://thunderstore.io/api/experimental/package/ebkr/r2modman/")
    if req.ok:
        data = await req.text()
        r2m = json.loads(data)
        emb.add_field("Latest Version:", r2m['latest']['version_number'], inline=False)
        emb.set_thumbnail(r2m['latest']['icon'])
    emb.add_field("Links:", "[Thunderstore Page (Download)](https://thunderstore.io/package/ebkr/r2modman/) | [GitHub Repo (Source Code)](https://github.com/ebkr/r2modmanPlus)", inline=False)
    await inter.send(embed=emb)

async def randomchart(inter:disnake.ApplicationCommandInteraction, rated):
    c = globals.all_charts.get_random(rated)
    emb = embed_builder(c["name"], globals.all_charts.to_discord(c))
    await inter.send(embed=emb)
    
async def refresh_chart_list(inter:disnake.ApplicationCommandInteraction):
    await globals.all_charts.get_songs()
    
    

fullmodlist = modsearch_update_list()