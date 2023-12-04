import disnake, os, re
from mutagen import oggvorbis
from Helpers.tbender_song import Song
from Helpers import globals

def validate_song(song:Song, message:disnake.Message, fstruct:list):
    #Validate alphanumeric ref/folder
    if not validate_alphanum(song.tmb["trackRef"], fstruct[2]) and globals.settings.verification.alphanumeric:
        return globals.settings.lang.rejects.alphanum
    improv = validate_improv(song.tmb)
    if not improv == True:
        return globals.settings.lang.rejects.invalid_improv.replace("$VAR", str(improv).upper())
    #Validate audio length
    if not validate_audio(fstruct[0], song.duration):
        return globals.settings.lang.rejects.song_length
    #Validate note pitch and timing
    pitchnotes, timenotes = validate_notes(song.tmb)
    if not pitchnotes == [] and globals.settings.verification.note_pitch:
        return globals.settings.lang.rejects.note_pitch.replace("$VAR", ", ".join(pitchnotes))
    if not timenotes == [] and globals.settings.verification.note_position:
        return globals.settings.lang.rejects.note_position.replace("$VAR", ", ".join(timenotes))
    #Validate spacing INT
    if not spacing_is_integer(song.tmb):
        return globals.settings.lang.rejects.spacing_not_int
    #Validate no WIP keys
    foundkeys = validate_wip_keys(song.tmb)
    if len(foundkeys) > 0:
        return globals.settings.lang.rejects.has_wip_key.replace("$VAR", ", ".join(foundkeys))
    #Validate file types
    v = validate_file_types(song.files)
    if not v == True:
        return globals.settings.lang.rejects.invalid_files.replace("$VAR", ", ".join(v))
    return

def validate_alphanum(trackref:str, foldername:str):
    expression = "[a-z0-9\-_\s]+"
    if not regex_compare(expression, trackref):
        return False
    if not regex_compare(expression, foldername):
        return False
    return True

def validate_improv(tmb:dict):
    if not "improv_zones" in tmb.keys():
        print("Key not found")
        return True
    if tmb["improv_zones"].__class__ == list().__class__:    
        return True
    return tmb["improv_zones"].__class__.__name__

def regex_compare(expression:re, input:str):
    output = re.fullmatch(expression, input, flags=re.IGNORECASE)
    if output == None:
        return False
    else:
        return True

def validate_notes(tmb:dict):
    pitchnotes = []
    timenotes = []
    songend = tmb["endpoint"]
    for note in tmb["notes"]:
        if max(abs(note[2]), abs(note[4])) > 178.75:
            pitchnotes.append(str(note[0]))
        if note[0] < 0 or note[0] + note[1] > songend:
            timenotes.append(str(note[0]))
    return pitchnotes, timenotes

def spacing_is_integer(tmb:dict):
    value = tmb["savednotespacing"]
    try:
        int(value)
    except ValueError as e:
        return False
    else:
        return True

def validate_audio(audiopath:str, songlength:float):
    ogg = oggvorbis.OggVorbis(os.path.join(audiopath, "song.ogg"))
    if songlength > ogg.info.length:
        return False
    return True

def validate_wip_keys(tmb:dict):
    illegalkeys = ["is_wip", "skip_save"]
    foundkeys = []
    for key in illegalkeys:
        if key in list(tmb.keys()) and tmb[key]:
            foundkeys.append(key)
    return foundkeys

def validate_file_types(files:list):
    allowed_regex = []
    for f in list(globals.settings.verification.allowed_filenames):
        f = f.replace(".", "\.")
        f = f.replace("*", ".+")
        allowed_regex.append(re.compile(f"({f})"))

    unmatched_files = []
    for f in files:
        for r in allowed_regex:
            if r.fullmatch(f):
                break
        else:
            unmatched_files.append(f)

    if len(unmatched_files) > 0:
        return unmatched_files
    return True
