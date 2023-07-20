import discord, random, os, requests, asyncio, json, datetime
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

avaliable_maps = ["mirage", "anubis", "ancient", "inferno", "overpass", "nuke", "vertigo"]
code_to_map={2056:"ancient",8388616:"anubis",32776:"mirage",8200:"nuke",268435464:"overpass",4104:"inferno",16392:"vertigo"}
api_data=json.loads(open("keys/api.json", encoding='utf-8').read())
users_data=json.loads(open("keys/users.json", encoding='utf-8').read())
probability_of_maps_count = {0: 3,1: 40,2: 20,3: 10,4: 10,5: 7,6: 7,7: 3}

client.login(api_data["login"],api_data["password"])
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

def get_request(url):
    try:
        rq=requests.get(url)
        while rq.status_code == 429:
            sleep(1)
            rq = requests.get(url)
        return rq
    except:
        return get_request(url)

def update_users_file():
    now = datetime.datetime.now()
    file_name=os.getcwd()+"\\backup\\backup_"+str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"_"+str(now.hour)+"-"+str(now.minute)+"-"+str(now.second)+".json"
    open(file_name,"wb+").write(open("keys/users.json","rb").read())
    open("keys/users.json","w",encoding='utf-8').write(json.dumps(users_data,ensure_ascii=False).replace("{","{\n    ").replace("},","},\n    ").replace("}}","}\n}    ").replace('"maps"','\n        "maps"').replace('"last_id"','    "last_id"').replace('"match_api"','\n        "match_api"').replace('"steam_id"','\n        "steam_id"'))

def update_stats(author):
    print(f"Collecting sharecodes for {author}...")
    maps_count=0
    while True:
        url = f'https://api.steampowered.com/ICSGOPlayers_730/GetNextMatchSharingCode/v1?key={api_data["steam_api"]}&steamid={users_data[author]["steam_id"]}&steamidkey={users_data[author]["match_api"]}&knowncode={users_data[author]["last_id"]}'
        id = get_request(url).json()['result']['nextcode']
        if id=="n/a":
            break
        else:
            maps_count+=1
            users_data[author]["last_id"]=id
        print(f'Working with {users_data[author]["last_id"]}')
        match_info = decode(users_data[author]["last_id"])
        response=None
        while response==None:
            try:
                cs.request_full_match_info(match_info["matchid"],match_info["outcomeid"],match_info["token"])
                response, = cs.wait_event('full_match_info')
            except:
                client.login(api_data["login"],api_data["password"])

        game_type=response.matches[0].roundstatsall[-1].reservation.game_type
        if game_type in code_to_map.keys():
            users_data[author]["maps"]=(users_data[author]["maps"]+[code_to_map[game_type]])[-20:]
    print(f"Number of collected maps:{maps_count}")
    update_users_file()
    print("Users file updated")
    return maps_count

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
    vc.play(discord.FFmpegPCMAudio(source=path, executable="ffmpeg/ffmpeg.exe"))
    while vc.is_playing():
        await asyncio.sleep(.1)


@bot.command()
async def randmaps(ctx):
    async with ctx.typing():
        author=str(ctx.author.name)
        if author not in users_data.keys():
            author=api_data["default_user"]
        update_stats(author)
        current_maps = []
        number_of_maps = randomize(probability_of_maps_count)
        maps = avaliable_maps.copy()
        if number_of_maps<7:
            probability_of_maps = {}
            for map in maps:
                probability_of_maps[map] = 1
            for i in range(len(users_data[author]["maps"])):
                probability_of_maps[users_data[author]["maps"][i]] = probability_of_maps[users_data[author]["maps"][i]]+(2**i)
            max_probability = max(probability_of_maps.values())+1
            for map in maps:
                probability_of_maps[map] = max_probability-probability_of_maps[map]
            if number_of_maps != 0:
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
            if number_of_maps==7:
                await ctx.send(', '.join([str(elem) for elem in maps]))
            elif number_of_maps==0:
                await ctx.send('Премьер режим')
            else:
                await ctx.send(', '.join([str(elem) for elem in current_maps]))
            await play_audio(vc, pick_random_file("song/bye"))
            await play_audio(vc, "song/empty.mp3")
            await vc.disconnect()
        else:
            await ctx.send(', '.join([str(elem) for elem in current_maps]))

@bot.command()
async def currentprob(ctx, *args):
    author = ' '.join(args)
    if author not in users_data.keys():
        author=ctx.author.name
        if author not in users_data.keys():
            author=api_data["default_user"]
    maps = avaliable_maps.copy()
    probability_of_maps = {}
    for map in maps:
        probability_of_maps[map] = 1
    for i in range(len(users_data[author]["maps"])):
        probability_of_maps[users_data[author]["maps"][i]] = probability_of_maps[users_data[author]["maps"][i]]+(2**i)
    max_probability = max(probability_of_maps.values())+1
    for map in maps:
        probability_of_maps[map] = max_probability-probability_of_maps[map]
    sum_of_prob=sum(probability_of_maps.values())
    msg=f"Вероятности выпадения карт {author}\n"
    for map in maps:
        msg+=map+": "+str(round(probability_of_maps[map]/sum_of_prob*100,2))+"%\n"
    await ctx.send(msg)

@bot.command()
async def update(ctx, *args):
    author = ' '.join(args)
    if author not in users_data.keys():
        author=ctx.author.name
        if author not in users_data.keys():
            author=api_data["default_user"]
    number_of_maps=update_stats(author)
    await ctx.send(f"Статистика для {author} обновлена\nКарт обработано: {str(number_of_maps)}")

bot.run(api_data["bot_api"])