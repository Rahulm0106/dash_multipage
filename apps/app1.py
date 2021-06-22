from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from flask import url_for

from app import app

def layout():
    return html.Div([
            html.Div(className='Row',children=[
                html.Div(className='col-lg-12 page-header',children=[
                    html.H3(className='text-center',children='Analytics Platform TruFeedback')])
            ]),
            html.Div(className='Row',children=[
                html.Div(className='col-lg-2'),
                html.Div(className='col-lg-8',children=[
                    
                    html.Div(className='col-lg-6',children=[
                      html.A([html.Img(className='img-responsive',src='/static/plotly(8).png')],href="/apps/displayAll"),
                      html.A(  [html.Img(className='img-responsive',src='/static/plotly(9).png')],  href="/apps/app3"  )
                    ]),
                    html.Div(className='col-lg-6',children=[
                       dcc.Link ( children= [html.Img(className='img-responsive',src='/static/plotly(10).png')], href="/apps/displayAll"),
                       html.A( [html.Img(className='img-responsive',src='/static/plotly(12).png')], href="/apps/app8"  )
                    ])
                ]),
                html.Div(className='col-lg-2')
            ])
        ])


