from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

from app import app

def layout():
    return html.Div([
    html.H3('Home'),
    html.Div([dcc.Link('Commercial App', href='/apps/app1',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('Analitic App', href='/apps/displayAll',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('Sales App', href='/apps/app3',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('IT devices', href='/apps/app4',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('United IT devices', href='/apps/app5',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('CBD', href='/apps/app6',style={ 'text-decoration': 'underline','color':'#1F77B4'})]),
    html.Div([dcc.Link('IT queue', href='/apps/app7',style={ 'text-decoration': 'underline','color':'#1F77B4'})])
],style={'text-align': 'center','height':'500px'})

