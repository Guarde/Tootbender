from hashlib import sha256
import re, disnake, json, shutil, os, time, cv2, math, logging
from Helpers.tbender_song import Song
from pyunpack import Archive
from Helpers.tbender_validate import validate_song
from Helpers import globals
from Helpers.globals import botLog

async def handle_submission(self, message:disnake.Message, db, google):
    botLog("info", "Received new message from " + message.author.display_name)
    await message.add_reaction("⌛")
    maxsize = 0
    for triple in self.permits:
        user, size, mess = triple
        if message.author.id == user.id:
            maxsize = size
            break
    #Get download link
    dl = await verify_download(message)
    if not dl:
        return

    #Clear folder just to be sure
    clear_folder()

    #Download from google
    if dl[0] == "googledrive":
        status = await google.download_file(dl[1], maxsize)

    #Download via direct link
    else:
        status = await download_common(dl[1], maxsize)
    if status == "toobig":
        reject = globals.settings.lang.rejects.filesize.replace("$VAR", globals.settings.upload.max_file_size)
        await reject_song(message, reject)
        return
    if not status == True:
        reject = globals.settings.lang.rejects.download_failed.replace("$VAR", f"[{status[0]}] {status[1]}")
        await reject_song(message, reject)
        return
    botLog("info", "File downloaded")

    #Extract song
    if not await extract():
        await reject_song(message, globals.settings.lang.rejects.invalid_zip)
        return
    botLog("info", "File extracted")

    #Get file structure
    fstruct = await verify_structure(message)
    if globals.settings.verification.file_structure and not fstruct:
        await reject_song(message, globals.settings.lang.rejects.file_structure)
        return

    #Get tmb
    tmb, hash = fetch_tmb(fstruct)
    if tmb == None:
        await reject_song(message, hash)
        return

    #Find video
    video = None
    if globals.settings.upload.youtube:
        video = find_videos(message)

    #Create song
    files = fstruct[1]
    try:
        song = Song(tmb, message, video, dl[1], files, hash)
    except Exception as e:
        botLog("ERROR", f"The following exception was caught when trying to create the song object:\n{e}")
        if not e.args[0] == "MissingKeys":
            await reject_song(message, globals.settings.lang.rejects.other_error + "\n" + str(e))
            return
        await reject_song(message, globals.settings.lang.rejects.missing_keys.replace("$VAR", ", ".join(e.args[1])))
        return
    botLog("info", "Song built!")

    if "bg.png" in fstruct[1]:
        song.bgpath = os.path.join(fstruct[0], "bg.png")
    elif "bg.mp4" in fstruct[1]:
        song.bgpath = os.path.join(fstruct[0], "bg.mp4")

    #Validate song
    val = validate_song(song, message, fstruct)
    if val:
        await reject_song(message, val)
        return

    #Confirm unique trackref
    trackref = song.tmb["trackRef"]
    if globals.settings.verification.unique_trackref and not db.check_trackref(trackref):
        await reject_song(message, globals.settings.lang.rejects.trackref.replace("$VAR", trackref))
        return
    botLog("info", "Song validation successful!")

    #Filesize Prompt
    tt_size_limit = min(25 + (song.duration / 20), 50.0)
    if song.filesize > tt_size_limit:
        botLog("info", "File too large for TootTally mirror. Awaiting confirmation...")
        conf = await do_size_confirm(self, message, song, tt_size_limit)
        if not conf:
            botLog("info", "Confirmation did not pass. Aborting...")
            return
        
    botLog("info", "TootTally mirror size check passed")

    #Post on Discord
    await post_song(self, message, song)
    if maxsize > 0:
        try:
            await mess.delete()
        except Exception as e:
            pass    
        try:
            self.permits.remove((user, maxsize, mess))
        except ValueError:
            pass
    if not globals.settings.general.debug == True:
        #Post to TootTally
        await tt_post(globals.settings.upload.tt_api_key, song.as_dict())
        
        #Add to Spreadsheet
        google.post_spreadsheet(song)

        #Add to Database
        db.post_chart(song)

    #Clear temp folder
    clear_folder()

async def do_size_confirm(self, message:disnake.Message, song:Song, tt_size_limit:float):
    size_emb = disnake.Embed(title="Hold on a second!", description=f"**Your upload is too big to recieve a TootTally mirror!**\nAt the length of `{song.duration_string}` your file may not be larger than `{round(tt_size_limit,ndigits=2)} MB`.\nClick the ✅ to upload anyway.\n*(This action will be cancelled in 10 seconds.)*")
    mess = await message.reply(embed=size_emb, delete_after=20)
    await mess.add_reaction("✅")
    
    def reactcheck(reaction:disnake.Reaction, user:disnake.User):
        return user == message.author and str(reaction.emoji) == "✅"
    try:
        reaction, user = await self.wait_for('reaction_add', timeout=10.0, check=reactcheck)

    
    except asyncio.TimeoutError:
        size_emb = disnake.Embed(title="Upload Cancelled", description=f"The upload has been cancelled. (User didn't react in time)")
        await message.delete()
        await mess.edit(embed=size_emb)
        return False
    
    finally:        
        await mess.clear_reactions()
        
    size_emb = disnake.Embed(title="Uploading...", description=f"Upload confirmed. This chart will not receive a mirror.")
    await mess.edit(embed=size_emb)
    return True

async def post_song(self, message:disnake.Message, song:Song):
    attachment = False
    comment = disnake.utils.remove_markdown(message.clean_content)
    if not globals.settings.general.allow_links:
        urls = findUrls(comment)
        for url in urls:
            comment = comment.replace(url, "")
    else:
        if song.download:
            comment = comment.replace(song.download, "")
        if song.video:
            comment = comment.replace(song.video, "")

    embed = song.to_embed(comment)
    charts = message.guild.get_channel(int(globals.settings.general.charts_channel))
    if not globals.settings.general.debug == True:
        charts2 = self.get_channel(int(globals.settings.general.charts_channel2))
    botLog("info", f"Submitting \"{song.name}\"!")
    buttons = [disnake.ui.Button(style=disnake.ButtonStyle.success, label="Download Chart", url = song.download)]
    if song.video:
        thumburl = get_thumbnail(song.video)
        embed.set_image(thumburl)
        buttons.append(disnake.ui.Button(style=disnake.ButtonStyle.danger, label="Preview Video", url = song.video))
    elif "bg.png" in song.bgpath:
        file = disnake.File(song.bgpath, "bg.png")
        attachment = "bg.png"
    elif "bg.mp4" in song.bgpath:
        video_to_png(song.bgpath)
        time.sleep(0.5)
        file = disnake.File(os.path.join(globals.temp_dir, "preview.png"), "preview.png")
        attachment = "preview.png"
    timest = song.timestamp.strftime("Posted on %b %d, %Y at %H:%M")
    embed.set_footer(text = timest)
    if attachment:                       
        embed.set_image(f"attachment://{attachment}")
        msg = await charts.send(file = file, embed = embed, components=buttons)
    else:
        msg = await charts.send(embed = embed, components=buttons)
    if not globals.settings.general.debug == True:
        await charts2.send(embed = embed)
    await message.clear_reactions()
    await message.add_reaction("✅")
    await msg.add_reaction("♥")
    if globals.settings.general.do_threads:
        thread = await msg.create_thread(name = song.name + " Discussion")
        await thread.add_user(message.author)

async def tt_post(api_key, song:dict):
    url = "https://toottally.com/api/upload/"
    data = {"song": json.dumps(song), "api_key": api_key}
    req = await globals.session.post(url, data=data)
    if not req.ok:
        message = f"POST request returned error [{req.status}] {req.reason}"
        botLog("warning", message)
    else:
        botLog("info", "Song successfully posted to TootTally")

def video_to_png(filename):
    cam = cv2.VideoCapture(filename)
    length = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    cam.set(cv2.CAP_PROP_POS_FRAMES, math.floor(length/2))
    ret,frame = cam.read()
    if ret:
        name = os.path.join(globals.temp_dir, "preview.png")
        cv2.imwrite(name, frame)
    cam.release()
    cv2.destroyAllWindows()
    return

def fetch_tmb(fstruct:list):
    tmb = None
    h = None
    tmbroot = fstruct[0]
    try:
        with open(os.path.join(tmbroot, "song.tmb"), mode="rb") as f:
            r = f.read()
            h = sha256(r).hexdigest()
            tmb = json.loads(r.decode("utf-8"))
            botLog("info", f"Filehash: {h}")
        return (tmb, h)
    except Exception as e:
        err = f"The following exception was caught when trying to import the .tmb:\n{e}"
        botLog("ERROR", err)
        return (None, err)

async def extract():
    if not os.path.isdir(globals.temp_dir):
        os.mkdir(globals.temp_dir)
    try:
        Archive(os.path.join(globals.temp_dir, "song.zip")).extractall(directory=globals.temp_dir)
        os.remove(os.path.join(globals.temp_dir, "song.zip"))
        return True
    except Exception as e:
        botLog("ERROR", f"The following exception was caught when trying to extract the archive:\n{e}")
        return

async def verify_structure(message):
    songdir = None
    for root, dirs, files in os.walk(globals.temp_dir):
        if root == globals.temp_dir:
            if len(dirs) == 1:
                songdir = dirs[0]
                continue
            if globals.settings.verification.file_structure:
                return False
            files = await check_missing_files(message, files)
            if files:
                return [root, files, None]
        else:
            if songdir and root.endswith(songdir):
                files = await check_missing_files(message, files)
                if files:
                    return [root, files, songdir]


async def check_missing_files(message, files):
    if not "song.tmb" in files or not "song.ogg" in files:
        await reject_song(message, globals.settings.lang.rejects.missing_files)
        return
    if not globals.settings.verification.background:
        return files
    if not r"bg.(trombackground|mp4|png)".find(" ".join(files)):
        await reject_song(message, globals.settings.lang.rejects.missing_files)
    return files

def clear_folder():
    try:
        shutil.rmtree(globals.temp_dir)
    except Exception as e:
        botLog("ERROR", f"The following exception was caught when trying to clear the folder:\n{e}")
    try:
        os.mkdir(globals.temp_dir)
    except Exception as e:
        botLog("ERROR", f"The following exception was caught when trying to create a new folder:\n{e}")
        pass

async def download_common(url:str, maxsize:int=0):
        url  = url.replace("dl=0", "dl=1")
        try:
            r = await globals.session.get(url, allow_redirects=True)
            #Check filesize before saving
            filesize = len(await r.read())/1000000
            #Get maximum
            maxsize = max(int(globals.settings.upload.max_file_size), maxsize)
            if filesize > maxsize:
                return "toobig"
            with open(os.path.join(globals.temp_dir, "song.zip"), 'wb') as f:
                f.write(await r.read())
            return True
        except Exception as e:
            botLog("ERROR", f"The following exception was caught when trying to download the (common) file:\n{e}")
            return False

async def verify_download(message:disnake.Message):
    download = None
    try:
        download = await verify_services(message)
    except Exception as e:
        if e.args[1] == "NoDownload":
            botLog("info", "Message rejected for reason: No Download provided!")
        elif e.args[1] == "TooManyDownloads":
            botLog("info", "Message rejected for reason: Too many downloads provided!")
        else:
            botLog("warning", "An unexpected error occured while attempting to fetch the download link!")
        return None
    return download

async def verify_services(message:disnake.Message):
    links = findUrls(message.content)    
    services = []
    service_urls = []
    #List allowed services
    if globals.settings.upload.dropbox:
        services.append("Dropbox")
        service_urls.append(["dropbox", "www.dropbox.com"])
    if globals.settings.upload.googledrive:
        services.append("Google Drive")
        service_urls.append(["googledrive", "drive.google.com/file/d/"])
    if globals.settings.upload.discord_uploads:
        for att in message.attachments:
            links.append(att.url)
        services.append("Discord")
        service_urls.append(["discord", "cdn.discordapp.com"])

    #Check if services are empty
    if len(services) == 0:
        botLog("warning", "Unable to process upload. All upload services are disabled in the config!")
        return []
    
    matches = []

    #Combine direct download links
    for l in links:
        for serv, url in service_urls:
            if not url in l:
                continue
            if not serv in ["discord", "dropbox"]:
                matches.append((serv, l))
                continue
            matches.append((serv, l))
    if len(matches) == 0:
        reject = ""
        if "Discord" in services:
            if len(services) == 1:
                reject = globals.settings.lang.rejects.no_file_upload
            else:
                reject = globals.settings.lang.rejects.no_file_upload_link.replace("$VAR", ", ".join(services))
        else:
            reject = globals.settings.lang.rejects.no_file_link.replace("$VAR", ", ".join(services))
        await reject_song(message, reject)
        raise Exception("SongRejected", "NoDownload")

    if len(matches) > 1:
        await reject_song(message, globals.settings.lang.rejects.too_many_links)
        raise Exception("SongRejected", "TooManyDownloads")
    botLog("info", "Download link check passed!")
    return matches[0]

def find_videos(message:disnake.Message):
    links = findUrls(message.content)

    matches = []
    for l in links:
        for url in ["youtube.com/watch", "youtu.be/"]:
            if not url in l:
                continue
            matches.append(l)

    if len(matches) == 0:
        botLog("info", "No video attached!")
        return

    else:
        botLog("info", "Video link found!")
        return matches[0]

def get_thumbnail(video:str):    
    match = re.search(r"youtube\.com\/.*v=([^&]*)", video)
    if not match:        
        match = re.search(r"youtu\.be\/([^&]*)", video)
    if match:
        return f"https://img.youtube.com/vi/{match.group(1)}/maxresdefault.jpg"

async def reject_song(message:disnake.Message, reason:str):
    emb = disnake.Embed(title=f"[@{message.author.name}] Submission Failed!", description=reason, color=disnake.Colour.red())
    botLog("info", f"Rejecting song with reason: \"{reason}\"")
    clear_folder()
    if globals.settings.general.dm_rejections:
        if not message.author.dm_channel:
            await message.author.create_dm()
        await message.author.dm_channel.send(embed=emb)
    else:
        try:
            time = int(globals.settings.general.reject_delete_timer)
        except Exception as e:
            time = 0
        if time > 0:
            try:
                await message.reply(embed=emb, delete_after=time, mention_author=True)
            except Exception as e:
                botLog("info", f"Failed to reply to original message. Sending regular message instead...")
                await message.channel.send(embed=emb, delete_after=time)
        else:
            try:
                await message.reply(embed=emb, mention_author=True)
            except Exception as e:
                botLog("info", f"Failed to reply to original message. Sending regular message instead...")
                await message.channel.send(embed=emb)
    try:
        await message.delete()
    except Exception as e:
        pass

def findUrls(string):
    # findall() has been used 
    # with valid conditions for urls in string
    regex = r"(https?\S*)"
    url = re.findall(regex, string)
    return [x for x in url]