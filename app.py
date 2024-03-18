import dash
import dash_bootstrap_components as dbc
from flask_caching import Cache

# Font Awesome link 
FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
# Bootstrap Icons CDN
BI = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.4.0/font/bootstrap-icons.css"


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, FA], suppress_callback_exceptions=True)
cache = Cache(app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache-directory'})
server = app.server


# No app.layout definition here

if __name__ == '__main__':
    from index import server as application  # Adjust this line if your entry point is named differently
    application.run(debug=True, port=8050)  # Optional: specify port
