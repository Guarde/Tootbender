import json, disnake, asyncio, aiohttp
from dateutil import parser
from math import ceil
from Helpers import globals

#https://toottally.com/api/search/?page=${page}&song_name=${songName}&min_diff=${minDifficulty}&max_diff=${maxDifficulty}&official=${official}&rated=${rated}`

async def command(self, inter:disnake.ApplicationCommandInteraction, search):
    url = f"https://toottally.com/api/search/?song_name={search}&page_size=9"
    status, response = await chart_search(url)
    emb = None

    if not status:
        emb = disnake.Embed(title="API ERROR", description=f"API Request exited with error [{response.status}] {response.reason}", color=disnake.Color.red())
        await inter.send(embed=emb)
        return

    count, prev_url, next_url, charts = response
    pages = ceil(count/9)
    if pages > 1:
        emb = disnake.Embed(title=f"Search Results for \"{search}\"", description=f"*Found {count} charts across {pages} page(s)*")
    elif count == 0:
        emb = disnake.Embed(title=f"Search Results for \"{search}\"", description=f"*No charts found for given search term*")
    else:
        emb = disnake.Embed(title=f"Search Results for \"{search}\"", description=f"*Found {count} charts*")
    emb = make_results(charts, emb)
    if pages > 1:
        emb.set_footer(text=f"Powered by TootTally | Page 1 of {pages}")
    else:
        emb.set_footer(text=f"Powered by TootTally")
    await inter.send(embed=emb)
    if next_url or prev_url:
       await add_reactions(self, inter, next_url, prev_url, 1)
    return

async def add_reactions(self, inter:disnake.ApplicationCommandInteraction, next_url, prev_url, page):
    message = await inter.original_response()
    message = disnake.utils.get(self.cached_messages, id=message.id)
    reacts = []
    moji = ""
    if prev_url:
        await message.add_reaction("⬅️")
        reacts.append("⬅️")
    if next_url:
        await message.add_reaction("➡️")
        reacts.append("➡️")

    def reactcheck(reaction:disnake.Reaction, user:disnake.User):
        return user == inter.author and str(reaction.emoji) in reacts

    try:
        reaction, user = await self.wait_for('reaction_add', timeout=30.0, check=reactcheck)
    
    except asyncio.TimeoutError:
        await message.clear_reactions()
        return
    else:
        for re in message.reactions:
            if not str(re.emoji) in reacts:
                continue
            async for us in re.users():
                if inter.author == us:
                    moji = str(re.emoji)
                    break
        if moji == "➡️":
            results = await chart_search(next_url)
            page += 1
        elif moji == "⬅️":
            results = await chart_search(prev_url)
            page += -1
        await message.clear_reactions()

        emb = None

        if not results[0]:
            emb = disnake.Embed(title="API ERROR", description="Currently unable to reach the TootTally API")
            await message.edit(embed=emb)
            return

        count, prev_url, next_url, charts = results[1]

        emb = message.embeds[0]
        emb = make_results(charts, emb)
        emb.set_footer(text=f"Powered by TootTally | Page {page} of {ceil(count/9)}")
        await message.edit(embed=emb)
        if next_url or prev_url:
            await add_reactions(self, inter, next_url, prev_url, page)

async def chart_search(url:str):
    search = await globals.session.get(url) #https://toottally.com/api/search/?song_name={name}
    if not search.ok:
        return False, search
    data = await search.text()
    result = json.loads(data)
    charts = sorted(result["results"], key=lambda item: item["play_count"]*-1)
    return True, (result["count"], result["previous"], result["next"], charts)

def make_results(charts:dict, emb:disnake.Embed):    
    emb.clear_fields()
    for chart in charts:
        rated = "❌"
        dl = ""
        if chart["mirror"] != None:
            dl = f" | [Mirror]({chart['mirror']})"
        elif chart["download"] != None:
            dl = f" | [Download]({chart['download']})"
        if chart['is_rated']:
            rated = "✅"
        date = round(parser.parse(chart["uploaded_at"]).timestamp())
        emb.add_field(name="__" + chart["name"] + "__", value=f"*by {chart['author']}*\n**Charter:** {chart['charter']}\n **Diff.:** {round(chart['difficulty'], ndigits=1)} | **Rated:** {rated}\n<t:{date}:R>\n[Leaderboard]({'https://toottally.com/song/' + str(chart['id'])}){dl}")
    return emb

async def chart_search_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if user_input in [None, ""]:
        return []
    results = globals.all_charts.search(user_input)

    #Create Autofill List
    autofill = []
    for fill in results:
        fill = fill["name"]
        #Limit Result Length
        if len(fill) > 100:
            fill = fill[0:90] + "..."
        autofill.append(fill)
    return autofill[:min(len(autofill), 25)]