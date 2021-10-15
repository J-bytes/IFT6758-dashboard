# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 22:58:46 2020

@author: joeda
"""

import os
from random import randint
import numpy as np
import flask

from advanced_visu_2 import data_cleaner
from advanced_visu_2 import shot_map
from question_2 import data_manager
import plotly.express as px




import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = flask.Flask(__name__)

server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)
app_color = {"graph_bg": "#082255", "graph_line": "#007ACE"}

dm = data_manager("https://statsapi.web.nhl.com/api/v1/game/")
dm.load(2016)
dm.load(2017)
dm.load(2018)
dm.load(2019)
dm.load(2020)
data=dm.to_DataFrame()
data,team_data=data_cleaner(data)
fig1 = shot_map(data,team_data)




list_teams = team_data[team_data["season"]==2016]["team_info"].unique()
option_list = []
for i in list_teams:
    option_list.append(
        {"label": i, "value": i}
    )
first_team=option_list[0]["value"]

app.layout = html.Div(children=[
    html.H1(''),

    html.Div(children=[
    html.Div(children=[
        dcc.Graph(
        id='graph',
        animate=False,
        figure=fig1
    )],
        className="six columns"),
    ]),



        html.Label('Season'),
    html.Div(dcc.Dropdown(
    options=[
        {'label': '2016-2017', 'value': 2016},
        {'label': '2017-2018', 'value': 2017},
        {'label': '2018-2019', 'value': 2018},
        {'label': '2019-2020', 'value': 2019},
        {'label': '2020-2021', 'value': 2020},
    ],
    searchable=True,
    id='season',
    value=2016,
    placeholder="2016"),  style= {'padding': 20}),

    html.Label('teams'),


    html.Div(dcc.Dropdown(

 #       options=[
 #           {'label': '2016-2017', 'value': '2016'},
 #           {'label': '2017-2018', 'value': '2017'},
 #           {'label': '2018-2019', 'value': '2018'},
 #           {'label': '2019-2020', 'value': '2019'},
 #           {'label': '2020-2021', 'value': '2020'},
 #       ],

        options=option_list,
        searchable=True,
        id='team',
        value='all',
        placeholder="team"), style={'padding': 20}),

])


@app.callback(
    [Output('team', 'options')],
    [Input('season', 'value'),
    Input('team', 'value')
    ])

def update_dropdown(season,team):
    team_data2 = team_data[team_data["season"] == season]
    list_teams = team_data2["team_info"].unique()
    option_list=[]
    for i in list_teams :
        option_list.append(
            {"label" : i , "value" : i}
        )

    return [option_list]


@app.callback(
    [Output('graph', 'figure')],
    [Input('season', 'value'),
    Input('team', 'value')
    ])

def update_figure(season,team):

    if team=="all" :
        team_data2=team_data[team_data["season"]==season]

    else :
        specific_season=team_data[team_data["season"] == season]
        team_data2 = specific_season[specific_season["team_info"]==team]
    fig = shot_map(data, team_data2)
    return [fig]



if __name__ == '__main__':
    app.run_server(debug=True)
