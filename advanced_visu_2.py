
import numpy as np
import pandas as pd
from PIL import Image

import matplotlib.pyplot as plt
from src.MileStone1.question_2 import data_manager




def data_cleaner(data) :
    side = data.groupby(['game_ID', 'team_info', 'period'], as_index=False)['coord_x'].mean()
    side['side'] = np.where(side.coord_x < 0, -1, 1)
    data = pd.merge(data, side[['game_ID', 'team_info', 'period', 'side']],
                    on=['game_ID', 'team_info', 'period'], how='left')
    del side

    data['distance'] = np.where(data.coord_x * data.side >= 0,
                                ((89 - abs(data.coord_x))**2 + data.coord_y**2)**0.5,
                                ((89 + abs(data.coord_x))**2 + data.coord_y**2)**0.5)

    data.loc[data['coord_x'] < 0, ['coord_x', 'coord_y']] *= -1
    #team_data = data[data.team_info == 'Anaheim Ducks'] # or any other team
    team_data=data
    team_data["coord_x"] = team_data["coord_x"].add(100)
    team_data["coord_y"] = team_data["coord_y"].add(42.5)
    return data,team_data


#utile plus tard ?
"""
team_total_shots = len(team_data)
team_goal_percentage = len(team_data[team_data.event == 'Goal'])/team_total_shots
league_total_shots = len(data)
league_goal_percentage = len(data[data.event == 'Goal'] )/league_total_shots
"""

def shot_map(data,team_data) :
    img = Image.open('./figures/nhl_rink.png')
    width, height = img.size

    scale_x=200/width
    scale_y=85/height
    scale_factor=0.5*(scale_x+scale_y)
    """
    fig = plt.figure(figsize=(width/96, height/96), dpi = 96)

    ax = fig.add_subplot(111, frameon=False, xticks=[], yticks=[])
    ax_extent = [-100,100,-42,42]

    plt.imshow(img, extent=ax_extent)
    sns.set_style("white")
    sns.kdeplot(x = team_data.coord_x,y =  team_data.coord_y, cmap="Reds", shade=True, alpha=0.4)
    
    #sns.kdeplot(x = crop.coord_x,y =  crop.coord_y, cmap="Blues", shade=True, alpha=0.4)
    ### La moyenne doit etre calculee mais je ne suis pas certain de la maniere de proceder...
    ### faudrait peut-etre quadriller la zone...


    ## Il faut encore faire la rotation de 90° et le crop pour avoir seulement la zone offensive
    plt.savefig('./figures/shot_map_beta.png')
    """
    import plotly.express as px
    import plotly.graph_objects as go


    xx=np.min(team_data["coord_x"])
    xx2=np.max(team_data["coord_x"])
    yy=np.min(team_data["coord_y"])
    yy2=np.max(team_data["coord_y"])

    fig2=px.density_contour(x=team_data["coord_x"],y=team_data["coord_y"],width=width, height=height)



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
        title="something",


            ),


    return fig2


if __name__=="__main__" :
    dm = data_manager("https://statsapi.web.nhl.com/api/v1/game/")
    dm.load(2016)
    dm.load(2017)
    dm.load(2018)
    dm.load(2019)
    dm.load(2020)
    data=dm.to_DataFrame()
    data,team_data=data_cleaner(data)
    fig2=shot_map(data,team_data)
    fig2.show()
