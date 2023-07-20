import requests,datetime,os,json
from time import sleep
from csgo.sharecode import decode
from steam.client import SteamClient
from csgo.client import CSGOClient

client = SteamClient()
cs = CSGOClient(client)

@client.on('logged_on')
def start_csgo():
    cs.launch()

code_to_map={2056:"ancient",8388616:"anubis",32776:"mirage",8200:"nuke",268435464:"overpass",4104:"inferno",16392:"vertigo"}
api_data=json.loads(open("keys/api.json").read())
users_data=json.loads(open("keys/users.json", encoding='utf-8').read())

client.login(api_data["login"],api_data["password"])

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
    file_name=os.getcwd()+"\\backup\\backup_"+str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"_"+str(now.hour)+str(now.minute)+str(now.second)+".json"
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

for user in users_data.keys():
    update_stats(user)
input("Stats updated...")