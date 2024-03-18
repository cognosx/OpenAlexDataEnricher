from dash import html
import dash_bootstrap_components as dbc

def Footer():
    return html.Footer(
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.P('© 2024 CognosX.', className='text-center small'),
                        width=12
                    ),
                    dbc.Col(
                        html.P('For feedback and collaborations, contact us at:', className='text-center small'),
                        width=12
                    ),
                    dbc.Col(
                        html.A(
                            [html.I(className="fas fa-envelope mr-2", style={'color': '#ffa500'}), 'cognosxx@gmail.com'],
                            href='mailto:cognosxx@gmail.com',
                            className='text-center small d-block footer-link',
                            target="_blank"  # This will open the GitHub link in a new tab
                        ),
                        width=12
                    ),
                    dbc.Col(
                        html.A(
                            [html.I(className="fab fa-github mr-2", style={'color': '#ffa500'}), 'GitHub Repository'],
                            href='https://github.com/cognosx',
                            className='text-center small d-block footer-link',
                            target="_blank"  # This will open the GitHub link in a new tab
                        ),
                        width=12
                    ),
                ],
                justify="center",
            ),
            fluid=True,
            className="py-3"
        ),
        className="bg-light mt-5"
    )
