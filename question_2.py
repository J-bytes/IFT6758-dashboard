import requests
import pandas as pd
import json
import os
from tqdm import tqdm
#https://statsapi.web.nhl.com/api/v1/game/ID/feed/live

"""
Game IDs

The first 4 digits identify the season of the game (ie. 2017 for the 2017-2018 season). 
The next 2 digits give the type of game, where 01 = preseason, 02 = regular season, 
03 = playoffs, 04 = all-star. The final 4 digits identify the specific game number. 
For regular season and preseason games, this ranges from 0001 to the number of games played. 
(1271 for seasons with 31 teams (2017 and onwards) and 1230 for seasons with 30 teams). 
For playoff games, the 2nd digit of the specific number gives the round of the playoffs, 
the 3rd digit specifies the matchup, and the 4th digit specifies the game (out of 7).

src : https://github.com/dword4/nhlapi
"""



class data_manager() :
    def __init__(self, url,path=""):
        """

        :param
        url: The url of the REST API
        path : the path between your code and the data folder
        """

        self.url=url


        self.number_of_match=0
        self.starting_dict=dict({

            "event": [],
            "game_time": [],
            "period_info": [],
            "period" :[],
            "game_ID": [],
            "team_info": [],
            "coord_x": [],
            "coord_y": [],
            "shooter_name": [],
            #"rinkSide" : [] ,
            "goalie_name": [],
            "shot_type": [],
            "net_empty": [],
            "strength": [],
            "season" : [],
            "game_type" : [],
            "game_number" : []


        }.copy())
        self.data=dict(self.starting_dict.copy())
        self.path=path
        self.all_data=dict(self.starting_dict.copy())

    def to_DataFrame(self):
        return pd.DataFrame(self.all_data)

    def TidyData(self,dataset):




        gametype={
            "01" : "preseason",
            "02" : "regular" ,
            "03" : "playoff",
            "04" : "all-star"
        }
        teams = dataset["gameData"]["teams"]
        gameID=dataset["gamePk"]["game"]

        events=["Goal","Shot"]
        plays=dataset["liveData"]["plays"]

        away=dataset["gameData"]["teams"]["away"]["name"]
        home=dataset["gameData"]["teams"]["home"]["name"]
        for event in plays["allPlays"] :
            a=event["result"]["event"]
            if a in events :

                self.data["event"].append(a)
                self.data["game_time"].append(event["about"]["periodTime"])
                self.data["period_info"].append(event["about"]["periodType"])
                self.data["game_ID"].append(gameID)
                self.data["team_info"].append(event["team"]["name"])
                self.data["period"].append(event["about"]["period"])

                try :
                    if event["result"]["event"]=="Shot" or event["result"]["event"]=="Goal" :
                        x=event["coordinates"]["x"]
                        y=event["coordinates"]["y"]
                        self.data["coord_x"].append(x)
                        self.data["coord_y"].append(y)
                    else :
                        self.data["coord_x"].append(None)
                        self.data["coord_y"].append(None)
                except :
                    self.data["coord_x"].append("N/A")
                    self.data["coord_y"].append("N/A")

                try :
                    if a=="Shot" or a == "Goal" :
                        self.data["shot_type"].append(event["result"]["secondaryType"])
                    elif a=="Goal" :
                        self.data["shot_type"].append(self.data["shot_type"][len(self.data["shot_type"])])
                    else :
                        self.data["shot_type"].append(None)
                except :
                    self.data["shot_type"].append("N/A")
                self.data["strength"].append(None if event["result"]["event"]=="Shot" else event["result"]["strength"]["name"])

                self.data["shooter_name"].append(event["players"][0]["player"]["fullName"])  # doublecheck if always 0


                goalie=None
                for player in event["players"][1::] :
                    if player["playerType"]=="Goalie" :
                        goalie=player["player"]["fullName"]
                self.data["goalie_name"].append(goalie)

                #net_empty=None if event["result"]["event"]=="Shot" else event["result"]["emptyNet"]
                net_empty=None
                if event["result"]["event"] == "Goal" :
                    if goalie==None :
                        net_empty=False
                    else :
                        net_empty=True
                self.data["net_empty"].append(net_empty)

                self.data["season"].append(str(gameID)[0:4])
                try :
                    self.data["game_type"].append(  gametype[str(gameID)[4:6]])
                except :
                    self.data["game_type"].append(str(gameID)[4:6])


                self.data["game_number"].append(str(gameID)[6::])


                """
                 if  gametype[str(gameID)[4:6]]=="all-star" or gametype[str(gameID)[4:6]]=="preseason" :
                    self.data["rinkSide"].append(None)
                else :
                    period=event["about"]["period"]-1
                    if event["about"]["periodType"]=="SHOOTOUT" :
                        period-=1
                    if event["team"]["name"]==home :
                        self.data["rinkSide"].append(dataset["liveData"]["linescore"]["periods"][period]["home"]["rinkSide"])
                    elif  event["team"]["name"]==away :
                        self.data["rinkSide"].append(dataset["liveData"]["linescore"]["periods"][period]["away"]["rinkSide"])
                    else :
                        raise Exception("team not found")
                """



        return
        
        
    def __add__(self,dataset):
        """
        This function overload the __add__ operator and allow to merge the dataset already in self.data with a new game dataset
        :param dataset: The new season dataset to merge with our previous dataset
        :return: nothing
        """
        return

    def clear(self):
        for (k,v) in self.all_data.items() :
            self.all_data[k]=[]

    def load_online(self,path2, season):
        # !!! verifier date pour 2021-2022
        schedule_url = f"https://statsapi.web.nhl.com/api/v1/schedule?startDate={season}-10-01&endDate={season + 1}-09-30"
        r = requests.get(schedule_url)
        response = r.status_code

        if response == 200:
            tqdm.write("The server has been accessed succesfully")
        elif response == 404:
            raise Exception("Connection Error 404")
        else:
            raise Exception(f"error {r.status_code}")

        schedule = r.json()

        for date in tqdm(schedule["dates"], mininterval=1):
            for game in date["games"]:
                self.load_game(game["gamePk"], season)

        copy=dict(self.data.copy())
        pd.DataFrame(copy).to_csv(path2, index=False)
        return
    def load(self,season,reload=False):

        path2 = os.path.join(self.path,"data", "processed", f"{season}.csv")

        if not reload :
            if os.path.isfile(path2) :
                self.data=pd.read_csv(path2)
            else :
                self.load_online(path2,season)
        else :
            self.load_online(path2, season)


        for k, v in self.data.items():
            self.all_data[k].extend(v)

        if type(self.data)!=dict : #pandas converts it to a dataframe without my permisssion
            self.data=self.data.to_dict()
        for k, v in self.data.items():
            self.data[k] =[]
    def load_game(self,game_ID,season):
        """

        :param game_ID: The game_ID which identifies a particular game.
        :return:
        """

        path= os.path.join(self.path,"data","raw",f"{game_ID}.json")
        if os.path.isfile(path) :
            dataset = pd.read_json(path)
            self.TidyData(dataset)

        else :
            #tqdm.write(f"Could not load file locally for game {game_ID}",end = "\r")
            dataset = pd.read_json(self.url+f"{game_ID}/feed/live")
            dataset.to_json(path)
            self.TidyData(dataset)


        return

if __name__=="__main__" :
        dm= data_manager("https://statsapi.web.nhl.com/api/v1/game/")
        dm.load(2016)
        dm.clear()
        dm.load(2017)
        dm.load(2018)
        dm.clear()
        dm.load(2019)
        dm.load(2020)

        #print(dm.to_DataFrame().head(10))
"""
@Jonathan, je ne veux pas changer de trucs dans le code que tu as fait, mais penses-tu qu'on pourrait ajouter ca
a la portion Tidydata ?  C'est pertinent autant pour les buts que pour les tirs pour la colonne distance et 
c'est pertinent pour toutes les autres evenement dans le cas de rink side
side = self.data.groupby(['game_ID', 'team_info', 'period'], as_index=False)['coord_x'].mean()
side['score_side'] = np.where(side.coord_x < 0, -1, 1)
self.data = pd.merge(self.data, side[['game_ID', 'team_info', 'period', 'side']],
                on=['game_ID', 'team_info', 'period'], how='left')
del side

self.data['distance'] = np.where(self.data.coord_x * self.data.score_side >= 0,
                            ((89 - abs(self.data.coord_x)) ** 2 + self.data.coord_y ** 2) ** 0.5,
                            ((89 + abs(self.data.coord_x)) ** 2 + self.data.coord_y ** 2) ** 0.5)
"""