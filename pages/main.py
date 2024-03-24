# Import required libraries
from components.navbar import Navbar  # Adjust according to your file structure
from components.footer import Footer
import os 
import dash
import pandas as pd
import requests
from dash import dcc, html, dash_table, callback_context, Input, Output, State, no_update, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import re
from flask_caching import Cache
import time
from app import app, cache  # Importing app and cache here



def layout():
    return dbc.Container([
        Navbar(),  # Use the Navbar component

        dbc.Row(dbc.Col(html.H1('Publications Fetcher'),  className="d-flex justify-content-center")), #width={"size": 3, "offset": 3},
        dbc.Row(dbc.Col(html.P("Enter your ORCID ID to fetch and display your publications."), className="d-flex justify-content-center")),
        dbc.Row(
            dbc.Col([
                dcc.Input(id='orcid-input', type='text', placeholder='e.g., 0000-0002-1825-0097', debounce=True, className="me-2"),
                html.Button('Submit', id='submit-button', n_clicks=0, className="submit-button")
            ], width=12, className="d-flex justify-content-center"),
            justify="center"  # This centers the row
        ),
        dbc.Row(dbc.Col(dbc.Alert(id='input-alert', color="warning", className="mt-3", style={"display": "none"}))),
        dbc.Row(dbc.Col(dbc.Alert(id='status-alert', children="The ORCID number is valid. Fetching publications, please wait...", color="info", className="mt-3", style={"display": "none"}))),
        dbc.Row(dbc.Col(dbc.Alert(id='status-alert-output', children="Publications ready. You can now view or download the list.", color="info", className="mt-3", style={"display": "none"}))),

        dbc.Row(dbc.Col(html.Div(id='spinner-container', children=[dbc.Spinner(size="lg", color="primary", type="border")], style={'display': 'none'}))),
        dbc.Row(dbc.Col(html.Div(id='spinner-container-closed', children=[dbc.Spinner(size="lg", color="primary", type="border")], style={'display': 'none'}))),

        dbc.Row(dbc.Col(html.Button('Download Publications List', id='download-button', disabled=True, className="mt-3", style={'display': 'none'}))),
        dcc.Download(id='download-link'),

        dcc.Store(id='stored-data'),
        dcc.Store(id='stored-orcid-id'),  # Additional stored data

        html.Div(id='table-container', className="mt-3"),  # Placeholder for table

        Footer(),  # Use the Footer component
    ], fluid=True, className="py-3")



#############functions to fetch############################

@cache.memoize()
def fetch_orcid_publications(orcid_id):
    url = f'https://pub.orcid.org/v3.0/{orcid_id}/works'
    headers = {'Accept': 'application/json'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        works = response.json().get('group', [])
        dois = [
            external_id['external-id-value']
            for work in works
            for external_id in work['work-summary'][0]['external-ids']['external-id']
            if external_id['external-id-type'] == 'doi'
        ]
        return dois
    except requests.RequestException as e:
        print(f"Error fetching ORCID publications: {e}")
        return []

@cache.memoize()
def fetch_crossref_metadata(doi):
    url = f'https://api.crossref.org/works/{doi}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('message', {})
    except requests.RequestException as e:
        print(f"Error fetching Crossref metadata: {e}")
        return {}

@cache.memoize()
def fetch_openalex_metadata(doi):
    openalex_url = f'https://api.openalex.org/works?filter=doi:{doi}'
    # if response.status_code == 200 and response.json()['meta']['count'] > 0:
    try:
        response = requests.get(openalex_url)
        response.raise_for_status() 
        response_data = response.json()
        works = response_data['results'][0] if response_data.get('results') and len(response_data['results']) > 0 else {}
        # works = response.json()['results'][0]
        return works#[0] if works else {}
    except requests.RequestException as e:
        print(f"Error fetching OpenAlex publications: {e}")
        return {}

@cache.memoize()
def fetch_altmetric_data(doi):
    altmetric_url = f'https://api.altmetric.com/v1/doi/{doi}'
    try:
        response = requests.get(altmetric_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching Altmetric data: {e}")
        return {}

def build_publications_dataframe(orcid_id):
    dois = fetch_orcid_publications(orcid_id)
    publications_data = [collect_publication_info(doi) for doi in dois]
    return pd.DataFrame(publications_data)

def collect_publication_info(doi):
    crossref_metadata = fetch_crossref_metadata(doi)
    altmetric_data = fetch_altmetric_data(doi)
    work  = fetch_openalex_metadata(doi) #openalex_metadata

    # Define the list of unique institutions and their country codes
    institutions_country = []
    institution_type = []
    first_authors_institutions_countries = []
    last_authors_institutions_countries = []
    corresponding_authors_institutions_countries = []
    for authorship in work.get('authorships', []):
        for institution in authorship.get('institutions', []):
            institution_name = institution.get('display_name')
            country_code = institution.get('country_code')
            type_of_institution = institution.get('type')  # Renamed variable to avoid conflict
            institutions_country.append(f"{institution_name} ({country_code})")
            institution_type.append(f"{institution_name} ({type_of_institution})")  # Use the renamed variable here
            if authorship.get('author_position') == 'first':
                first_authors_institutions_countries.append(f"{institution_name} ({country_code})")
            elif authorship.get('author_position') == 'last':
                last_authors_institutions_countries.append(f"{institution_name} ({country_code})")
            elif authorship.get('is_corresponding') == 'True':
                corresponding_authors_institutions_countries.append(f"{institution_name} ({country_code})")

    # Remove duplicates by converting the list to a set and then back to a list
    institutions_country = list(set(institutions_country))
    institution_type = list(set(institution_type))  # Use the renamed variable here
    first_authors_institutions_countries = list(set(first_authors_institutions_countries))
    last_authors_institutions_countries = list(set(last_authors_institutions_countries))
    corresponding_authors_institutions_countries = list(set(corresponding_authors_institutions_countries))


    # Define the set of unique author countries
    author_countries = set()
    for authorship in work.get('authorships', []):
        for country in authorship.get('countries', []):
            author_countries.add(country)
    # Now, 'author_countries' is a set of unique author countries.
    # You can convert it to a list if you prefer:
    author_countries = list(author_countries)

    # Get all the first, last, and corresponding authorships
    first_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('author_position') == 'first']
    last_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('author_position') == 'last']
    corresponding_authorships = [authorship for authorship in work.get('authorships', []) if authorship.get('is_corresponding')]

    # Get the author dictionary from each authorship
    first_authors = [authorship.get('author', {}) for authorship in first_authorships]
    last_authors = [authorship.get('author', {}) for authorship in last_authorships]
    corresponding_authors = [authorship.get('author', {}) for authorship in corresponding_authorships]

    # Get the display name of each author
    first_author_names = [author.get('display_name') for author in first_authors]
    last_author_names = [author.get('display_name') for author in last_authors]
    corresponding_author_names = [author.get('display_name') for author in corresponding_authors]

    # Get the author dictionary and country from each authorship
    first_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in first_authorships]
    last_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in last_authorships]
    corresponding_authors_countries = [authorship.get('countries', [])[0] if authorship.get('countries') else "Unknown" for authorship in corresponding_authorships]


    journal = "Not Available"  # Default value
    primary_location = work.get('primary_location', {})
    if primary_location:
        source = primary_location.get('source', {})
        if source:
            journal = source.get('display_name', "Not Available")

    # authors_list = crossref_metadata.get('author', [])
    # authors_name = [f"{author.get('given')} {author.get('family')}" for author in authors_list if 'given' in author and 'family' in author]
    return {
        'ORCID DOI': doi,
        'OpenAlex DOI': work.get('doi'),
        'OpenAlex ID': work.get('id'),
        'OpenAlex Title': work.get('display_name'),
        # 'Title': crossref_metadata.get('title', [''])[0],
        # 'Abstract': work.get('abstract'),
        'OpenAlex Publication Year': work.get('publication_year'),
        # 'Crossref Published Year': crossref_metadata.get('published', {}).get('date-parts', [[None]])[0][0],        
        'OpenAlex Publication Date': work.get('publication_date'),

        'OpenAlex Authors': ', '.join([authorship['author'].get('display_name', 'Unknown Author') for authorship in work.get('authorships', [])]),
        # 'Authors Name': ', '.join(authors_name),
        'OpenAlex First Authors': ', '.join(first_author_names),
        'OpenAlex Last Authors': ', '.join(last_author_names),
        'OpenAlex Corresponding Authors': ', '.join(corresponding_author_names),


        'OpenAlex Institutions': ', '.join(institutions_country),
        'OpenAlex Institutions Type': ', '.join(institution_type),
        'OpenAlex First Authors Institutions Countries': ', '.join(first_authors_institutions_countries),
        'OpenAlex Last Authors Institutions Countries': ', '.join(last_authors_institutions_countries),
        # 'Corresponding Authors Institutions Countries': ', '.join(corresponding_authors_institutions_countries),
        'OpenAlex Institutions Distinct Count': work.get('institutions_distinct_count'),

        'OpenAlex Countries': ', '.join(author_countries),
        'OpenAlex First Authors Countries': ', '.join(first_authors_countries),
        'OpenAlex Last Authors Countries': ', '.join(last_authors_countries),
        'OpenAlex Corresponding Authors Countries': ', '.join(corresponding_authors_countries),
        'OpenAlex Countries Distinct Count': work.get('countries_distinct_count'),

        'OpenAlex Journal': journal,
        # 'Crossref Journal': ', '.join(crossref_metadata.get('container-title', [])),
        'OpenAlex Crossref Publisher': crossref_metadata.get('publisher', ''),


        'OpenAlex Crossref Subject': ', '.join(crossref_metadata.get('subject', [])),
        'OpenAlex Keywords': ', '.join([keyword.get('keyword') for keyword in work.get('keywords', [])]),
        'OpenAlex Mesh': ', '.join([mesh.get('descriptor_name') for mesh in work.get('mesh', [])]),
        'OpenAlex Concepts': ', '.join([concept.get('display_name') for concept in work.get('concepts', [])]),
        'OpenAlex Sustainable Development Goals': ', '.join([sdg.get('display_name') for sdg in work.get('sustainable_development_goals', [])]),

        'Crossref Citation count': crossref_metadata.get('is-referenced-by-count', 0),
        'OpenAlex Cited by Count': work.get('cited_by_count'),
        'OpenAlex Counts by Year': str(work.get('counts_by_year')),

    #     # Additional fields as needed,
        'OpenAlex Publication Type': work.get('type'),
        # 'Publication Type': crossref_metadata.get('type', ''),
        'OpenAlex Indexed In': str(work.get('indexed_in')),

        'OpenAlex Language': work.get('language'),
        'OpenAlex Open Access status': work.get('open_access', {}).get('oa_status', None),
        'OpenAlex grants': ', '.join([grant.get('funder_display_name') for grant in work.get('grants', [])]),
        'Crossref Funders': ', '.join(funder.get('name', '') for funder in crossref_metadata.get('funder', [])),

        'Altmetric Score': altmetric_data.get('score'),
        'Altmetric Read Count': altmetric_data.get('readers_count'),
        'Altmetric Image': altmetric_data.get('images', {}).get('small'),
        'Altmetric URL': altmetric_data.get('details_url'),
    }




####################################################

@app.callback(
    [
        Output('status-alert', 'children'),  # To update the message
        Output('status-alert', 'style'),  # To show/hide the message alert
        Output('spinner-container', 'style'),  # To show/hide the spinner
        Output('stored-orcid-id', 'data'),  # To store the ORCID ID if valid
        Output('table-container', 'children'),  # To display the data table
        Output('download-button', 'disabled'),  # To enable/disable the download button
        Output('download-button', 'style'),  # To show/hide the download button
        Output('stored-data', 'data'),  # To store the fetched data for download
    ],
    [Input('submit-button', 'n_clicks')],
    [State('orcid-input', 'value')],
    prevent_initial_call=True
)
def validate_fetch_and_update_ui(n_clicks, orcid_id):
    if not orcid_id or not re.match(r'^\d{4}-\d{4}-\d{4}-[\dX]{4}$', orcid_id):
        return (
            "Missing or Invalid ORCID ID format. Please correct it and try again.",
            {'display': 'block', 'color': 'warning'},
            {'display': 'none'},  # Hide spinner
            no_update,
            no_update,
            True,
            {'display': 'none'},
            no_update,
        )

    # Valid ORCID ID, start fetching data
    # Show spinner and update message
    spinner_style = {'display': 'block'}  # Make spinner visible
    message = "The ORCID number is valid. Fetching publications, please wait..."
    alert_style = {'display': 'block', 'color': 'primary'}

    try:
        df = build_publications_dataframe(orcid_id)
        if df.empty:
            # Handle empty DataFrame (no publications found)
            return (
                "No publications found for the provided ORCID ID.",
                {'display': 'block', 'color': 'secondary'},
                {'display': 'none'},  # Hide spinner
                orcid_id,
                no_update,
                True,
                {'display': 'none'},
                no_update,
            )

        # Publications fetched, prepare the data table
        # table = prepare_data_table(df)  # Assume this is a function that prepares the Dash DataTable
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
            {'display': 'none'},  # Hide spinner after fetching
            orcid_id,
            table,
            False,  # Enable download button
            {'display': 'block'},  # Show download button
            df.to_dict('records'),
        )
    except Exception as e:
        # Handle any exceptions during the fetching process
        return (
            f"An error occurred: {str(e)}",
            {'display': 'block', 'color': 'danger'},
            {'display': 'none'},  # Hide spinner
            no_update,
            no_update,
            True,
            {'display': 'none'},
            no_update,
        )




#####################################################################################################
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback to download the data
@app.callback(
    Output('download-link', 'data'),
    [Input('download-button', 'n_clicks')],
    [State('stored-data', 'data'),  # Keeps existing state for the data
     State('orcid-input', 'value')],  # Adds the ORCID ID as a state
    prevent_initial_call=True
)
def download_publications_list(n_clicks, stored_data, orcid_id):
    if n_clicks is None or stored_data is None:
        raise PreventUpdate
    # Sanitize the ORCID ID to ensure it's safe for use in a filename
    # This removes any characters that might be invalid for filenames
    safe_orcid_id = re.sub(r'[^\w\-_]', '_', orcid_id)
    filename = f"{safe_orcid_id}_publications_list.csv"
    # Convert the stored data back to a DataFrame
    df = pd.DataFrame(stored_data)
    # Return the CSV download, dynamically naming the file with the ORCID ID
    return dcc.send_data_frame(df.to_csv, filename, index=False)



if __name__ == '__main__':
    app.run_server(debug=True)