import discord, random, os, requests, asyncio
from discord.ext import commands
from time import sleep
from csgo.sharecode import decode
from steam.client import SteamClient
from csgo.client import CSGOClient

client = SteamClient()
cs = CSGOClient(client)

@client.on('logged_on')
def start_csgo():
    cs.launch()


client.login(open("keys/login.txt").read(),open("keys/password.txt").read())
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

avaliable_maps = ["mirage", "anubis", "ancient", "inferno", "overpass", "nuke", "vertigo"]
code_to_map={2056:"ancient",8388616:"anubis",32776:"mirage",8200:"nuke",268435464:"overpass",4104:"inferno",16392:"vertigo"}

def get_request(url):
    try:
        rq=requests.get(url)
        while rq.status_code == 429:
            sleep(1)
            rq = requests.get(url)
        return rq
    except:
        return get_request(url)

def update_stats():
    id = open("keys/lastid.txt").read()
    steamapi = open("keys/steamapi.txt").read()
    matchesid = open("keys/matches_access.txt").read()
    id = get_request(f'https://api.steampowered.com/ICSGOPlayers_730/GetNextMatchSharingCode/v1?key={steamapi}&steamid=76561198390902271&steamidkey={matchesid}&knowncode={id}').json()['result']['nextcode']
    
    print("Collecting sharecodes...")
    maps = []
    last_id=id+""
    while id != "n/a":
        match_info = decode(id)
        response=None
        while response==None:
            try:
                cs.request_full_match_info(match_info["matchid"],match_info["outcomeid"],match_info["token"])
                response, = cs.wait_event('full_match_info')
            except:
                client.login(open("keys/login.txt").read(),open("keys/password.txt").read())

        game_type=response.matches[0].roundstatsall[-1].reservation.game_type
        if game_type in code_to_map.keys():
            maps.append(code_to_map[game_type])
        print(f"Working with {id}")
        url = f'https://api.steampowered.com/ICSGOPlayers_730/GetNextMatchSharingCode/v1?key={steamapi}&steamid=76561198390902271&steamidkey={matchesid}&knowncode={id}'
        last_id=id+""
        id = get_request(url).json()['result']['nextcode']
    print(f"Number of collected maps:{len(maps)}")

    if len(maps) > 0:
        f = open("maps.txt")
        maps_from_file=f.read().split(",")
        f.close()
        f = open("maps.txt", "w+")
        maps=maps_from_file+maps
        maps_string = ','.join([str(elem) for elem in maps[-100:]])
        f.write(maps_string)
        print("Maps file updated")
        f = open("keys/lastid.txt", "w")
        f.write(last_id)
        f.close()
        print("Last match ID saved")


def randomize(dict):
    sum_of_values = sum(dict.values())
    values = list(dict.values())
    keys = list(dict.keys())
    random_number = random.randrange(sum_of_values)
    counter = -1
    while random_number >= 0:
        random_number -= values[counter+1]
        counter += 1
    return keys[counter]


def pick_random_file(dir_name):
    dir = os.scandir(dir_name)
    files = []
    for file in dir:
        if file.is_file():
            files.append(file.name)
    return dir_name+"/"+files[random.randrange(len(files))]


async def play_audio(vc, path):
    vc.play(discord.FFmpegPCMAudio(source=path))
    while vc.is_playing():
        await asyncio.sleep(.1)


@bot.command()
async def randmaps(ctx):
    async with ctx.typing():
        update_stats()
        probability_of_maps_count = {
            0: 3,
            1: 30,
            2: 20,
            3: 15,
            4: 15,
            5: 7,
            6: 7,
            7: 3
        }
        number_of_maps = randomize(probability_of_maps_count)
        played_maps = open("maps.txt").read().split(",")
        maps = avaliable_maps.copy()
        probability_of_maps = {}
        for map in maps:
            probability_of_maps[map] = 1
        for map in played_maps:
            probability_of_maps[map] += 1
        max_probability = max(probability_of_maps.values())+1
        for map in maps:
            probability_of_maps[map] = max_probability-probability_of_maps[map]
        if number_of_maps != 0:
            current_maps = []
            for i in range(number_of_maps):
                current_map = randomize(probability_of_maps)
                current_maps.append(current_map)
                probability_of_maps[current_map] = 0
        if ctx.author.voice != None:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            await play_audio(vc, pick_random_file("song/hello"))
            await play_audio(vc, "song/maps/you_are_playing.m4a")
            await play_audio(vc, f"song/maps/number/{number_of_maps}.m4a")
            for map in current_maps:
                await play_audio(vc, f"song/maps/maps/{map}.m4a")
            await ctx.send(', '.join([str(elem) for elem in current_maps]))
            await play_audio(vc, pick_random_file("song/bye"))
            await play_audio(vc, "song/empty.mp3")
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
        else:
            await ctx.send(', '.join([str(elem) for elem in current_maps]))

@bot.command()
async def currentprob(ctx):
    played_maps = open("maps.txt").read().split(",")
    maps = avaliable_maps.copy()
    probability_of_maps = {}
    for map in maps:
        probability_of_maps[map] = 1
    for map in played_maps:
        probability_of_maps[map] += 1
    max_probability = max(probability_of_maps.values())+1
    for map in maps:
        probability_of_maps[map] = max_probability-probability_of_maps[map]
    sum_of_prob=sum(probability_of_maps.values())
    msg=""
    for map in maps:
        msg+=map+": "+str(round(probability_of_maps[map]/sum_of_prob*100,2))+"%\n"
    await ctx.send(msg)
            
bot.run(open("keys/api.txt").read())
