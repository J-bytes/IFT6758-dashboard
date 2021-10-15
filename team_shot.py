
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as p
from question_2 import data_manager

def data_cleaner(df):
    side = df.groupby(['game_ID', 'team_info', 'period'], as_index=False)['coord_x'].mean()
    side['side'] = np.where(side.coord_x < 0, -1, 1)
    df = pd.merge(df, side[['game_ID', 'team_info', 'period', 'side']],
                    on=['game_ID', 'team_info', 'period'], how='left')
    del side

    df['distance'] = np.where(df.coord_x * df.side >= 0,
                                ((89 - abs(df.coord_x)) ** 2 + df.coord_y ** 2) ** 0.5,
                                ((89 + abs(df.coord_x)) ** 2 + df.coord_y ** 2) ** 0.5)

    df = df.loc[(df.game_type == 'regular')]
    df.loc[df['coord_x'] < 0, ['coord_x', 'coord_y']] *= -1
    games = df.groupby(['game_ID'], as_index=False)['period'].max()

    # games
    games['game_length'] = np.select([games.period == 3, games.period == 4, games.period == 5],
                                     [60, 0, 65])
    games
    liste_prolo = list(games[games.period == 4]['game_ID'])
    time = df[(df.game_ID.isin(liste_prolo)) & (df.period == 4) & (df.event == 'Goal')][['game_ID', 'game_time']]

    for i in range(len(liste_prolo)):
        games.loc[games.game_ID == liste_prolo[i], 'game_length'] = 60 + float(time.loc[
                                                                                   time.game_ID == liste_prolo[i]][
                                                                                   'game_time'].values[0][0:2] + "." +
                                                                               time.loc[
                                                                                   time.game_ID == liste_prolo[i]][
                                                                                   'game_time'].values[0][3:5])

    df = pd.merge(df, games[['game_ID', 'game_length']],
                  on=['game_ID'], how='left')

    teams = df.groupby(['team_info', 'game_ID'], as_index=False)['game_length'].agg('max')
    time_teams = teams.groupby('team_info', as_index=False)['game_length'].sum()
    del (teams, time, liste_prolo, games)

    df = df[df.distance < 100]
    total_game_len_league = time_teams.game_length.sum()
    # bin the data into equally spaced groups
    df['x_cut'] = pd.cut(df.coord_x, np.linspace(0, 100, 61), right=False)
    df['y_cut'] = pd.cut(df.coord_y, np.linspace(-42.5, 42.5, 41), right=False)

    # group and count
    league_cut = df.groupby(['x_cut', 'y_cut'], as_index=False)['event'].count()
    # team_cut.head(10)

    league_cut = league_cut.rename(columns={'event': 'league_avg'})
    league_cut['league_avg'] = league_cut['league_avg'] / total_game_len_league * 60
    df = pd.merge(df, league_cut, on=['x_cut', 'y_cut'], how='left')

    # bin the data into equally spaced groups

    # group and count
    team_cut = df.groupby(['team_info', 'x_cut', 'y_cut'], as_index=False)['event'].count()
    time_teams = time_teams.rename(columns={'game_length': 'tot_game_len'})

    team_cut = team_cut.rename(columns={'event': 'team_avg'})
    team_cut = pd.merge(team_cut, time_teams, on='team_info')
    team_cut['team_avg'] = team_cut['team_avg'] / team_cut.tot_game_len * 60
    df = pd.merge(df, team_cut, on=['team_info', 'x_cut', 'y_cut'])

    df['diff_shot'] = df.team_avg - df.league_avg
    df['coord_x_bin'] = df['x_cut'].apply(lambda x: x.mid).astype('float')
    df['coord_y_bin'] = df['y_cut'].apply(lambda x: x.mid).astype('float')
    print(df.coord_x_bin)
    df = df.groupby(['team_info', 'coord_x_bin', 'coord_y_bin'], as_index=False)['league_avg', 'team_avg'].min()
    # fun = fun.fillna(0)#[['team_info', 'coord_x_bin','coord_y_bin','league_avg','team_avg']].fillna(0)
    df[['league_avg', 'team_avg']] = df[['league_avg', 'team_avg']].fillna(0)
    df['diff_shot'] = df.league_avg - df.team_avg
    df = df.drop(columns=['league_avg', 'team_avg'])
    return df

def shot_map(data):

    img = Image.open('./figures/nhl_rink.png')
    width, height = img.size
    scale_x = 200 / width
    scale_y = 85 / height
    scale_factor = 0.5 * (scale_x + scale_y)
    data.coord_x_bin = data.coord_x_bin + 100/2
    data.coord_y_bin = data.coord_y_bin + 42.5/2
    data['diff_shot'] = np.where(data.diff_shot == 0, None,data.diff_shot)
    #data.diff_shot = data.diff_shot.round(5)

    ###Ici ce serait le dernier df que je t'ai montre mais je ne sais pas quoi faire avec les na...
    #fig2 = px.density_heatmap(x = data["coord_x_bin"], y=data["coord_y_bin"], z=data['diff_shot'],
    #                          width=width,height=height)

    fig2 = px.density_contour(x=data["coord_x_bin"], y=data["coord_y_bin"], z=data['diff_shot'],
                              width=width, histfunc= 'avg',
                              height=height)

    ##Si on rajoute du remplissage, ça cache l'image...


    fig2.update_traces(
        #contours_showlabels=True,
        opacity = 0.4,
        contours_coloring = 'fill',
        zmid=0,
       
        #colorbar=dict(
        #    title='Number Count',
        #    titleside='right',
        #    titlefont=dict(
        #        size=14,
        #        family='Arial, sans-serif'))
    )

    fig2.add_layout_image(dict(source=img,
                               x=0,
                               sizex=width * scale_factor,
                               y=height * scale_factor,
                               sizey=height * scale_factor,
                               xref="x",
                               yref="y",
                               opacity=1.0,
                               sizing="stretch",

                               layer="below"))

    # Configure axes
    fig2.update_xaxes(
        visible=False,
        range=[0, width * scale_factor]
    )

    fig2.update_yaxes(
        visible=False,
        range=[0, height * scale_factor],
        # the scaleanchor attribute ensures that the aspect ratio stays constant
        scaleanchor="x"
    )

    fig2.update_layout(
        width=width,
        height=height,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        yaxis = dict(scaleanchor = 'x', constrain ='domain')
        #title="something",


    ),

    return fig2

if __name__ == "__main__":
    dm = data_manager("https://statsapi.web.nhl.com/api/v1/game/")
    #dm.load(2016)
    #dm.load(2017)
    dm.load(2017)
    #dm.load(2019)
    #dm.load(2020)
    data = dm.to_DataFrame()
    data = data_cleaner(data)
    data = data[data.team_info == 'Tampa Bay Lightning']
    fig2 = shot_map(data)
    fig2.show()
