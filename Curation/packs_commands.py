import disnake, json, re, asyncio
import os
from Helpers import globals
from Curation import packs_static, packs_helpers, packs_fileman

# Commands
async def create_pack(inter:disnake.ApplicationCommandInteraction, name:str):
    await inter.response.defer()
    #Check if used in correct channel
    if inter.channel.type.name != "public_thread" or inter.channel.parent_id != int(globals.settings.curation.curator_forum_channel):
        await packs_helpers.send_embed(inter, packs_static.header, "This command may only be used from a thread in the curator forum")
        return

    #Check thread is info thread
    if inter.channel.is_pinned():
        await packs_helpers.send_embed(inter, packs_static.header, "This command can not be used in the pinned thread of a forum!")
        return

    #Check for empty string and whitespaces
    if name == None or name.strip() == "":
        await packs_helpers.send_embed(inter, packs_static.header, "Please provide a name for this chart pack.")
        return    
    
    #Forbidden Chart Names
    if name in ["new", "template"]:
        await packs_helpers.send_embed(inter, packs_static.header, f"\"{name}\" is not allowed as a chart pack name!")
        return

    #Validate Alphanum, _, -
    if re.fullmatch(r"[0-9a-zA-Z_-]+", name) == None:
        await packs_helpers.send_embed(inter, packs_static.header, "The pack name may only consist of the characters ` a-Z `, ` 0-9 `, ` - ` and ` _ `")
        return
    
    #Check if thread already in use
    thread_id = inter.channel_id
    if thread_id in list(packs_static.threads.keys()):
        packname = packs_static.threads[thread_id]
        await packs_helpers.send_embed(inter, packs_static.header, f"This thread is already used for the chart pack \"{packname}\".")
        return

    #Check for unique pack name
    if name in list(packs_static.packs.keys()):
        await packs_helpers.send_embed(inter, packs_static.header, f"A chart pack with the name \"{name}\" already exists. Please choose a different name.")
        return
    
    chan_name, chan_firstmessage = await packs_helpers.get_thread_info(inter.channel)
    
    #Build pack object
    new_pack = packs_static.pack(name, thread_id)
    new_pack.title = chan_name
    new_pack.curator_id = chan_firstmessage.author.id
    new_pack.description = chan_firstmessage.content
        

    #Send Messages & Write to file
    pub_forum = await inter.client.fetch_channel(globals.settings.curation.public_forum_channel)
    thread, threadmess = await pub_forum.create_thread(name=new_pack.title, content = "Placeholder Text")
    new_pack.target_thread = thread.id
    new_pack.message = threadmess.id
    new_pack.add_to_dict()
    packs_fileman.save_packs_file()
    globals.googleapi.create_pack_page(name, new_pack.title)
    await threadmess.edit(packs_helpers.pack_message(new_pack))

    #Send to TootTally:
    tt_error = await packs_helpers.tt_create_pack(new_pack)
    if not tt_error == None:
        await packs_helpers.send_embed(inter, packs_static.header, f"Received the following error when posting to TootTally: \n{tt_error}\n\nAll other actions were executed successfully")
        return
    await packs_helpers.send_embed(inter, packs_static.header, f"Successfully created chart pack \"{new_pack.title}\".\n\n{pub_forum.jump_url}")

async def delete_pack(inter:disnake.ApplicationCommandInteraction):
    await inter.response.defer()
    #Check if used in correct channel
    if inter.channel.type.name != "public_thread" or inter.channel.parent_id != int(globals.settings.curation.curator_forum_channel):
        await packs_helpers.send_embed(inter, packs_static.header, "This command may only be used from a thread in the curator forum")
        return

    #Check thread is info thread
    if inter.channel.is_pinned():
        await packs_helpers.send_embed(inter, packs_static.header, "This command can not be used in the pinned thread of a forum!")
        return
    
    #Check if thread already in use
    thread_id = inter.channel_id
    if not thread_id in list(packs_static.threads.keys()):
        packname = packs_static.threads[thread_id]
        await packs_helpers.send_embed(inter, packs_static.header, f"There is no pack associated with this forum thread.")
        return
    
    #Confirmation
    await packs_helpers.send_embed(inter, "Are you sure you want to do this?", "**Deleting a chart pack is irreversible**\n(Action will be cancelled in 10 seconds.)")
    mess = await inter.original_response()
    await mess.add_reaction("✅")
    
    def reactcheck(reaction:disnake.Reaction, user:disnake.User):
        return user == inter.author and str(reaction.emoji) == "✅"
    try:
        reaction, user = await inter.bot.wait_for('reaction_add', timeout=10.0, check=reactcheck)

    
    except asyncio.TimeoutError:
        emb = disnake.Embed(title=packs_static.header, description=f"Pack deletion was cancelled", color=packs_static.color)
        await inter.edit_original_message(embed=emb)
        return
    
    finally:        
        await mess.clear_reactions()

    packname = packs_static.threads.pop(thread_id)    
    target = await packs_static.packs[packname].get_target_thread(inter.client)
    await target.delete(reason="Thread pack was deleted")
    deleted_pack = packs_static.packs.pop(packname)
    packs_fileman.save_packs_file()
    globals.googleapi.delete_pack_page(packname)
 
    emb = disnake.Embed(title=packs_static.header, description=f"Chart pack \"{packname}\" was deleted.", color=packs_static.color)

    #Send to TootTally:
    tt_error = await packs_helpers.tt_delete_pack(deleted_pack)
    if not tt_error == None:
        emb.add_field("Exceptions:", f"Received the following error when posting to TootTally: \n{tt_error}\n\nAll other actions were executed successfully")

    await inter.edit_original_message(embed=emb)

async def update_message(inter:disnake.ApplicationCommandInteraction):
    await inter.response.defer()
    #Check if used in correct channel
    if inter.channel.type.name != "public_thread" or inter.channel.parent_id != int(globals.settings.curation.curator_forum_channel):
        await packs_helpers.send_embed(inter, packs_static.header, "This command may only be used from a thread in the curator forum")
        return

    #Check thread is info thread
    if inter.channel.is_pinned():
        await packs_helpers.send_embed(inter, packs_static.header, "This command can not be used in the pinned thread of a forum!")
        return
    
    #Check if pack exists
    thread_id = inter.channel_id
    if not thread_id in list(packs_static.threads.keys()):
        await packs_helpers.send_embed(inter, packs_static.header, f"There is no pack associated with this forum thread. Please create a chart pack first")
        return

    emb = disnake.Embed(title=packs_static.header, description=f"Updating Pack Message...", color=packs_static.color)
    packname = packs_static.threads.pop(thread_id)    
    mess: disnake.Message = await packs_static.packs[packname].get_message(inter.client)
    await mess.edit(packs_helpers.pack_message(packs_static.packs[packname]))

    await inter.send(embed=emb)

async def add_chart(inter:disnake.ApplicationCommandInteraction, args:str):
    await inter.response.defer()
    #Check if used in correct channel
    if inter.channel.type.name != "public_thread" or inter.channel.parent_id != int(globals.settings.curation.curator_forum_channel):
        await packs_helpers.send_embed(inter, packs_static.header, "This command may only be used from a thread in the curator forum")
        return

    #Check thread is info thread
    if inter.channel.is_pinned():
        await packs_helpers.send_embed(inter, packs_static.header, "This command can not be used in the pinned thread of a forum!")
        return
    
    #Check if pack exists
    thread_id = inter.channel_id
    if not thread_id in list(packs_static.threads.keys()):
        await packs_helpers.send_embed(inter, packs_static.header, f"There is no pack associated with this forum thread. Please create a chart pack first")
        return
    packname = packs_static.threads[thread_id]

    reg = r"[0-9]+"
    matches = re.findall(reg, args)
    if len(matches) == 0:
        await packs_helpers.send_embed(inter, packs_static.header, "No valid chart ID was entered. Please enter a single TootTally Chart ID or a list of Chart IDs separated by spaces, commas, or whatever else you want")
        return

    #Try to get charts
    url="https://toottally.com/api/songs/$(ID)/"
    fails = []
    successes = []
    google_queue = []
    for m in matches:
        #Ignore duplicates
        if packs_static.packs[packname].has_chart(m):
            fails.append(f"- `{m}` - Chart is already in this pack")
            continue
        r = await globals.session.get(url.replace("$(ID)", m), allow_redirects=True)
        #Catch Request Error
        if not r.ok:
            fails.append(f"- `{m}` - API Error ({r.status})")
            continue
        response = json.loads(await r.read())
        #Check if ID returned a result
        if response["count"] == 0:
            fails.append(f"- `{m}` - Unknown Chart ID")
            continue
        c = packs_static.pack_chart().from_toottally(response)
        #Check if DL exists
        if c.download == None:
            fails.append(f"- `{m}` - No TootTally download link!")
            continue        
        packs_static.packs[packname].add_chart(c)
        successes.append(f"- `{m}` - \"{c.title}\" was added to the chart pack")
        google_queue.append(c)
    packs_static.packs[packname].add_to_dict()
    packs_fileman.save_packs_file()
    emb = disnake.Embed(title=packs_static.header, description="", color=packs_static.color)
    if len(successes) > 0:
        success_message = "\n".join(successes)
        if len(success_message) > 1024:
            success_message = success_message[:1020] + "..."
        globals.googleapi.add_pack_charts(packname, google_queue, len(list(packs_static.packs[packname].charts.keys())))
        emb.description = f"Successfully fetched {len(successes)} charts!"
        emb.add_field("Charts added:", success_message, inline=False)
        mess: disnake.Message = await packs_static.packs[packname].get_message(inter.client)
        await mess.edit(packs_helpers.pack_message(packs_static.packs[packname]))
    else:
        emb.description = f"Failed to fetch any charts from given IDs"


    if len(fails) > 0:
        fail_message = "\n".join(fails)
        if len(fail_message) > 1024:
            fail_message = fail_message[:1020] + "..."
        emb.add_field("Failed:", fail_message, inline=False)
        
    #Send to TootTally:
    if len(successes) > 0:
        tt_error = await packs_helpers.tt_update_pack(packs_static.packs[packname])
        if not tt_error == None:
            emb.add_field("Exceptions:", f"Received the following error when posting to TootTally: \n{tt_error}\n\nAll other actions were executed successfully")
    await inter.edit_original_message(embed=emb)
        
    
async def remove_chart(inter:disnake.ApplicationCommandInteraction, args:str):
    await inter.response.defer()
    #Check if used in correct channel
    if inter.channel.type.name != "public_thread" or inter.channel.parent_id != int(globals.settings.curation.curator_forum_channel):
        await packs_helpers.send_embed(inter, packs_static.header, "This command may only be used from a thread in the curator forum")
        return

    #Check thread is info thread
    if inter.channel.is_pinned():
        await packs_helpers.send_embed(inter, packs_static.header, "This command can not be used in the pinned thread of a forum!")
        return
    
    #Check if pack exists
    thread_id = inter.channel_id
    if not thread_id in list(packs_static.threads.keys()):
        await packs_helpers.send_embed(inter, packs_static.header, f"There is no pack associated with this forum thread. Please create a chart pack first")
        return
    packname = packs_static.threads[thread_id]

    reg = r"[0-9]+"
    matches = re.findall(reg, args)
    if len(matches) == 0:
        await packs_helpers.send_embed(inter, packs_static.header, "No valid chart ID was entered. Please enter a single TootTally Chart ID or a list of Chart IDs separated by spaces, commas, or whatever else you want")
        return

    if len(matches) > 5:
        await packs_helpers.send_embed(inter, packs_static.header, "Due to google API limitations, only up to 5 charts may be deleted at a time")
        return

    fails = []
    successes = []
    google_queue = []
 
    for m in matches:
        #Skip non-existing
        if not packs_static.packs[packname].has_chart(m):
            fails.append(f"- `{m}` - Chart was not part of this pack")
            continue
        c = packs_static.packs[packname].remove_id(m)
        successes.append(f"- `{m}` - \"{c.title}\" was removed from the chart pack")
        google_queue.append(m)
    
    packs_static.packs[packname].add_to_dict()
    packs_fileman.save_packs_file()
    emb = disnake.Embed(title=packs_static.header, description="", color=packs_static.color)
    if len(successes) > 0:
        success_message = "\n".join(successes)
        if len(success_message) > 1024:
            success_message = success_message[:1020] + "..."
        globals.googleapi.remove_pack_charts(packname, google_queue)
        emb.description = f"Successfully removed {len(successes)} charts!"
        emb.add_field("Charts added:", success_message, inline=False)
        mess: disnake.Message = await packs_static.packs[packname].get_message(inter.client)
        await mess.edit(packs_helpers.pack_message(packs_static.packs[packname]))
    else:
        emb.description = f"Failed to match any of the given IDs to charts in the pack"
    if len(fails) > 0:
        fail_message = "\n".join(fails)
        if len(fail_message) > 1024:
            fail_message = fail_message[:1020] + "..."
        emb.add_field("Failed:", fail_message, inline=False)
        
    #Send to TootTally:
    if len(successes) > 0:
        tt_error = await packs_helpers.tt_update_pack(packs_static.packs[packname])
        if not tt_error == None:
            emb.add_field("Exceptions:", f"Received the following error when posting to TootTally: \n{tt_error}\n\nAll other actions were executed successfully")
    await inter.edit_original_message(embed=emb)

packs_fileman.reload_packs_file()