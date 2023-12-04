import disnake, json
from Helpers import globals
from Curation import packs_static, packs_fileman

# Helper Functions
async def send_embed(inter:disnake.ApplicationCommandInteraction, title:str, description:str):
    emb = disnake.Embed(title = title, description = description, color = packs_static.color)
    await inter.edit_original_message(embed=emb)

async def get_thread_info(chan:disnake.Thread):
    title = chan.name
    async for m in chan.history(limit = 1, oldest_first=True):
        first_message = m
    return title, first_message

def pack_message(chart_pack:packs_static.pack):
    return f"**by <@{chart_pack.curator_id}> | [{len(chart_pack.charts)} Charts]**\n{chart_pack.description}\n\n[Spreadsheet](<{globals.googleapi.get_pack_url(chart_pack.name)}>)"

async def tt_create_pack(chart_pack:packs_static.pack):
    url = "https://toottally.com/api/packs/new/"
    data = chart_pack.to_request_data(globals.settings.upload.tt_api_key)
    return await make_post_request(url, data)
        

async def tt_update_pack(chart_pack:packs_static.pack):
    url = f"https://toottally.com/api/packs/{chart_pack.name}/change/"
    data = chart_pack.to_request_data(globals.settings.upload.tt_api_key)
    return await make_post_request(url, data)

async def tt_delete_pack(chart_pack:packs_static.pack):
    url = f"https://toottally.com/api/packs/{chart_pack.name}/remove/"
    data = {"api_key": globals.settings.upload.tt_api_key}
    return await make_post_request(url, data)
    
async def make_post_request(url:str, data:dict()):
    r = await globals.session.post(url, json=data)
    if r.ok:
       return
    return f"[{r.status}] {r.reason}"
