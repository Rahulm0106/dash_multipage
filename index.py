from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from app import app
from apps import app1, displayAll,app3,app4,app5,app6,app7,app8,home
import dash_table_experiments as dt
import base64
import os
from flask import send_from_directory



server=app.server


#after

app.layout=html.Div([html.Link(
    rel='stylesheet',
    href='/static/custom.css'),
    dcc.Location(id='url', refresh=False),
    html.Nav(id='nav',
    className='navbar navbar-default',children=html.Div(className='container-fluid',children=[html.Div(
            className='navbar-header',children=html.Div(className="navbar-brand",children='Analytics App')
        ),
        html.Ul(className='nav navbar-nav',children=[
        html.Li(children=html.A(href="/apps/app1",children="Home")),
        html.Li(children=html.A(href="/apps/displayAll",children="Visualization")),
        html.Li(children=html.A(href="/apps/app3",children="Natural Language Processing")),
        #html.Li(children=html.A(href="/apps/app4",children="app4")),
        #html.Li(children=html.A(href="/apps/app5",children="app5")),
        html.Li(children=html.A(href="/apps/app6",children="Statistical models")),
        #html.Li(children=html.A(href="/apps/app7",children="HelpDesk stats")),
        html.Li(children=html.A(href="/apps/app8",children="Machine Learning"))
        ]),
        html.P(className='text-right vertical-center',children=html.A(className='text-muted',href="https://plot.ly/products/dash/",children='Created using Dash by Plotly'))
        ])
    )
    ,html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'})
    ,html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/app1':
        return app1.layout()
    elif pathname == '/apps/displayAll':
        return displayAll.layout()
    elif pathname == '/apps/app3':
        return app3.layout()
    elif pathname == '/apps/app4':
        return app4.layout()
    elif pathname == '/apps/app5':
        return app5.layout()
    elif pathname == '/apps/app6':
        return app6.layout()
    elif pathname == '/apps/app7':
        return app7.layout()
    elif pathname == '/apps/app8':
        return app8.layout()
    else:
        return app1.layout()



@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)







if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=True)
