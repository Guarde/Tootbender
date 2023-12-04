import os, disnake, json, datetime, aiohttp
from Helpers import globals

def find_attachment(message:disnake.Message):
    for att in message.attachments:
        if att.filename in ["LogOutput.log", "LogOutput.log.1", "song.tmb"]:
            return att
    return False

async def parse_log(message:disnake.Message, url):
    emb = disnake.Embed(title="Log Parser", url=message.jump_url)
    req = await globals.session.get(url=url, timeout=5)
    if not req.ok:
        emb.description = f"Failed to obtain log file:\n[{req.status} {req.reason}]"
        emb.color = disnake.Colour.red()
        return False, False
    
    log = await req.text()
    log = log.split("\n")
    paste = await hastebin_api("\n".join(log))
    mods = []
    errors = []
    warnings = []
    plural = ""
    debuginfo = False
    babooninfo = False
    note = "\n\n*Version reported might differ from the actual mod version*\n*This list does not include library mods*\n***For a more detailed overview (that includes library mods), please consider installing the DebugHelper mod!***\n (https://trombone-champ.thunderstore.io/package/Guardie/DebugHelper/)"

    for line in log:
        if line.startswith("[Info   :   BepInEx] Loading "):
            line = line.replace("[Info   :   BepInEx] Loading ", "")
            line = line[1:len(line)-1]
            linelist = line.split(" ")
            modname = " ".join(linelist[:len(linelist) - 1])
            version = linelist[len(linelist) - 1]
            mods.append(f"[**{modname.replace('_', ' ')}**-{version}")

        if line.startswith("[Error  :"):
            line = line[9:].strip().split("]")
            line = f"• **[{line[0]}]** *{']'.join(line[1:]).strip()}*"
            errors.append(line)

        if line.startswith("[Warning:"):
            line = line[9:].strip().split("]")
            line = f"• **[{line[0]}]** *{']'.join(line[1:]).strip()}*"
            warnings.append(line)

        if line.startswith("[Message:DebugHelper] "):
            line = line.replace("[Message:DebugHelper] ", "").strip()
            try:
                debuginfo = json.loads(line)
            except Exception:
                note = "\n\n*Version reported might differ from the actual mod version*\n**This list does not include library mods as the JSON returned by the DebugHelper mod could not be decoded**"
                continue

        if line.startswith("[Info   : BaboonAPI] ENV_DATA:"):
            line = line.replace("[Info   : BaboonAPI] ENV_DATA:", "").strip()
            try:
                babooninfo = json.loads(line)
            except Exception:
                continue

    info = dict()
    footer = dict()
#[Info   : BaboonAPI] ENV_DATA:{"GameVersion":"1.13E","Launcher":{"AreModsInGameDir":false,"BepInPath":"C:\\Users\\Manu\\AppData\\Roaming\\r2modmanPlus-local\\TromboneChamp\\profiles\\Default\\BepInEx"},"Platform":"Microsoft Windows NT 10.0.22621.0","SteamValid":true,"Timestamp":1692134138,"UnityPlatform":"WindowsPlayer","UnityVersion":"2019.4.40f1"}
    if babooninfo:
        for key in list(babooninfo.keys()):
            value = babooninfo[key]
            if key == "Launcher":
                info["Modded in Game Directory"] = value["AreModsInGameDir"]
                continue
            if key == "SteamValid":
                info["Steam Connected"] = value
                continue
            if key == "GameVersion":
                footer["Game Version"] = value
                continue
            if key == "Platform":
                footer["Platform"] = value
                continue
            if key == "Timestamp":
                timestring = datetime.datetime.fromtimestamp(value).strftime('%d %b, %Y - %H:%M:%S')
                footer["Log Date"] = timestring
                continue

#[Message:DebugHelper] {"Game Version": "1.13e", "Platform": "Windows", "Using Steam": "Yes", "Using r2modman": "Yes", "Timestamp": 1692134138, "CoreMods": [["Newtonsoft.Json", "13.0.0.0"], ["FSharp.Core", "6.0.0.0"], ["RuntimeUnityEditor.Bepin5", "1.0.0.0"], ["RuntimeUnityEditor.Core", "4.1.1.0"]]}
    if debuginfo:
        baboonkeys = list(info.keys()) + list(footer.keys())
        note = "\n\n*Version reported might differ from the actual mod version*"
        for key in list(debuginfo.keys()):
            value = debuginfo[key]
            if key == "Using Steam" and not "Steam Connected" in baboonkeys:
                if value == "Yes":
                    value = True
                else:
                    value=False
                info["Steam Connected"] = value
                continue
            if key == "Using r2modman" and not "Modded in Game Directory" in baboonkeys:
                if value == "Yes":
                    value = True
                else:
                    value=False
                info["Modded in Game Directory"] = value
                continue

            if key == "Game Version" and not "Game Version" in baboonkeys:
                footer["Game Version"] = value
                continue
            if key == "Platform":
                footer["Platform"] = value
                continue
            if key == "Timestamp" and not "Log Date" in baboonkeys:
                timestring = datetime.datetime.fromtimestamp(value).strftime('%d %b, %Y - %H:%M:%S')
                footer["Log Date"] = timestring
                continue
            if key == "CoreMods":
                if len(value) > 0:
                    note = "\n\n*⁽\*⁾Library mod*\n*Version reported might differ from the actual mod version*"
                for mod in value:
                    mods.append(f"[**{mod[0]}**-{mod[1]}]⁽\*⁾")
                continue
    parsed_footer = []
    for entry in list(footer.keys()):
        parsed_footer.append(f"{entry}: {footer[entry]}")

    parsed_info = []
    for entry in list(info.keys()):
        parsed_info.append(f"**{entry}:** {info[entry]}")

    emb.set_footer(text="  |  ".join(parsed_footer))
    emb.description = "\n".join(parsed_info)
    if mods == []:
        emb.add_field(name="Mods Loaded:", value="⚠️ No mods loaded!", inline = False) 
    else:
        emb.add_field(name=f"Mods Loaded ({len(mods)}):", value=", ".join(mods) + note, inline = False)

    if errors == []:
        emb.add_field(name="Errors:", value="✅ No errors reported", inline = False)
    else:
        if len(errors) > 1:
            plural = "s"
        if len(errors) <= 5:
            emb.add_field(name=f"Error{plural} ({len(errors)}):", value="\n".join(errors), inline = False)
        else:            
            emb.add_field(name=f"Error{plural} ({len(errors)}):", value="\n".join(errors[:4]) + f"\n***(And {len(errors)-4} more...)***", inline = False)

    if warnings != []:
        if len(warnings) > 1:
            plural = "s"
        if len(warnings) <= 5:
            emb.add_field(name=f"Warning{plural} ({len(warnings)}):", value="\n".join(warnings), inline = False)
        else:            
            emb.add_field(name=f"Warning{plural} ({len(warnings)}):", value="\n".join(warnings[:4]) + f"\n***(And {len(warnings)-4} more...)***", inline = False)
    return emb, paste

async def hastebin_api(log:str):
    token = globals.settings.upload.hastebin_api_key
    req = await globals.session.post(url="https://hastebin.com/documents", headers={"Authorization": f"Bearer {token}", "content-type": "text/plain"}, data=log.encode(encoding = "utf-8"))
    if not req.ok:
        return False
    else:
        data = await req.text()
        id = json.loads(data)["key"]
        return f"https://hastebin.com/share/{id}.log"