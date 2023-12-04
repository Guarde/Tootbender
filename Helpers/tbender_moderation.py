import disnake, asyncio
from datetime import datetime
from Helpers.tbender_extras import botLog
from Helpers.globals import settings

tracker = {} #{user_id: [timestamp: message, timestamp: message]}
notif_ratelimit = {}

async def handle_incoming_message(message:disnake.Message):
    global tracker, notif_ratelimit
    update_tracker()
    track_message(message)
    result =  check_messages(message.author)
    if result == True:
        return True

    mod_chan = await message.guild.fetch_channel(settings.moderation.staff_channel_id)
    try:
        mention = message.guild.get_role(int(settings.general.mod_roles[0])).mention
    except Exception:
        mention = f"<@{settings.general.owners[0]}>"
    messagetexts = []
    for m in tracker[message.author.id]:
        messagetexts.append(m[2].clean_content)
    emb = disnake.Embed(title="Spam Filter", description=f"Potential spam detected by user {message.author.mention} ({message.author.id})")
    emb.add_field(name="Reason", value = f"User exceeded the rate limit of **{settings.moderation.rate_limit_channels} channels** across **{settings.moderation.rate_limit_time} seconds.**", inline=False)
    emb.add_field(name="Messages", value = "- " + "\n- ".join(messagetexts), inline=False)

    if settings.moderation.passive_filter:
        emb.add_field(name="Actions", value = "No actions were taken", inline=False)
        botLog("info", f"Potential spam detected by user {message.author.mention} ({message.author.id}). No actions were taken")

    else:
        try:
            await message.author.timeout(duration=int(settings.moderation.timeout_duration), reason="Spam Filter")
            emb.add_field(name="Actions", value = f"Messages deleted and user timed out for **{settings.moderation.timeout_duration} seconds**", inline=False)
        except Exception as e:
            botLog("warning", "Unable to time out user, likely lacking permissions...")
            emb.add_field(name="Actions", value = f"Messages deleted. (Unable to time out user, likely lacking permissions...)", inline=False)
        for m in tracker[message.author.id]:
            try:
                await m[2].delete()
            except Exception:
                pass
        botLog("info", f"Potential spam detected by user {message.author.mention} ({message.author.id}). Deleted Messages and timed out user")

    
    if not message.author.id in list(notif_ratelimit.keys()) or datetime.timestamp(datetime.now()) - notif_ratelimit[message.author.id] > 10:
        notif_ratelimit[message.author.id] = datetime.timestamp(datetime.now())
        await mod_chan.send(mention, embed = emb)
    return False


def track_message(message:disnake.Message):    
    global tracker
    if not message.author.id in list(tracker.keys()):
        tracker[message.author.id] = []
    tracker[message.author.id].append((datetime.timestamp(datetime.now()), message.channel.id, message))

def update_tracker():
    global tracker
    now = datetime.timestamp(datetime.now())
    lookup = tracker
    for u in list(lookup.keys()):
        tracker[u] = [x for x in lookup[u] if now - x[0] < int(settings.moderation.rate_limit_time)]
        if tracker[u] == []:
            tracker.pop(u)

def check_messages(user:disnake.User):
    messages = tracker[user.id]
    channels = []
    for m in messages:
        if not m[1] in channels:
            channels.append(m[1])
    if len(channels) >= int(settings.moderation.rate_limit_channels):
        return False
    return True