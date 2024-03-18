
# pages/contact.py
from dash import html
from components.navbar import Navbar  # Adjust according to your file structure
from components.footer import Footer

def layout():
    return html.Div([
        Navbar(),
        html.Div([  # Wrapper div for centering
            html.H1("Contact Us", className="mt-5"),  # Margin top for spacing
            html.P('For feedback and collaborations, contact us at:'),
            html.Ul([
                html.Li('Email: cognosxx@gmail.com'),
                html.Li('GitHub: https://github.com/cognosx/publication-fetcher'),
            ]),
        ], className="center-block"),  # Apply custom CSS class
        Footer(),
    ])

