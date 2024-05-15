# Import required libraries
import dash
import pandas as pd
import requests
from dash import dcc, html, dash_table, callback_context, Input, Output, State, no_update, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import re
from flask_caching import Cache
from app import app, cache  # Importing app and cache here

# Import custom components (adjust according to your file structure)
from components.navbar import Navbar
from components.footer import Footer

# Define the layout
def layout():
    return dbc.Container([
        Navbar(),  # Use the Navbar component

        dbc.Row(dbc.Col(html.H1('OpenAlex Data Enricher'), className="d-flex justify-content-center")),
        dbc.Row(dbc.Col(html.P("Enter search parameters to fetch and display publications."), className="d-flex justify-content-center")),
        dbc.Row(
            dbc.Col([
                dcc.Input(id='search-input', type='text', placeholder='e.g., https://api.openalex.org/works?filter=authorships.institutions.continent:q15,publication_year:2024-2024,title_and_abstract.search:hiv+OR+aids+OR+%22Human+Immunodeficiency+Virus%22+OR+%22HIV/AIDS%22+OR+%22Human+Immunodeficiency+Viruses%22+OR+%22human+immuno-deficiency+virus%22+OR+%22Acquired+Immune+Deficiency+Syndrome%22+OR+%22Acquired+Immunodeficiency+Syndrome%22,type:types/review', debounce=True, className="me-2"),
                html.Button('Submit', id='submit-button', n_clicks=0, className="submit-button")
            ], width=12, className="d-flex justify-content-center"),
            justify="center"
        ),
        dbc.Row(dbc.Col(dbc.Checklist(
            options=[
                {'label': 'Include Crossref Data', 'value': 'crossref'},
                {'label': 'Include Altmetric Data', 'value': 'altmetric'}
            ],
            value=[],
            id='data-options',
            inline=True
        ), className="d-flex justify-content-center")),
        dbc.Row(dbc.Col(dbc.Alert(id='input-alert', color="warning", className="mt-3", style={"display": "none"}))),
        dbc.Row(dbc.Col(dbc.Alert(id='status-alert', children="Valid search. Fetching publications, please wait...", color="info", className="mt-3", style={"display": "none"}))),
        dbc.Row(dbc.Col(dbc.Alert(id='status-alert-output', children="Publications ready. You can now view or download the list.", color="info", className="mt-3", style={"display": "none"}))),

        dbc.Row(dbc.Col(html.Div(id='spinner-container', children=[dbc.Spinner(size="lg", color="primary", type="border")], style={'display': 'none'}))),
        dbc.Row(dbc.Col(html.Div(id='spinner-container-closed', children=[dbc.Spinner(size="lg", color="primary", type="border")], style={'display': 'none'}))),

        dbc.Row(dbc.Col(html.Button('Download Publications List', id='download-button', disabled=True, className="mt-3", style={'display': 'none'}))),
        dcc.Download(id='download-link'),

        dcc.Store(id='stored-data'),
        dcc.Store(id='stored-search-query'),

        html.Div(id='table-container', className="mt-3"),

        Footer(),  # Use the Footer component
    ], fluid=True, className="py-3")

############# Functions to fetch data ############################

def clean_doi(doi):
    """
    Function to transform DOIs to the required format.
    Converts https://doi.org/10.21203/rs.3.pex-2537/v1 to 10.21203/rs.3.pex-2537/v1.
    """
    if doi and doi.startswith("https://doi.org/"):
        return doi.replace("https://doi.org/", "")
    return doi

@cache.memoize()
def fetch_openalex_publications(search_query, max_results=100000):
    works = []
    per_page = 25
    cursor = '*'
    while True:
        url = f"{search_query}&per-page={per_page}&cursor={cursor}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            if not results:
                break
            works.extend(results)
            if len(works) >= max_results:
                break
            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                break
        except requests.RequestException as e:
            print(f"Error fetching OpenAlex publications: {e}")
            break
    return works

@cache.memoize()
def fetch_crossref_metadata(doi):
    doi = clean_doi(doi)
    url = f'https://api.crossref.org/works/{doi}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('message', {})
    except requests.RequestException as e:
        print(f"Error fetching Crossref metadata: {e}")
        return {}

@cache.memoize()
def fetch_altmetric_data(doi):
    doi = clean_doi(doi)
    altmetric_url = f'https://api.altmetric.com/v1/doi/{doi}'
    try:
        response = requests.get(altmetric_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching Altmetric data: {e}")
        return {}

def build_publications_dataframe(search_query, include_crossref, include_altmetric):
    works = fetch_openalex_publications(search_query)
    publications_data = [collect_publication_info(work, include_crossref, include_altmetric) for work in works]
    return pd.DataFrame(publications_data)

def collect_publication_info(work, include_crossref, include_altmetric):
    doi = work.get('doi', 'Not Available')
    crossref_metadata = fetch_crossref_metadata(doi) if include_crossref and doi != 'Not Available' else {}
    altmetric_data = fetch_altmetric_data(doi) if include_altmetric and doi != 'Not Available' else {}

    institutions_country = []
    institution_type = []
    first_authors_institutions_countries = []
    last_authors_institutions_countries = []
    corresponding_authors_institutions_countries = []

    for authorship in work.get('authorships', []):
        for institution in authorship.get('institutions', []):
            institution_name = institution.get('display_name')
            country_code = institution.get('country_code')
            type_of_institution = institution.get('type')
            institutions_country.append(f"{institution_name} ({country_code})")
            institution_type.append(f"{institution_name} ({type_of_institution})")
            if authorship.get('author_position') == 'first':
                first_authors_institutions_countries.append(f"{institution_name} ({country_code})")
            elif authorship.get('author_position') == 'last':
                last_authors_institutions_countries.append(f"{institution_name} ({country_code})")
            elif authorship.get('is_corresponding') == 'True':
                corresponding_authors_institutions_countries.append(f"{institution_name} ({country_code})")

    institutions_country = list(set(institutions_country))
    institution_type = list(set(institution_type))
    first_authors_institutions_countries = list(set(first_authors_institutions_countries))
    last_authors_institutions_countries = list(set(last_authors_institutions_countries))
    corresponding_authors_institutions_countries = list(set(corresponding_authors_institutions_countries))

    author_countries = set()
    for authorship in work.get('authorships', []):
        for country in authorship.get('countries', []):
            author_countries.add(country)
    author_countries = list(author_countries)

    first_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('author_position') == 'first']
    last_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('author_position') == 'last']
    corresponding_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('is_corresponding')]

    first_authors = [authorship.get('author', {}) for authorship in first_authorships]
    last_authors = [authorship.get('author', {}) for authorship in last_authorships]
    corresponding_authors = [authorship.get('author', {}) for authorship in corresponding_authorships]

    first_author_names = [author.get('display_name') for author in first_authors]
    last_author_names = [author.get('display_name') for author in last_authors]
    corresponding_author_names = [author.get('display_name') for author in corresponding_authors]

    first_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in first_authorships]
    last_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in last_authorships]
    corresponding_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in corresponding_authorships]

    journal = "Not Available"
    primary_location = work.get('primary_location', {})
    source = primary_location.get('source', {}) if primary_location else {}

    apc_list = work.get('apc_list', {}) or {}
    apc_paid = work.get('apc_paid', {}) or {}

    # Initialize the citation counts dictionary
    citation_counts = {}
    for count_data in work.get('counts_by_year', []):
        year = count_data.get('year')
        if year:
            citation_counts[f'Citations {year}'] = count_data.get('cited_by_count', 0)

    publication_info = {
        'OpenAlex DOI': work.get('doi'),
        'OpenAlex ID': work.get('id'),
        'OpenAlex Title': work.get('display_name'),
        'OpenAlex Publication Year': work.get('publication_year'),
        'OpenAlex Publication Date': work.get('publication_date'),
        'OpenAlex Authors': ', '.join([authorship['author'].get('display_name', 'Unknown Author') for authorship in work.get('authorships', [])]),
        'OpenAlex First Authors': ', '.join(first_author_names),
        'OpenAlex Last Authors': ', '.join(last_author_names),
        'OpenAlex Corresponding Authors': ', '.join(corresponding_author_names),
        'OpenAlex Institutions': ', '.join(institutions_country),
        'OpenAlex Institutions Type': ', '.join(institution_type),
        'OpenAlex First Authors Institutions Countries': ', '.join(first_authors_institutions_countries),
        'OpenAlex Last Authors Institutions Countries': ', '.join(last_authors_institutions_countries),
        'OpenAlex Institutions Distinct Count': work.get('institutions_distinct_count'),
        'OpenAlex Countries': ', '.join(author_countries),
        'OpenAlex First Authors Countries': ', '.join(first_authors_countries),
        'OpenAlex Last Authors Countries': ', '.join(last_authors_countries),
        'OpenAlex Corresponding Authors Countries': ', '.join(corresponding_authors_countries),
        'OpenAlex Countries Distinct Count': work.get('countries_distinct_count'),
        'OpenAlex Journal': source.get('display_name', "Not Available"),
        'is_in_doaj': source.get('is_in_doaj', False),
        'OpenAlex Crossref Publisher': crossref_metadata.get('publisher', ''),

        'OpenAlex Crossref Subject': ', '.join(crossref_metadata.get('subject', [])),
        'OpenAlex topics': ', '.join([topic.get('display_name') for topic in work.get('topics', [])]),
        'OpenAlex Keywords': ', '.join([keyword.get('display_name') for keyword in work.get('keywords', [])]),
        'OpenAlex Mesh': ', '.join([mesh.get('descriptor_name') for mesh in work.get('mesh', [])]),
        'OpenAlex Concepts': ', '.join([concept.get('display_name') for concept in work.get('concepts', [])]),
        'OpenAlex Sustainable Development Goals': ', '.join([sdg.get('display_name') for sdg in work.get('sustainable_development_goals', [])]),
        'Crossref Citation count': crossref_metadata.get('is-referenced-by-count', 0),
        'OpenAlex Cited by Count': work.get('cited_by_count'),
        'OpenAlex Counts by Year': str(work.get('counts_by_year')),
        'OpenAlex Publication Type': work.get('type'),
        'OpenAlex Indexed In': str(work.get('indexed_in')),
        'OpenAlex Language': work.get('language'),
        'OpenAlex Open Access status': work.get('open_access', {}).get('oa_status', None),
        'OpenAlex grants': ', '.join([grant.get('funder_display_name') for grant in work.get('grants', [])]),
        'Crossref Funders': ', '.join(funder.get('name', '') for funder in crossref_metadata.get('funder', [])),
        'Altmetric Score': altmetric_data.get('score'),
        'Altmetric Read Count': altmetric_data.get('readers_count'),
        'Altmetric Image': altmetric_data.get('images', {}).get('small'),
        'Altmetric URL': altmetric_data.get('details_url'),
        'apc_list_value': apc_list.get('value', None),
        'apc_list_currency': apc_list.get('currency', None),
        'apc_list_value_usd': apc_list.get('value_usd', None),
        'apc_list_provenance': apc_list.get('provenance', None),
        'apc_paid_value': apc_paid.get('value', None),
        'apc_paid_currency': apc_paid.get('currency', None),
        'apc_paid_value_usd': apc_paid.get('value_usd', None),
        'apc_paid_provenance': apc_paid.get('provenance', None),
        'number_of_authors': len(work.get('authorships', []))
    }

    # Add citation counts to publication_info
    publication_info.update(citation_counts)

    return publication_info

@app.callback(
    [
        Output('status-alert', 'children'),
        Output('status-alert', 'style'),
        Output('spinner-container', 'style'),
        Output('stored-search-query', 'data'),
        Output('table-container', 'children'),
        Output('download-button', 'disabled'),
        Output('download-button', 'style'),
        Output('stored-data', 'data'),
    ],
    [Input('submit-button', 'n_clicks')],
    [State('search-input', 'value'), State('data-options', 'value')],
    prevent_initial_call=True
)
def validate_fetch_and_update_ui(n_clicks, search_query, data_options):
    if not search_query:
        return (
            "Missing search query. Please enter a search term and try again.",
            {'display': 'block', 'color': 'warning'},
            {'display': 'none'},
            no_update,
            no_update,
            True,
            {'display': 'none'},
            no_update,
        )

    spinner_style = {'display': 'block'}
    message = "Valid search. Fetching publications, please wait..."
    alert_style = {'display': 'block', 'color': 'primary'}

    include_crossref = 'crossref' in data_options
    include_altmetric = 'altmetric' in data_options

    try:
        df = build_publications_dataframe(search_query, include_crossref, include_altmetric)
        if df.empty:
            return (
                "No publications found for the provided search query.",
                {'display': 'block', 'color': 'secondary'},
                {'display': 'none'},
                search_query,
                no_update,
                True,
                {'display': 'none'},
                no_update,
            )

        tooltip_data = [
            {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()}
            for row in df.to_dict('records')
        ]
        table = dbc.Spinner(dash_table.DataTable(
            id='table-filtering',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            filter_action='native',
            sort_action='native',
            sort_mode='multi',
            page_size=10,
            style_cell={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 200},
            tooltip_data=tooltip_data,
            tooltip_delay=0,
            tooltip_duration=None
        ), size="lg", color="primary", type="border", fullscreen=True)

        return (
            "Publications ready. You can now view or download the list.",
            {'display': 'block', 'color': 'success'},
            {'display': 'none'},
            search_query,
            table,
            False,
            {'display': 'block'},
            df.to_dict('records'),
        )
    except Exception as e:
        return (
            f"An error occurred: {str(e)}",
            {'display': 'block', 'color': 'danger'},
            {'display': 'none'},
            no_update,
            no_update,
            True,
            {'display': 'none'},
            no_update,
        )

@app.callback(
    Output('download-link', 'data'),
    [Input('download-button', 'n_clicks')],
    [State('stored-data', 'data'), State('search-input', 'value')],
    prevent_initial_call=True
)
def download_publications_list(n_clicks, stored_data, search_query):
    if n_clicks is None or stored_data is None:
        raise PreventUpdate
    safe_search_query = re.sub(r'[^\w\-_]', '_', search_query)
    filename = f"{safe_search_query}_publications_list.csv"
    df = pd.DataFrame(stored_data)
    return dcc.send_data_frame(df.to_csv, filename, index=False)

@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")]
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run_server(debug=True)
