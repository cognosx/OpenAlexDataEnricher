import dash_bootstrap_components as dbc
from dash import html

def Navbar():
    navbar = dbc.Navbar(
        dbc.Container(
            [
                # Logo and Brand name on the left
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="/assets/cognosx_logo.png", height="60px")),
                            # dbc.Col(dbc.NavbarBrand("My Dash App", className="ml-2")),
                        ],
                        align="center",
                        className="flex-grow-0",  # Prevent the row from taking extra space
                        # no_gutters=True,
                    ),
                    href="/",
                ),
                # Navbar toggler for smaller screens
                dbc.NavbarToggler(id="navbar-toggler", className="ml-auto"),
                # Navbar menu items
                dbc.Collapse(
                    dbc.Nav(
                        [
                            # dbc.NavItem(dbc.NavLink("Home", href="/")),
                            dbc.NavItem(dbc.NavLink("Methodology", href="/methodology")),
                            # dbc.NavItem(dbc.NavLink("Contact", href="/contact")),
                        ],
                        className="ml-auto", # Aligns the nav items to the right of the navbar
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                    is_open=False,  # Ensures the menu starts collapsed on smaller screens
                ),
            ],
            fluid=False,  # Makes the container fluid to use the full width
        ),
        color="dark",
        dark=True,
        className="mb-4 sticky-navbar",  # Margin bottom for spacing
        sticky="top",
        # className="mb-5",  # Adds margin at the bottom for spacing, adjust as needed
    )
    return navbar
