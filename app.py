# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import eda
import plotly.express as px
import pandas as pd
from collections import defaultdict
from ast import literal_eval
from datetime import date
from datetime import datetime, timedelta


def get_nth_date(n=1):
    date = datetime.today() - timedelta(days=n)
    if len(str(date.day)) == 1:
        day = f'0{date.day}'
    else:
        day = str(date.day)
    if len(str(date.month)) == 1:
        month = f"0{date.month}"
    else:
        month = str(date.month)
    return f"2021/{month}/{day} 00:00:00"


def hashtag_figs(df):
    def all_hashtags(df, title='All hashtags'):
        hashtags = defaultdict(int)
        for idx, row in df.iterrows():
            hts = literal_eval(row.hashtags)
            for ht in hts:
                hashtags[ht] += 1

        ht_df = pd.DataFrame(
            {"hashtag": list(hashtags.keys()), "count": list(hashtags.values())})
        return px.bar(ht_df, x='hashtag', y='count', title=title)

    def todays_hashtags(df):
        today_df = df[df['received_at'] > get_nth_date(n=1)]
        return all_hashtags(today_df, title="Today's hashtags")

    def weeks_hashtags(df):
        week_df = df[df['received_at'] > get_nth_date(n=7)]
        return all_hashtags(week_df, title="Past Week's hashtags")

    return all_hashtags(df), todays_hashtags(df), weeks_hashtags(df)


def username_figs(df):
    def all_usernames(df, title="All usernames"):
        usernames = df['username'].value_counts()
        u_df = pd.DataFrame(
            {"username": list(usernames.index), "count": list(usernames.values)})
        return px.bar(u_df, x='username', y='count', title=title)

    def todays_users(df):
        today_df = df[df['received_at'] > get_nth_date(n=1)]
        return all_usernames(today_df, title="Today's usernames")

    def weeks_users(df):
        week_df = df[df['received_at'] > get_nth_date(n=7)]
        return all_usernames(week_df, title="Past Week's usernames")

    return all_usernames(df), todays_users(df), weeks_users(df)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

fig, df = eda.main()
fig1, fig2, fig3 = hashtag_figs(df)
fig4, fig5, fig6 = username_figs(df)

app.layout = html.Div(children=[
    html.H1(children='Twitter bots and muppets displaying anti-Armenian content'),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
    dcc.Graph(
        id='example-graph1',
        figure=fig1
    ),
    dcc.Graph(
        id='example-graph2',
        figure=fig2
    ),
    dcc.Graph(
        id='example-graph3',
        figure=fig3
    ),
    dcc.Graph(
        id='example-graph4',
        figure=fig4
    ),
    dcc.Graph(
        id='example-graph5',
        figure=fig5
    ),
    dcc.Graph(
        id='example-graph6',
        figure=fig6
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
