# -*- coding: utf-8 -*-
"""
Module doc string
"""
import pathlib
import re
import json
from datetime import datetime
import flask
import dash
import dash_table
import matplotlib.colors as mcolors
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from apps.dask_dash_app3.precomputing import add_stopwords
from dash.dependencies import Output, Input, State
from dateutil import relativedelta
from wordcloud import WordCloud, STOPWORDS
#from ldacomplaints import lda_analysis
from sklearn.manifold import TSNE
from app import app, cache

# embed_df = pd.read_csv(
#     "data/tsne_bigram_data.csv", index_col=0
# )  # Bigram embedding dataframe, with placeholder tsne values (at perplexity=3)
# vects_df = pd.read_csv(
#     "data/bigram_vectors.csv", index_col=0
# )  # Simple averages of GLoVe 50d vectors
# bigram_df = pd.read_csv("data/bigram_counts_data.csv", index_col=0)
bigram_ = pd.read_csv("./assets/trufeed.csv", index_col=0)

bigram_.set_index(['answers.0.values'], inplace=True)

# sort index for easy sorting/search-retrieval
bigram_.sort_index(inplace=True)
# dumpy pandas file
cars = {'ngram': [" "] * 20,
        'company': ['a']*10 + ['b']*10,
        'value': [0]*20
        }
compare = pd.DataFrame(cars, columns=['ngram', 'company', 'value'])


DATA_PATH = pathlib.Path(__file__).parent.resolve()
EXTERNAL_STYLESHEETS = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
#FILENAME = "data/trufeed.csv"
FILENAME_PRECOMPUTED = "precomputed.json"
PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"
#GLOBAL_DF = pd.read_csv(DATA_PATH.joinpath(FILENAME), header=0)
with open(DATA_PATH.joinpath(FILENAME_PRECOMPUTED)) as precomputed_file:
    PRECOMPUTED_LDA = json.load(precomputed_file)

"""
We are casting the whole column to datetime to make life easier in the rest of the code.
It isn't a terribly expensive operation so for the sake of tidyness we went this way.
"""
# GLOBAL_DF["Date received"] = pd.to_datetime(
#     GLOBAL_DF["Date received"], format="%m/%d/%Y"
# )

bigram_.createdAt = pd.to_datetime(
    bigram_.createdAt, format="%Y/%m/%d"
)
"""
In order to make the graphs more useful we decided to prevent some words from being included
"""
ADDITIONAL_STOPWORDS = [
    "XXXX",
    "XX",
    "xx",
    "xxxx",
    "n't",
    "Trans Union",
    "BOA",
    "Citi",
    "account",
]
for stopword in ADDITIONAL_STOPWORDS:
    STOPWORDS.add(stopword)

"""
Proudly written for Plotly by Vildly in 2019. info@vild.ly


The aim with this dashboard is to demonstrate how Plotly's Dash framework
can be used for NLP based data analysis. The dataset is open and contains
consumer complaints from US banks ranging from 2013 to 2017.

Users can select to run the dashboard with the whole dataset (which can be slow to run)
or a smaller subset which then is evenly and consistently sampled accordingly.

Once a data sample has been selected the user can select a bank to look into by
using the dropdown or by clicking one of the bars on the right with the top 10
banks listed by number of filed complaints. Naturally bigger banks tend to end
up in this top 10 since we do not adjust for number of customers.

Once a bank has been selected a histogram with the most commonly used words for
complaints to this specific bank is shown together with a scatter plot over all
complaints, grouped by autogenerated groups.

Users can at this point do deeper inspections into interesting formations or
clusters in the scatter plot by zooming and clicking dots.

Clicking on dots in the scatter plot will display a table showing the contents
of the selected complaint (each dot is a specific complaint).

It is worth mentioning that there is also a time frame selection slider which
allows the user to look at specific time windows if there is desire to do so.

To illustrate the usefulness of this dashboard we suggest looking at how the
wordcloud and scatter plot changes from Equifax if 2017 is included in the plots
or not.

Another potentially interesting find is that Capital One has a common word
other banks seem to lack, "Macy". It would appear that Capital One at some point
teamed up with popular retailer Macy's to offer their services. This company
might have been hugely popular and thus explaining it's high frequency of occurance
in complaints, or perhaps there are other reasons explaining the data.

Regardless of what caused these two mentioned outliers, it shows how a tool
such as this can aid an analyst in finding potentially interesting things to
dig deeper into.
"""

"""
#  Somewhat helpful functions
"""


def sample_data(dataframe, float_percent):
    """
    Returns a subset of the provided dataframe.
    The sampling is evenly distributed and reproducible
    """
    print("making a local_df data sample with float_percent: %s" % (float_percent))
    return dataframe.sample(frac=float_percent, random_state=1)


def get_complaint_count_by_company(dataframe):
    """ Helper function to get complaint counts for unique banks """
    company_counts = dataframe["country"].value_counts()
    # we filter out all banks with less than 11 complaints for now
    #company_counts = company_counts[company_counts > 10]
    values = company_counts.keys().tolist()
    counts = company_counts.tolist()
    return values, counts


def calculate_bank_sample_data(dataframe, sample_size, time_values):
    """ TODO """
    print(
        "making bank_sample_data with sample_size count: %s and time_values: %s"
        % (sample_size, time_values)
    )
    if time_values is not None:
        min_date = time_values[0]
        max_date = time_values[1]
        dataframe = dataframe[
            (dataframe["createdAt"] >= min_date)
            & (dataframe["createdAt"] <= max_date)
        ]
    company_counts = dataframe["country"].value_counts()
    company_counts_sample = company_counts[:sample_size]
    values_sample = company_counts_sample.keys().tolist()
    counts_sample = company_counts_sample.tolist()

    return values_sample, counts_sample


def make_local_df(selected_bank, time_values, n_selection):
    """ TODO """
    print("redrawing bank-wordcloud...")
    n_float = float(n_selection / 100)
    print("got time window:", str(time_values))
    print("got n_selection:", str(n_selection), str(n_float))
    # sample the dataset according to the slider
    local_df = sample_data(bigram_, n_float)
    if time_values is not None:
        time_values = time_slider_to_date(time_values)
        local_df = local_df[
            (local_df["createdAt"] >= time_values[0])
            & (local_df["createdAt"] <= time_values[1])
        ]
    if selected_bank:
        local_df = local_df[local_df["country"] == selected_bank]
        add_stopwords(selected_bank)
    return local_df


def make_marks_time_slider(mini, maxi):
    """
    A helper function to generate a dictionary that should look something like:
    {1420066800: '2015', 1427839200: 'Q2', 1435701600: 'Q3', 1443650400: 'Q4',
    1451602800: '2016', 1459461600: 'Q2', 1467324000: 'Q3', 1475272800: 'Q4',
     1483225200: '2017', 1490997600: 'Q2', 1498860000: 'Q3', 1506808800: 'Q4'}
    """
    step = relativedelta.relativedelta(days=+1)
    start = datetime(year=mini.year, month=3, day=1)
    end = datetime(year=maxi.year, month=maxi.month, day=30)
    ret = {}

    current = start
    while current <= end:
        current_str = int(current.timestamp())
        if current.day == 1 and current.month == 3:
            ret[current_str] = {
                "label": str(current.day)+'/' + str(current.month)+'/' + str(current.year),
                "style": {"font-weight": "bold"},
            }
        elif current.day == 15 and current.month == 3:
            ret[current_str] = {
                "label": str(current.day)+'/' + str(current.month)+'/' + str(current.year),
                "style": {"font-weight": "light", "font-size": 7},
            }
        elif current.day == 1 and current.month == 4:
            ret[current_str] = {
                "label": str(current.day)+'/' + str(current.month)+'/' + str(current.year),
                "style": {"font-weight": "light", "font-size": 7},
            }
        elif current.day == 15 and current.month == 4:
            ret[current_str] = {
                "label": str(current.day)+'/' + str(current.month)+'/' + str(current.year),
                "style": {"font-weight": "light", "font-size": 7},
            }
        elif current.day == 30 and current.month == 4:
            ret[current_str] = {
                "label": str(current.day)+'/' + str(current.month)+'/' + str(current.year),
                "style": {"font-weight": "bold"},
            }
        else:
            pass
        current += step
    # print(ret)
    return ret


def time_slider_to_date(time_values):
    """ TODO """
    min_date = datetime.fromtimestamp(time_values[0]).strftime("%c")
    max_date = datetime.fromtimestamp(time_values[1]).strftime("%c")
    print("Converted time_values: ")
    print("\tmin_date:", time_values[0], "to: ", min_date)
    print("\tmax_date:", time_values[1], "to: ", max_date)
    return [min_date, max_date]


def make_options_bank_drop(values):
    """
    Helper function to generate the data format the dropdown dash component wants
    """
    ret = []
    for value in values:
        ret.append({"label": value, "value": value})
    return ret


def populate_lda_scatter(tsne_df, df_top3words, df_dominant_topic):
    """Calculates LDA and returns figure data you can jam into a dcc.Graph()"""
    mycolors = np.array(
        [color for name, color in mcolors.TABLEAU_COLORS.items()])

    # for each topic we create a separate trace
    traces = []
    for topic_id in df_top3words["topic_id"]:
        tsne_df_f = tsne_df[tsne_df.topic_num == topic_id]
        cluster_name = ", ".join(
            df_top3words[df_top3words["topic_id"]
                         == topic_id]["words"].to_list()
        )
        trace = go.Scatter(
            name=cluster_name,
            x=tsne_df_f["tsne_x"],
            y=tsne_df_f["tsne_y"],
            mode="markers",
            hovertext=tsne_df_f["doc_num"],
            marker=dict(
                size=6,
                # set color equal to a variable
                color=mycolors[tsne_df_f["topic_num"]],
                colorscale="Viridis",
                showscale=False,
            ),
        )
        traces.append(trace)

    layout = go.Layout({"title": "Region clustering"})

    return {"data": traces, "layout": layout}


def plotly_wordcloud(data_frame):
    """A wonderful function that returns figure data for three equally
    wonderful plots: wordcloud, frequency histogram and treemap"""
    complaints_text = list(data_frame["answers.10.values"].dropna().values)

    if len(complaints_text) < 1:
        return {}, {}, {}

    # join all documents in corpus
    text = " ".join(list(complaints_text))

    word_cloud = WordCloud(stopwords=set(STOPWORDS),
                           max_words=100, max_font_size=90)
    word_cloud.generate(text)

    word_list = []
    freq_list = []
    fontsize_list = []
    position_list = []
    orientation_list = []
    color_list = []
    freqs = []

    for (word, freq), fontsize, position, orientation, color in word_cloud.layout_:
        word_list.append(word)
        freq_list.append(freq)
        fontsize_list.append(fontsize)
        position_list.append(position)
        orientation_list.append(orientation)
        color_list.append(color)
        freqs.append(freq*100)

    # get the positions
    x_arr = []
    y_arr = []
    for i in position_list:
        x_arr.append(i[0])
        y_arr.append(i[1])

    # get the relative occurence frequencies
    # new_freq_list = []
    # for i in freq_list:
    #     new_freq_list.append(i * 80)
    freqs = pd.Series(freqs, dtype=object).fillna(0).tolist()

    f = dict(size=freqs, color=color_list)
    trace = go.Scatter(
        x=x_arr,
        y=y_arr,
        textfont=f,
        hoverinfo="text",
        textposition="top center",
        hovertext=["{0} - {1}".format(w, f)
                   for w, f in zip(word_list, freq_list)],
        mode="text",
        text=word_list,
    )

    layout = go.Layout(
        {
            "xaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "automargin": True,
                "range": [-100, 250],
            },
            "yaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "automargin": True,
                "range": [-100, 450],
            },
            "margin": dict(t=20, b=20, l=10, r=10, pad=4),
            "hovermode": "closest",
        }
    )

    wordcloud_figure_data = {"data": [trace], "layout": layout}
    word_list_top = word_list[:25]
    word_list_top.reverse()
    freq_list_top = freq_list[:25]
    freq_list_top.reverse()

    frequency_figure_data = {
        "data": [
            {
                "y": word_list_top,
                "x": freq_list_top,
                "type": "bar",
                "name": "",
                "orientation": "h",
            }
        ],
        "layout": {"height": "550", "margin": dict(t=20, b=20, l=100, r=20, pad=4)},
    }
    treemap_trace = go.Treemap(
        labels=word_list_top, parents=[""] * len(word_list_top), values=freq_list_top
    )
    treemap_layout = go.Layout({"margin": dict(t=10, b=10, l=5, r=5, pad=4)})
    treemap_figure = {"data": [treemap_trace], "layout": treemap_layout}

    return wordcloud_figure_data, frequency_figure_data, treemap_figure


"""
#  Page layout and contents

In an effort to clean up the code a bit, we decided to break it apart into
sections. For instance: LEFT_COLUMN is the input controls you see in that gray
box on the top left. The body variable is the overall structure which most other
sections go into. This just makes it ever so slightly easier to find the right
spot to add to or change without having to count too many brackets.
"""

NAVBAR = dbc.Navbar(
    children=[
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(
                        dbc.NavbarBrand(
                            "Trufeedback Data Analytics", className="ml-2")
                    ),
                ],
                align="center",
                no_gutters=True,
            ),
            href="https://plot.ly",
        )
    ],
    color="dark",
    dark=True,
    sticky="top",
)

LEFT_COLUMN = dbc.Jumbotron(
    [
        html.H4(children="Select country & dataset size",
                className="display-5"),
        html.Hr(className="my-2"),
        html.Label("Select percentage of dataset", className="lead"),
        html.P(
            "(Lower is faster. Higher is more precise)",
            style={"fontSize": 10, "font-weight": "lighter"},
        ),
        dcc.Slider(
            id="n-selection-slider",
            min=1,
            max=100,
            step=1,
            marks={
                0: "0%",
                10: "",
                20: "20%",
                30: "",
                40: "40%",
                50: "",
                60: "60%",
                70: "",
                80: "80%",
                90: "",
                100: "100%",
            },
            value=20,
        ),
        html.Label("Select country", style={
                   "marginTop": 50}, className="lead"),
        html.P(
            "(You can use the dropdown or click the barchart on the right)",
            style={"fontSize": 10, "font-weight": "lighter"},
        ),
        dcc.Dropdown(
            id="bank-drop", clearable=False, style={"marginBottom": 50, "font-size": 12}
        ),
        html.Label("Select time frame", className="lead"),
        html.Div(dcc.RangeSlider(id="time-window-slider"),
                 style={"marginBottom": 50}),
        html.P(
            "(You can define the time frame down to month granularity)",
            style={"fontSize": 10, "font-weight": "lighter"},
        ),
    ]
)

LDA_PLOT = dcc.Loading(
    id="loading-lda-plot", children=[dcc.Graph(id="tsne-lda")], type="default"
)
LDA_TABLE = html.Div(
    id="lda-table-block",
    children=[
        dcc.Loading(
            id="loading-lda-table",
            children=[
                dash_table.DataTable(
                    id="lda-table",
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Text"},
                            "textAlign": "left",
                            "whiteSpace": "normal",
                            "height": "auto",
                            "min-width": "50%",
                        }
                    ],
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "rgb(243, 246, 251)",
                        }
                    ],
                    style_cell={
                        "padding": "16px",
                        "whiteSpace": "normal",
                        "height": "auto",
                        "max-width": "0",
                    },
                    style_header={"backgroundColor": "white",
                                  "fontWeight": "bold"},
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    filter_action="native",
                    page_action="native",
                    page_current=0,
                    page_size=5,
                    columns=[],
                    data=[],
                )
            ],
            type="default",
        )
    ],
    style={"display": "none"},
)

LDA_PLOTS = [
    dbc.CardHeader(html.H4("Regions of Participants", style={'text-align': 'center', 'font-weight': 800}), style={
                   "border-radius": "20px 20px 0px 0px"}),
    dbc.Alert(
        "Not enough data to render LDA plots, please adjust the filters",
        id="no-data-alert-lda",
        color="warning",
        style={"display": "none"},
    ),
    dbc.CardBody(
        [
            html.P(
                "Click on a  point in the scatter to explore that specific region",
                className="mb-0",
            ),
            html.P(
                "(not affected by sample size or time frame selection)",
                style={"fontSize": 10, "font-weight": "lighter"},
            ),
            LDA_PLOT,
            html.Hr(),
            LDA_TABLE,
        ]
    ),
]
WORDCLOUD_PLOTS = [
    dbc.CardHeader(html.H4("Most frequently used words in survey", style={'text-align': 'center', 'font-weight': 800}),
                   style={"border-radius": "20px 20px 0px 0px"}),
    dbc.Alert(
        "Not enough data to render these plots, please adjust the filters",
        id="no-data-alert",
        color="warning",
        style={"display": "none"},
    ),
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-frequencies",
                            children=[dcc.Graph(id="frequency_figure")],
                            type="default",
                        )
                    ),
                    dbc.Col(
                        [
                            dcc.Tabs(
                                id="tabs",
                                children=[
                                    dcc.Tab(
                                        label="Treemap",
                                        children=[
                                            dcc.Loading(
                                                id="loading-treemap",
                                                children=[
                                                    dcc.Graph(id="bank-treemap")],
                                                type="default",
                                            )
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Wordcloud",
                                        children=[
                                            dcc.Loading(
                                                id="loading-wordcloud",
                                                children=[
                                                    dcc.Graph(
                                                        id="bank-wordcloud")
                                                ],
                                                type="default",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ],
                        md=8,
                    ),
                ]
            )
        ]
    ),
]

TOP_BANKS_PLOT = [
    dbc.CardHeader(html.H4("Participants Distribution per country", style={'text-align': 'center', 'font-weight': 800}), style={
                   "border-radius": "20px 20px 0px 0px"}),
    dbc.CardBody(
        [
            dcc.Loading(
                id="loading-banks-hist",
                children=[
                    dbc.Alert(
                        "Not enough data to render this plot, please adjust the filters",
                        id="no-data-alert-bank",
                        color="warning",
                        style={"display": "none"},
                    ),
                    dcc.Graph(id="bank-sample"),
                ],
                type="default",
            )
        ],
        style={"marginTop": 0, "marginBottom": 0},
    ),
]

TOP_BIGRAM_PLOT = [
    dbc.CardHeader(html.H4("Participants Size By Profession", style={'text-align': 'center', 'font-weight': 800}),
                   style={"border-radius": "20px 20px 0px 0px"}),
    dbc.CardBody(
        [
            dcc.Loading(
                id="loading-bigrams-scatter",
                children=[
                    dbc.Alert(
                        "Something's gone wrong! Give us a moment, but try loading this page again if problem persists.",
                        id="no-data-alert-bigrams",
                        color="warning",
                        style={"display": "none"},
                    ),
                    dbc.Row(
                        [
                            dbc.Col(html.P(["Choose a country:"]), md=6),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id="bigrams-perplex-dropdown",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in bigram_.country.unique()
                                        ],
                                        value="Nigeria",
                                    )
                                ],
                                md=3,
                            ),
                        ]
                    ),
                    dcc.Graph(id="bigrams-scatter"),
                ],
                type="default",
            )
        ],
        style={"marginTop": 0, "marginBottom": 0},
    ),
]

TOP_BIGRAM_COMPS = [
    dbc.CardHeader(html.H4("Participants Club Choice per Country", style={'text-align': 'center', 'font-weight': 800}),
                   style={"border-radius": "20px 20px 0px 0px"}),
    dbc.CardBody(
        [
            dcc.Loading(
                id="loading-bigrams-comps",
                children=[
                    dbc.Alert(
                        "Something's gone wrong! Give us a moment, but try loading this page again if problem persists.",
                        id="no-data-alert-bigrams_comp",
                        color="warning",
                        style={"display": "none"},
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.P("Choose 2 countries to compare:"), md=12),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id="bigrams-comp_1",
                                        options=[
                                            {"label": i, "value": i}
                                            for i in bigram_.country.unique()
                                        ],
                                        value="Turkey",
                                    )
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id="bigrams-comp_2",
                                        options=[
                                            {"label": i, "value": i}
                                            for i in bigram_.country.unique()
                                        ],
                                        value="Nigeria",
                                    )
                                ],
                                md=6,
                            ),
                        ]
                    ),
                    dcc.Graph(id="bigrams-comps"),
                ],
                type="default",
            )
        ],
        style={"marginTop": 0, "marginBottom": 0, "border-radius": "30px"},
    ),
]

BODY = dbc.Container(
    [
        dbc.Row([dbc.Col(dbc.Card(TOP_BIGRAM_COMPS, style={"border-radius": "20px", "box-shadow": "0px 0px 8px 8px #ebe9e8",
                                                           "-webkit-box-shadow": "0px 0px 8px 8px #ebe9e8"}))],
                style={"marginTop": 30}),
        dbc.Row([dbc.Col(dbc.Card(TOP_BIGRAM_PLOT, style={"border-radius": "20px", "box-shadow": "0px 0px 8px 8px #ebe9e8",
                                                          "-webkit-box-shadow": "0px 0px 8px 8px #ebe9e8"})), ],
                style={"marginTop": 30}),
        dbc.Row(
            [
                dbc.Col(LEFT_COLUMN, md=4, align="center"),
                dbc.Col(dbc.Card(TOP_BANKS_PLOT, style={
                        "border-radius": "20px", "box-shadow": "0px 0px 8px 8px #ebe9e8",
                        "-webkit-box-shadow": "0px 0px 8px 8px #ebe9e8"}), md=8),
            ],
            style={"marginTop": 30},
        ),
        dbc.Card(WORDCLOUD_PLOTS, style={
            "border-radius": "20px", "border-radius": "20px", "box-shadow": "0px 0px 8px 8px #ebe9e8",
            "-webkit-box-shadow": "0px 0px 8px 8px #ebe9e8"}),
        dbc.Row([dbc.Col([dbc.Card(LDA_PLOTS, style={
                "border-radius": "20px", "border-radius": "20px", "box-shadow": "0px 0px 8px 8px #ebe9e8",
                "-webkit-box-shadow": "0px 0px 8px 8px #ebe9e8"})])], style={"marginTop": 50, "marginBottom": 100}),
    ],
    className="mt-12",
)


# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# server = app.server  # for Heroku deployment

# app.layout = html.Div(children=[NAVBAR, BODY])


"""
#  Callbacks
"""


@app.callback(
    Output("bigrams-scatter",
           "figure"), [Input("bigrams-perplex-dropdown", "value")],
)
def populate_bigram_scatter(perplexity):

    h = bigram_[bigram_["country"] ==
                perplexity]['answers.3.values'].value_counts().values
    t = bigram_[bigram_["country"] ==
                perplexity]['answers.3.values'].value_counts().index.values

    # reduce the size of plot . maximum is 20. (take first 20)
    if len(h) > 15:
        h = h[:15]
        t = t[:15]

    # use TSNe
    tsne = TSNE(n_components=3, random_state=0)
    projections = tsne.fit_transform(h.reshape(-1, 1), )
   # X_embedded = TSNE(n_components=2, perplexity=3).fit_transform(h.reshape(-1, 1))

    plotters = {'x1': projections[:, 0],
                'x2': projections[:, 1],
                'x3': projections[:, 2],
                'labels': t,
                'size': h
                }

    #embed_df["tsne_1"] = X_embedded[:, 0]
    #embed_df["tsne_2"] = X_embedded[:, 1]
    fig = px.scatter_3d(


        plotters, x='x1', y='x2', z='x3', size='size', size_max=100, color="size", text='labels',
        labels={"words": "Avg. Length<BR>(words)"}, color_continuous_scale=px.colors.sequential.Sunsetdark
        # X_embedded,
        # x="tsne_1",
        # y="tsne_2",
        # hover_name="bigram",
        # text="bigram",
        # size=t,
        # color=t,
        # size_max=45,
        # template="plotly_white",
        # title="Bigram similarity and frequency",
        # labels={"words": "Avg. Length<BR>(words)"},
        # color_continuous_scale=px.colors.sequential.Sunsetdark,
    )
    # fig.update_traces(marker=dict(line=dict(width=1, color="Gray")))

    camera = dict(
        up=dict(x=5, y=3, z=2),
        center=dict(x=0, y=0, z=0),
        eye=dict(x=1.25, y=1.25, z=1.25)
    )

    fig.update_layout(scene_camera=camera)
    fig.update_layout(
        autosize=True,
        height=800,
        font_size=12,
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            zaxis=dict(showticklabels=False),
        )
    )

    return fig


@app.callback(
    Output("bigrams-comps", "figure"),
    [Input("bigrams-comp_1", "value"), Input("bigrams-comp_2", "value")],
)
def comp_bigram_comparisons(comp_first, comp_second):
    # comp_list = [comp_first, comp_second]
    # temp_df = bigram_df[bigram_df.company.isin(comp_list)]
    # temp_df.loc[temp_df.company == comp_list[-1], "value"] = -temp_df[
    #     temp_df.company == comp_list[-1]
    # ].value.values

    compare.loc[compare.company == 'a', 'company'] = comp_first
    compare.loc[compare.company == 'b', 'company'] = comp_second

    # second componet

    sizes = bigram_.loc[(comp_second)].groupby(
        ['answers.2.values']).size().sort_values(ascending=False)[:10].values.shape[0]
    if sizes > 0:
        sizeNew = 10+sizes
        compare.loc[10:sizeNew-1, 'ngram'] = bigram_.loc[(comp_second)].groupby(
            ['answers.2.values']).size().sort_values(ascending=False)[:sizes].index
        compare.loc[10:sizeNew-1, 'value'] = bigram_.loc[(comp_second)].groupby(
            ['answers.2.values']).size().sort_values(ascending=False)[:sizes].values

    # first histo

    size = bigram_.loc[(comp_first)].groupby(['answers.2.values']).size(
    ).sort_values(ascending=False)[:10].values.shape[0]
    if size > 0:
        compare.loc[:size-1, 'ngram'] = bigram_.loc[(comp_first)].groupby(
            ['answers.2.values']).size().sort_values(ascending=False)[:size].index
        compare.loc[:size-1, 'value'] = bigram_.loc[(comp_first)].groupby(
            ['answers.2.values']).size().sort_values(ascending=False)[:size].values

    #print("I am checking my work .......daaaaaaa")
    # compare.head()

    fig = px.bar(
        compare,
        title="Comparison: " + comp_first + " | " + comp_second,
        x="ngram",
        y="value",
        color="company",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"company": "Company:", "ngram": "Football Clubs"},
        hover_data="",
    )
    fig.update_layout(legend=dict(x=0.1, y=1.1), legend_orientation="h")
    fig.update_yaxes(title="", showticklabels=False)
    fig.data[0]["hovertemplate"] = fig.data[0]["hovertemplate"][:-14]
    return fig


@app.callback(
    [
        Output("time-window-slider", "marks"),
        Output("time-window-slider", "min"),
        Output("time-window-slider", "max"),
        Output("time-window-slider", "step"),
        Output("time-window-slider", "value"),
    ],
    [Input("n-selection-slider", "value")],
)
def populate_time_slider(value):
    """
    Depending on our dataset, we need to populate the time-slider
    with different ranges. This function does that and returns the
    needed data to the time-window-slider.
    """
    value += 0
    min_date = bigram_["createdAt"].min()
    max_date = bigram_["createdAt"].max()

    marks = make_marks_time_slider(min_date, max_date)
    min_epoch = list(marks.keys())[0]
    max_epoch = list(marks.keys())[-1]

    return (
        marks,
        min_epoch,
        max_epoch,
        (max_epoch - min_epoch) / (len(list(marks.keys())) * 3),
        [min_epoch, max_epoch],
    )


@app.callback(
    Output("bank-drop", "options"),
    [Input("time-window-slider", "value"),
     Input("n-selection-slider", "value")],
)
def populate_bank_dropdown(time_values, n_value):
    """ TODO """
    print("bank-drop: TODO USE THE TIME VALUES AND N-SLIDER TO LIMIT THE DATASET")
    if time_values is not None:
        pass
    n_value += 1
    bank_names, counts = get_complaint_count_by_company(bigram_)
    counts.append(1)
    return make_options_bank_drop(bank_names)


@app.callback(
    [Output("bank-sample", "figure"), Output("no-data-alert-bank", "style")],
    [Input("n-selection-slider", "value"),
     Input("time-window-slider", "value")],
)
def update_bank_sample_plot(n_value, time_values):
    """ TODO """
    print("redrawing bank-sample...")
    print("\tn is:", n_value)
    print("\ttime_values is:", time_values)
    if time_values is None:
        return [{}, {"display": "block"}]
    n_float = float(n_value / 100)
    bank_sample_count = 10
    local_df = sample_data(bigram_, n_float)
    min_date, max_date = time_slider_to_date(time_values)
    values_sample, counts_sample = calculate_bank_sample_data(
        local_df, bank_sample_count, [min_date, max_date]
    )
    diff = max(counts_sample) - min(counts_sample)
    mins = min(counts_sample)
    counts_sample = [(i-mins)/diff for i in counts_sample]
    data = [
        {
            "x": values_sample,
            "y": counts_sample,
            "text": values_sample,
            "textposition": "top outside",
            "type": "line",
            "name": "",
            "mode": "lines+text+markers",
            "textweight": "bold"
        }
    ]
    layout = {
        "autosize": False,
        "margin": dict(t=10, b=10, l=40, r=0, pad=4),
        "xaxis": {"showticklabels": False},
    }
    print("redrawing bank-sample...done")
    #print("I am counting")
    print(counts_sample)
    return [{"data": data, "layout": layout}, {"display": "none", }]


@app.callback(
    [
        Output("lda-table", "data"),
        Output("lda-table", "columns"),
        Output("tsne-lda", "figure"),
        Output("no-data-alert-lda", "style"),
    ],
    [Input("bank-drop", "value"), Input("time-window-slider", "value")],
)
def update_lda_table(selected_bank, time_values):
    """ Update LDA table and scatter plot based on precomputed data """

    if selected_bank in PRECOMPUTED_LDA:
        df_dominant_topic = pd.read_json(
            PRECOMPUTED_LDA[selected_bank]["df_dominant_topic"]
        )
        tsne_df = pd.read_json(PRECOMPUTED_LDA[selected_bank]["tsne_df"])
        df_top3words = pd.read_json(
            PRECOMPUTED_LDA[selected_bank]["df_top3words"])
    else:
        return [[], [], {}, {}]

    lda_scatter_figure = populate_lda_scatter(
        tsne_df, df_top3words, df_dominant_topic)

    columns = [{"name": i, "id": i} for i in df_dominant_topic.columns]
    data = df_dominant_topic.to_dict("records")

    return (data, columns, lda_scatter_figure, {"display": "none"})


@app.callback(
    [
        Output("bank-wordcloud", "figure"),
        Output("frequency_figure", "figure"),
        Output("bank-treemap", "figure"),
        Output("no-data-alert", "style"),
    ],
    [
        Input("bank-drop", "value"),
        Input("time-window-slider", "value"),
        Input("n-selection-slider", "value"),
    ],
)
def update_wordcloud_plot(value_drop, time_values, n_selection):
    """ Callback to rerender wordcloud plot """
    local_df = make_local_df(value_drop, time_values, n_selection)
    wordcloud, frequency_figure, treemap = plotly_wordcloud(local_df)
    alert_style = {"display": "none"}
    if (wordcloud == {}) or (frequency_figure == {}) or (treemap == {}):
        alert_style = {"display": "block"}
    print("redrawing bank-wordcloud...done")
    return (wordcloud, frequency_figure, treemap, alert_style)


@app.callback(
    [Output("lda-table", "filter_query"), Output("lda-table-block", "style")],
    [Input("tsne-lda", "clickData")],
    [State("lda-table", "filter_query")],
)
def filter_table_on_scatter_click(tsne_click, current_filter):
    """ TODO """
    if tsne_click is not None:
        selected_complaint = tsne_click["points"][0]["hovertext"]
        if current_filter != "":
            filter_query = (
                "({Document_No} eq "
                + str(selected_complaint)
                + ") || ("
                + current_filter
                + ")"
            )
        else:
            filter_query = "{Document_No} eq " + str(selected_complaint)
        print("current_filter", current_filter)
        return (filter_query, {"display": "block"})
    return ["", {"display": "none"}]


@app.callback(Output("bank-drop", "value"), [Input("bank-sample", "clickData")])
def update_bank_drop_on_click(value):
    """ TODO """
    if value is not None:
        selected_bank = value["points"][0]["x"]
        return selected_bank
    return "Turkey"


# if __name__ == "__main__":
#     app.run_server(debug=True)

def layout():
    return html.Div(children=[BODY])
