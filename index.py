# index.py
import os 
from dash import Dash, html, dcc, callback, Input, Output
from app import app, cache
from pages import main
from pages.main import layout as main_layout
from pages import methodology
from pages import contact

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return main_layout()
    elif pathname == '/methodology':
        return methodology.layout()
    elif pathname == '/contact':
        return contact.layout()
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
