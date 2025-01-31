import dash
import pandas as pd
import numpy as np
import requests
from dash import dcc, html, dash_table, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import base64
import io
import logging
from flask_caching import Cache
from datetime import datetime
from app import app, cache  # Import app and cache here
from components.navbar import Navbar
from components.footer import Footer
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Utility Functions
def create_onboarding_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader("Welcome to the Publication Data Collector"),
            dbc.ModalBody(
                "This app allows you to fetch, enrich, and download publication data. Follow the steps provided to upload DOIs files or use the OpenAlex API."
            ),
            dbc.ModalFooter(dbc.Button("Got it!", id="close-onboarding", className="ms-auto")),
        ],
        id="onboarding-modal",
        is_open=True,
    )

def clean_doi(doi):
    if doi and doi.startswith("https://doi.org/"):
        return doi.replace("https://doi.org/", "")
    return doi

def parse_uploaded_file(contents, filename):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string).decode('utf-8')
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded))
        elif filename.endswith('.txt'):
            df = pd.DataFrame(decoded.splitlines(), columns=['DOI'])
        else:
            raise ValueError("Unsupported file type. Please upload a .csv or .txt file.")

        if 'DOI' in df.columns:
            dois = df['DOI'].dropna().tolist()
        else:
            dois = df.iloc[:, 0].dropna().tolist()

        return [clean_doi(doi) for doi in dois]
    except Exception as e:
        logging.error(f"Error parsing file: {e}")
        raise ValueError("Failed to parse the file. Ensure it is correctly formatted and contains valid DOIs.")

def fetch_openalex_publications(search_query, max_results=100000):
    works = []
    per_page = 25
    cursor = '*'
    while True:
        url = f"{search_query}&per-page={per_page}&cursor={cursor}"
        try:
            response = requests.get(url, timeout=10)
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
            time.sleep(1)  # Respect API rate limits
        except requests.RequestException as e:
            logging.error(f"Error fetching OpenAlex publications: {e}")
            break
    return works

def fetch_works_by_doi(dois):
    base_url = "https://api.openalex.org/works/http://dx.doi.org/"
    works = []
    for doi in dois:
        url = f"{base_url}{clean_doi(doi)}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            work = response.json()
            if 'id' in work:
                works.append(work)
            else:
                logging.warning(f"DOI {doi} returned no results.")
        except requests.Timeout:
            logging.warning(f"Timeout error for DOI {doi}. Skipping.")
        except requests.RequestException as e:
            logging.error(f"Error fetching work for DOI {doi}: {e}")
    return works

def fetch_crossref_metadata(doi):
    doi = clean_doi(doi)
    url = f'https://api.crossref.org/works/{doi}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('message', {})
    except requests.RequestException as e:
        logging.error(f"Error fetching Crossref metadata for DOI {doi}: {e}")
        return {}

def fetch_altmetric_data(doi):
    doi = clean_doi(doi)
    url = f'https://api.altmetric.com/v1/doi/{doi}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching Altmetric data for DOI {doi}: {e}")
        return {}


def reconstruct_abstract(abstract_inverted_index):
    """
    Reconstructs the abstract from the abstract_inverted_index.
    """
    if not abstract_inverted_index:
        return np.nan

    # Create a dictionary to hold position-word mappings
    abstract_dict = {}

    # Iterate over keys (which are words) and positions
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            abstract_dict[pos] = word

    # Sort by the position and join the words in order
    sorted_positions = sorted(abstract_dict.keys())
    abstract_words = [abstract_dict[pos] for pos in sorted_positions]

    return " ".join(abstract_words)

    
def rename_columns(df):
    """
    Renames the columns of the DataFrame to more descriptive names for clarity and user-friendliness.
    """
    column_mapping = {
        'OpenAlex DOI': 'DOI (OpenAlex)',
        'OpenAlex ID': 'OpenAlex ID',
        'OpenAlex Title': 'Title (OpenAlex)',
        'OpenAlex Abstract': 'Abstract (OpenAlex)',
        'OpenAlex Publication Year': 'Publication Year (OpenAlex)',
        'OpenAlex Publication Date': 'Publication Date (OpenAlex)',
        'OpenAlex Authors': 'Authors (OpenAlex)',
        'OpenAlex First Authors': 'First Authors (OpenAlex)',
        'OpenAlex Last Authors': 'Last Authors (OpenAlex)',
        'OpenAlex Corresponding Authors': 'Corresponding Authors (OpenAlex)',
        'OpenAlex Institutions': 'Institutions (OpenAlex)',
        'OpenAlex Institutions Type': 'Institution Types (OpenAlex)',
        'OpenAlex First Authors Institutions Countries': 'First Authors’ Institution Countries (OpenAlex)',
        'OpenAlex Last Authors Institutions Countries': 'Last Authors’ Institution Countries (OpenAlex)',
        'OpenAlex Institutions Distinct Count': 'Distinct Institutions Count (OpenAlex)',
        'OpenAlex Countries': 'Author Countries Abbr (OpenAlex)',
        'OpenAlex First Authors Countries': 'First Authors’ Countries Abbr (OpenAlex)',
        'OpenAlex Last Authors Countries': 'Last Authors’ Countries Abbr (OpenAlex)',
        'OpenAlex Corresponding Authors Countries': 'Corresponding Authors’ Countries Abbr (OpenAlex)',
        'OpenAlex Countries Distinct Count': 'Distinct Author Countries Count (OpenAlex)',
        'OpenAlex Journal': 'Journal Name (OpenAlex)',
        'is_in_doaj': 'Indexed in DOAJ (OpenAlex)',
        'OpenAlex Crossref Publisher': 'Publisher (Crossref)',
        'OpenAlex Crossref Subject': 'Subjects (Crossref)',
        'OpenAlex topics': 'Topics (OpenAlex)',
        'OpenAlex Keywords': 'Keywords (OpenAlex)',
        'OpenAlex Mesh': 'MeSH Terms (OpenAlex)',
        'OpenAlex Concepts': 'Concepts (OpenAlex)',
        'OpenAlex Sustainable Development Goals': 'Sustainable Development Goals (OpenAlex)',
        'Crossref Citation count': 'Citation Count (Crossref)',
        'OpenAlex Cited by Count': 'Citation Count (OpenAlex)',
        'OpenAlex Counts by Year': 'Citation Counts by Year (OpenAlex)',
        'OpenAlex Publication Type': 'Publication Type (OpenAlex)',
        'OpenAlex Indexed In': 'Indexed In (OpenAlex)',
        'OpenAlex Language': 'Language (OpenAlex)',
        'OpenAlex Open Access': 'Open Access (OpenAlex)',
        'OpenAlex Open Access status': 'Open Access Status (OpenAlex)',
        'OpenAlex grants': 'Grants (OpenAlex)',
        'Crossref Funders': 'Funders (Crossref)',
        'apc_list_value': 'APC Value (List) (OpenAlex)',
        'apc_list_currency': 'APC Currency (List) (OpenAlex)',
        'apc_list_value_usd': 'APC Value (List - USD) (OpenAlex)',
        'apc_list_provenance': 'APC Provenance (List) (OpenAlex)',
        'apc_paid_value': 'APC Value (Paid) (OpenAlex)',
        'apc_paid_currency': 'APC Currency (Paid) (OpenAlex)',
        'apc_paid_value_usd': 'APC Value (Paid - USD) (OpenAlex)',
        'apc_paid_provenance': 'APC Provenance (Paid) (OpenAlex)',
        'Altmetric ID': 'Altmetric ID',
        'Publisher Subjects': 'Publisher Subjects (Altmetric)',
        'Scopus Subjects': 'Subjects-Scopus (Altmetric)',
        'Cohort - Public': 'Demographic: Public (Altmetric)',
        'Cohort - Scientific': 'Demographic: Scientists (Altmetric)',
        'Cohort - Community': 'Demographic: Science communicators (journalists, bloggers, editors) (Altmetric)',
        'Cohort - Doctor': 'Demographic: Practitioners (doctors, other healthcare professionals) (Altmetric)',
        'Cited By Posts Count': 'Total Mentions Across Sources (Altmetric)',
        'Cited By Tweeters Count': 'Mentions on Twitter (Altmetric)',
        'Cited By MSM Count': 'Mentions in News Outlets (Altmetric)',
        'Cited By Feeds Count': 'Mentions in RSS Feeds (Altmetric)',
        'Cited By FB Walls Count': 'Mentions on Facebook (Altmetric)',
        'Cited By RDTs Count': 'Mentions on Reddit (Altmetric)',
        'Cited By Wikipedia Count': 'Mentions on Wikipedia (Altmetric)',
        'Cited By RH Count': 'Mentions in Research Highlights (Altmetric)',
        'Cited By Videos Count': 'Mentions in Videos (Altmetric)',
        'Cited By QnA Count': 'Mentions in Q&A Threads (Altmetric)',
        'Cited By Policies Count': 'Mentions in Policies (Altmetric)',
        'Cited By Book Reviews Count': 'Mentions in Book Reviews (Altmetric)',
        'Cited By Patents Count': 'Mentions in Patents (Altmetric)',
        'Cited By Guidelines Count': 'Mentions in Guidelines (Altmetric)',
        'Cited By Bluesky Count': 'Mentions on Bluesky (Altmetric)',
        'Cited By Accounts Count': 'Total Accounts Citing (Altmetric)',
        'Readers CiteULike': 'Readers on CiteULike (Altmetric)',
        'Readers Mendeley': 'Readers on Mendeley (Altmetric)',
        'Readers Connotea': 'Readers on Connotea (Altmetric)',
        'Readers Count': 'Total Readers (Altmetric)',
        'Altmetric Score': 'Altmetric Attention Score',
        'Altmetric Score History': 'Altmetric Score History',
        'History (1 Year)': 'Altmetric Score (Last Year)',
        'History (6 Months)': 'Altmetric Score (Last 6 Months)',
        'History (3 Months)': 'Altmetric Score (Last 3 Months)',
        'History (1 Month)': 'Altmetric Score (Last Month)',
        'History (1 Week)': 'Altmetric Score (Last Week)',
        'History (6 Days)': 'Altmetric Score (6 Days Ago)',
        'History (5 Days)': 'Altmetric Score (5 Days Ago)',
        'History (4 Days)': 'Altmetric Score (4 Days Ago)',
        'History (3 Days)': 'Altmetric Score (3 Days Ago)',
        'History (2 Days)': 'Altmetric Score (2 Days Ago)',
        'History (1 Day)': 'Altmetric Score (Yesterday)',
        'History (At)': 'Altmetric Score (At Retrieval)',
        'All Context Count': 'Total Outputs (Context - All) (Altmetric)',
        'All Context Mean': 'Mean Outputs (Context - All) (Altmetric)',
        'All Context Rank': 'Rank (Context - All) (Altmetric)',
        'All Context Pct': 'Percentile (Context - All) (Altmetric)',
        'Journal Context Count': 'Total Outputs (Journal Context) (Altmetric)',
        'Journal Context Mean': 'Mean Outputs (Journal Context) (Altmetric)',
        'Journal Context Rank': 'Rank (Journal Context) (Altmetric)',
        'Journal Context Pct': 'Percentile (Journal Context) (Altmetric)',
        'Similar Age 3m Context Count': 'Total Outputs (Similar Age - 3 Months) (Altmetric)',
        'Similar Age 3m Context Mean': 'Mean Outputs (Similar Age - 3 Months) (Altmetric)',
        'Similar Age 3m Context Rank': 'Rank (Similar Age - 3 Months) (Altmetric)',
        'Similar Age 3m Context Pct': 'Percentile (Similar Age - 3 Months) (Altmetric)',
        'Similar Age Journal 3m Context Count': 'Total Outputs (Similar Age Journal - 3 Months) (Altmetric)',
        'Similar Age Journal 3m Context Mean': 'Mean Outputs (Similar Age Journal - 3 Months) (Altmetric)',
        'Similar Age Journal 3m Context Rank': 'Rank (Similar Age Journal - 3 Months) (Altmetric)',
        'Similar Age Journal 3m Context Pct': 'Percentile (Similar Age Journal - 3 Months) (Altmetric)',
        'Altmetric Badge Small': 'Altmetric Badge (Small)',
        'Altmetric Badge Medium': 'Altmetric Badge (Medium)',
        'Altmetric Badge Large': 'Altmetric Badge (Large)',
        'Details URL': 'Altmetric Details URL',
        'number_of_authors': 'Number of Authors (OpenAlex)',

        # Derived Columns
        'Citations 2024': 'Citations (2024) (OpenAlex)',
        'Citations 2023': 'Citations (2023) (OpenAlex)',
        'Citations 2022': 'Citations (2022) (OpenAlex)',
        'Citations 2021': 'Citations (2021) (OpenAlex)',
        'Citations 2020': 'Citations (2020) (OpenAlex)',
        'Citations 2019': 'Citations (2019) (OpenAlex)',
        'Citations 2018': 'Citations (2018) (OpenAlex)',
        'Citations 2017': 'Citations (2017) (OpenAlex)',
        'Citations 2016': 'Citations (2016) (OpenAlex)',
        'Citations 2015': 'Citations (2015) (OpenAlex)',
        'Citations 2014': 'Citations (2014) (OpenAlex)',
        'Citations 2013': 'Citations (2013) (OpenAlex)',
        'OpenAlex Countries Full Name': 'Country Names (OpenAlex)',
        'OpenAlex Countries Region': 'Country Regions (OpenAlex)',
        'OpenAlex Countries Income': 'Country Income Levels (OpenAlex)',
        'OpenAlex First Authors Countries Full Name': 'First Author Country Names (OpenAlex)',
        'OpenAlex First Authors Countries Region': 'First Author Country Regions (OpenAlex)',
        'OpenAlex First Authors Countries Income': 'First Author Country Income Levels (OpenAlex)',
        'OpenAlex Last Authors Countries Full Name': 'Last Author Country Names (OpenAlex)',
        'OpenAlex Last Authors Countries Region': 'Last Author Country Regions (OpenAlex)',
        'OpenAlex Last Authors Countries Income': 'Last Author Country Income Levels (OpenAlex)',
        'OpenAlex Corresponding Authors Countries Full Name': 'Corresponding Author Country Names (OpenAlex)',
        'OpenAlex Corresponding Authors Countries Region': 'Corresponding Author Country Regions (OpenAlex)',
        'OpenAlex Corresponding Authors Countries Income': 'Corresponding Author Country Income Levels (OpenAlex)',   
    }

    return df.rename(columns=column_mapping)



################################ Collect Publication Info  ################################

def collect_publication_info(work, include_crossref, include_altmetric):
    doi = work.get('doi', np.nan)
    #print(f"Fetching metadata for DOI: {doi}")
    crossref_metadata = fetch_crossref_metadata(doi) if include_crossref and pd.notna(doi) else {}
    altmetric_data = fetch_altmetric_data(doi) if include_altmetric and pd.notna(doi) else {}

    #-----------------------------------

    # Extract Altmetric details
    altmetric_id = altmetric_data.get('altmetric_id')
    title = altmetric_data.get('title')
    issns = altmetric_data.get('issns', [])
    journal = altmetric_data.get('journal')

    # Safely handle the cohorts field
    cohorts = altmetric_data.get('cohorts', {})
    if not isinstance(cohorts, dict):  # If cohorts is not a dictionary
        # print(f"DOI causing cohorts issue: {doi}")
        # print(f"Cohorts data type: {type(cohorts)}")
        # print(f"Cohorts content: {cohorts}")
        # Set cohorts values to 0 when the structure is unexpected
        public_cohort = scientific_cohort = community_cohort = doctor_cohort = 0
    else:
        # Extract cohorts data if it is a dictionary
        public_cohort = cohorts.get('pub', 0)
        scientific_cohort = cohorts.get('sci', 0)
        community_cohort = cohorts.get('com', 0)
        doctor_cohort = cohorts.get('doc', 0)


    # Extract context details
    context = altmetric_data.get('context', {})
    all_context = context.get('all', {})
    journal_context = context.get('journal', {})
    similar_age_3m_context = context.get('similar_age_3m', {})
    similar_age_journal_3m_context = context.get('similar_age_journal_3m', {})

    authors = altmetric_data.get('authors', [])
    type_of_publication = altmetric_data.get('type')
    pubdate = altmetric_data.get('pubdate')
    epubdate = altmetric_data.get('epubdate')
    publisher_subjects = altmetric_data.get('publisher_subjects', [])
    scopus_subjects = altmetric_data.get('scopus_subjects', [])
    cited_by_posts_count = altmetric_data.get('cited_by_posts_count', 0)

    # Extract detailed cited-by categories
    cited_by_categories = {
        'Cited By Tweeters Count': altmetric_data.get('cited_by_tweeters_count', 0),
        'Cited By MSM Count': altmetric_data.get('cited_by_msm_count', 0),
        'Cited By Feeds Count': altmetric_data.get('cited_by_feeds_count', 0),
        'Cited By FB Walls Count': altmetric_data.get('cited_by_fbwalls_count', 0),
        'Cited By RDTs Count': altmetric_data.get('cited_by_rdts_count', 0),
        'Cited By Wikipedia Count': altmetric_data.get('cited_by_wikipedia_count', 0),
        'Cited By RH Count': altmetric_data.get('cited_by_rh_count', 0),
        'Cited By Videos Count': altmetric_data.get('cited_by_videos_count', 0),
        'Cited By QnA Count': altmetric_data.get('cited_by_qna_count', 0),
        'Cited By Policies Count': altmetric_data.get('cited_by_policies_count', 0),
        'Cited By Book Reviews Count': altmetric_data.get('cited_by_book_reviews_count', 0),
        'Cited By Patents Count': altmetric_data.get('cited_by_patents_count', 0),
        'Cited By Guidelines Count': altmetric_data.get('cited_by_guidelines_count', 0),
        'Cited By Bluesky Count': altmetric_data.get('cited_by_bluesky_count', 0),
        'Cited By Accounts Count': altmetric_data.get('cited_by_accounts_count', 0)
    }

    # Extract Altmetric score history
    history = altmetric_data.get('history', {})
    history_1y = history.get('1y', 0)
    history_6m = history.get('6m', 0)
    history_3m = history.get('3m', 0)
    history_1m = history.get('1m', 0)
    history_1w = history.get('1w', 0)
    history_6d = history.get('6d', 0)
    history_5d = history.get('5d', 0)
    history_4d = history.get('4d', 0)
    history_3d = history.get('3d', 0)
    history_2d = history.get('2d', 0)
    history_1d = history.get('1d', 0)
    history_at = history.get('at', 0)    
    
    
    readers = altmetric_data.get('readers', {})
    readers_count = altmetric_data.get('readers_count', 0)
    images = altmetric_data.get('images', {})
    details_url = altmetric_data.get('details_url')
    score = altmetric_data.get('score')
    history = altmetric_data.get('history', {})

    #-----------------------------------
    
    # Reconstruct the abstract if available
    abstract_inverted_index = work.get('abstract_inverted_index')
    abstract = reconstruct_abstract(abstract_inverted_index) if abstract_inverted_index else np.nan

    #-----------------------------------
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

    first_author_names = [author.get('display_name', '') for author in first_authors]
    last_author_names = [author.get('display_name', '') for author in last_authors]
    corresponding_author_names = [author.get('display_name', '') for author in corresponding_authors]

    first_authors_countries = [authorship.get('countries', [np.nan])[0] if authorship.get('countries') else np.nan for authorship in first_authorships]
    last_authors_countries = [authorship.get('countries', [np.nan])[0] if authorship.get('countries') else np.nan for authorship in last_authorships]
    corresponding_authors_countries = [authorship.get('countries', [np.nan])[0] if authorship.get('countries') else np.nan for authorship in corresponding_authorships]

    journal = np.nan
    primary_location = work.get('primary_location', {})
    #source = primary_location.get('source', {}) if isinstance(primary_location, dict) and 'source' in primary_location else {}
    source = primary_location.get('source', {}) if isinstance(primary_location, dict) and primary_location and 'source' in primary_location else {}  


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
        'OpenAlex Abstract': abstract,
        'OpenAlex Publication Year': work.get('publication_year'),
        'OpenAlex Publication Date': work.get('publication_date'),
        'OpenAlex Authors': ', '.join([authorship['author'].get('display_name', '') for authorship in work.get('authorships', []) if authorship['author'].get('display_name')]),
        'OpenAlex First Authors': ', '.join([name for name in first_author_names if name]),
        'OpenAlex Last Authors': ', '.join([name for name in last_author_names if name]),
        'OpenAlex Corresponding Authors': ', '.join([name for name in corresponding_author_names if name]),
        'OpenAlex Institutions': ', '.join([inst for inst in institutions_country if inst]),
        'OpenAlex Institutions Type': ', '.join([inst for inst in institution_type if inst]),
        'OpenAlex First Authors Institutions Countries': ', '.join([inst for inst in first_authors_institutions_countries if inst]),
        'OpenAlex Last Authors Institutions Countries': ', '.join([inst for inst in last_authors_institutions_countries if inst]),
        'OpenAlex Institutions Distinct Count': work.get('institutions_distinct_count'),
        'OpenAlex Countries': ', '.join([str(country) for country in author_countries if country]),
        'OpenAlex First Authors Countries': ', '.join([str(country) for country in first_authors_countries if country]),
        'OpenAlex Last Authors Countries': ', '.join([str(country) for country in last_authors_countries if country]),
        'OpenAlex Corresponding Authors Countries': ', '.join([str(country) for country in corresponding_authors_countries if country]),
        'OpenAlex Countries Distinct Count': work.get('countries_distinct_count'),
        'OpenAlex Journal': source['display_name'] if source else np.nan,
        'is_in_doaj': source['is_in_doaj'] if source else np.nan,
        'OpenAlex Crossref Publisher': crossref_metadata.get('publisher', ''),
        'OpenAlex Crossref Subject': ', '.join([subject for subject in crossref_metadata.get('subject', []) if subject]),
        'OpenAlex topics': ', '.join([topic.get('display_name') for topic in work.get('topics', []) if topic.get('display_name')]),
        'OpenAlex Keywords': ', '.join([keyword.get('display_name') for keyword in work.get('keywords', []) if keyword.get('display_name')]),
        'OpenAlex Mesh': ', '.join([mesh.get('descriptor_name') for mesh in work.get('mesh', []) if mesh.get('descriptor_name')]),
        'OpenAlex Concepts': ', '.join([concept.get('display_name') for concept in work.get('concepts', []) if concept.get('display_name')]),
        'OpenAlex Sustainable Development Goals': ', '.join([sdg.get('display_name') for sdg in work.get('sustainable_development_goals', []) if sdg.get('display_name')]),
        'Crossref Citation count': crossref_metadata.get('is-referenced-by-count', 0),
        'OpenAlex Cited by Count': work.get('cited_by_count'),
        'OpenAlex Counts by Year': str(work.get('counts_by_year')),
        'OpenAlex Publication Type': work.get('type'),
        'OpenAlex Indexed In': str(work.get('indexed_in')),
        'OpenAlex Language': work.get('language'),
        'OpenAlex Open Access': work.get('open_access', {}).get('is_oa', None),
        'OpenAlex Open Access status': work.get('open_access', {}).get('oa_status', None),
        'OpenAlex grants': ', '.join([grant.get('funder_display_name') for grant in work.get('grants', []) if grant.get('funder_display_name')]),
        'Crossref Funders': ', '.join([funder.get('name', '') for funder in crossref_metadata.get('funder', []) if funder.get('name', '')]),
        
        'apc_list_value': apc_list.get('value', None),
        'apc_list_currency': apc_list.get('currency', None),
        'apc_list_value_usd': apc_list.get('value_usd', None),
        'apc_list_provenance': apc_list.get('provenance', None),

        'Altmetric ID': altmetric_id,
        'Publisher Subjects': ', '.join([subject['name'] for subject in publisher_subjects if subject['name']]),
        'Scopus Subjects': ', '.join([subject for subject in scopus_subjects if subject]),

        'Cohort - Public': public_cohort,
        'Cohort - Scientific': scientific_cohort,
        'Cohort - Community': community_cohort,
        'Cohort - Doctor': doctor_cohort,

        'Cited By Posts Count': cited_by_posts_count,
        
        **cited_by_categories,  # Include all cited-by categories
        'Readers CiteULike': readers.get('citeulike', 0),
        'Readers Mendeley': readers.get('mendeley', 0),
        'Readers Connotea': readers.get('connotea', 0),
        'Readers Count': readers_count,
        'Altmetric Score': score,

        'Altmetric Score History': str(altmetric_data.get('history')),
        'History (1 Year)': history_1y,
        'History (6 Months)': history_6m,
        'History (3 Months)': history_3m,
        'History (1 Month)': history_1m,
        'History (1 Week)': history_1w,
        'History (6 Days)': history_6d,
        'History (5 Days)': history_5d,
        'History (4 Days)': history_4d,
        'History (3 Days)': history_3d,
        'History (2 Days)': history_2d,
        'History (1 Day)': history_1d,
        'History (At)': history_at,

        'All Context Count': all_context.get('count', 0),
        'All Context Mean': all_context.get('mean', 0),
        'All Context Rank': all_context.get('rank', 0),
        'All Context Pct': all_context.get('pct', 0),
        'Journal Context Count': journal_context.get('count', 0),
        'Journal Context Mean': journal_context.get('mean', 0),
        'Journal Context Rank': journal_context.get('rank', 0),
        'Journal Context Pct': journal_context.get('pct', 0),
        'Similar Age 3m Context Count': similar_age_3m_context.get('count', 0),
        'Similar Age 3m Context Mean': similar_age_3m_context.get('mean', 0),
        'Similar Age 3m Context Rank': similar_age_3m_context.get('rank', 0),
        'Similar Age 3m Context Pct': similar_age_3m_context.get('pct', 0),
        'Similar Age Journal 3m Context Count': similar_age_journal_3m_context.get('count', 0),
        'Similar Age Journal 3m Context Mean': similar_age_journal_3m_context.get('mean', 0),
        'Similar Age Journal 3m Context Rank': similar_age_journal_3m_context.get('rank', 0),
        'Similar Age Journal 3m Context Pct': similar_age_journal_3m_context.get('pct', 0),
        'Altmetric Badge Small': images.get('small'),
        'Details URL': details_url,

        'number_of_authors': len(work.get('authorships', [])),
        'OpenAlex Countries Distinct Count': work.get('countries_distinct_count'),
    }

    # Add citation counts to publication_info
    publication_info.update(citation_counts)

    return publication_info



############# Functions to process data and build publications dataframe ############################

def build_publications_dataframe(works, include_crossref, include_altmetric):
    publications_data = [collect_publication_info(work, include_crossref, include_altmetric) for work in works]
    df = pd.DataFrame(publications_data)

    # Country code to full name and region mapping
    country_mapping = {
    "US": {"name": "United States", "region": "North America", "income": "High income"},
    "KR": {"name": "South Korea", "region": "Asia", "income": "High income"},
    "AU": {"name": "Australia", "region": "Oceania", "income": "High income"},
    "HK": {"name": "Hong Kong", "region": "Asia", "income": "High income"},
    "FR": {"name": "France", "region": "Europe", "income": "High income"},
    "BR": {"name": "Brazil", "region": "South America", "income": "Upper middle income"},
    "LT": {"name": "Lithuania", "region": "Europe", "income": "High income"},
    "CA": {"name": "Canada", "region": "North America", "income": "High income"},
    "DE": {"name": "Germany", "region": "Europe", "income": "High income"},
    "IN": {"name": "India", "region": "Asia", "income": "Lower middle income"},
    "CN": {"name": "China", "region": "Asia", "income": "Upper middle income"},
    "GB": {"name": "United Kingdom", "region": "Europe", "income": "High income"},
    "JP": {"name": "Japan", "region": "Asia", "income": "High income"},
    "ZA": {"name": "South Africa", "region": "Africa", "income": "Upper middle income"},
    "NG": {"name": "Nigeria", "region": "Africa", "income": "Lower middle income"},
    "MX": {"name": "Mexico", "region": "North America", "income": "Upper middle income"},
    "RU": {"name": "Russia", "region": "Europe", "income": "Upper middle income"},
    "IT": {"name": "Italy", "region": "Europe", "income": "High income"},
    "ES": {"name": "Spain", "region": "Europe", "income": "High income"},
    "KE": {"name": "Kenya", "region": "Africa", "income": "Lower middle income"},
    "EG": {"name": "Egypt", "region": "Africa", "income": "Lower middle income"},
    "AR": {"name": "Argentina", "region": "South America", "income": "Upper middle income"},
    "CL": {"name": "Chile", "region": "South America", "income": "High income"},
    "CO": {"name": "Colombia", "region": "South America", "income": "Upper middle income"},
    "SA": {"name": "Saudi Arabia", "region": "Asia", "income": "High income"},
    "NZ": {"name": "New Zealand", "region": "Oceania", "income": "High income"},
    "SE": {"name": "Sweden", "region": "Europe", "income": "High income"},
    "NO": {"name": "Norway", "region": "Europe", "income": "High income"},
    "FI": {"name": "Finland", "region": "Europe", "income": "High income"},
    "DK": {"name": "Denmark", "region": "Europe", "income": "High income"},
    "TR": {"name": "Turkey", "region": "Asia", "income": "Upper middle income"},
    "PL": {"name": "Poland", "region": "Europe", "income": "High income"},
    "PT": {"name": "Portugal", "region": "Europe", "income": "High income"},
    "ID": {"name": "Indonesia", "region": "Asia", "income": "Lower middle income"},
    "IR": {"name": "Iran", "region": "Asia", "income": "Upper middle income"},
    "TH": {"name": "Thailand", "region": "Asia", "income": "Upper middle income"},
    "PH": {"name": "Philippines", "region": "Asia", "income": "Lower middle income"},
    "MY": {"name": "Malaysia", "region": "Asia", "income": "Upper middle income"},
    "BD": {"name": "Bangladesh", "region": "Asia", "income": "Lower middle income"},
    "PK": {"name": "Pakistan", "region": "Asia", "income": "Lower middle income"},
    "VN": {"name": "Vietnam", "region": "Asia", "income": "Lower middle income"},
    "ET": {"name": "Ethiopia", "region": "Africa", "income": "Low income"},
    "GH": {"name": "Ghana", "region": "Africa", "income": "Lower middle income"},
    "UG": {"name": "Uganda", "region": "Africa", "income": "Low income"},
    "TZ": {"name": "Tanzania", "region": "Africa", "income": "Low income"},
    "MO": {"name": "Macao", "region": "Asia", "income": "High income"},
    "AE": {"name": "United Arab Emirates", "region": "Asia", "income": "High income"},
    "QA": {"name": "Qatar", "region": "Asia", "income": "High income"},
    "BH": {"name": "Bahrain", "region": "Asia", "income": "High income"},
    "JO": {"name": "Jordan", "region": "Asia", "income": "Upper middle income"},
    "LB": {"name": "Lebanon", "region": "Asia", "income": "Upper middle income"},
    "CY": {"name": "Cyprus", "region": "Asia", "income": "High income"},
    "GR": {"name": "Greece", "region": "Europe", "income": "High income"},
    "HR": {"name": "Croatia", "region": "Europe", "income": "High income"},
    "RO": {"name": "Romania", "region": "Europe", "income": "High income"},
    "SI": {"name": "Slovenia", "region": "Europe", "income": "High income"},
    "SK": {"name": "Slovakia", "region": "Europe", "income": "High income"},
    "BG": {"name": "Bulgaria", "region": "Europe", "income": "Upper middle income"},
    "MK": {"name": "North Macedonia", "region": "Europe", "income": "Upper middle income"},
    "AL": {"name": "Albania", "region": "Europe", "income": "Upper middle income"},
    "MD": {"name": "Moldova", "region": "Europe", "income": "Upper middle income"},
    "UA": {"name": "Ukraine", "region": "Europe", "income": "Upper middle income"},

    "AF": {"name": "Afghanistan", "region": "Asia", "income": "Low income"},
    "AL": {"name": "Albania", "region": "Europe", "income": "Upper middle income"},
    "DZ": {"name": "Algeria", "region": "Africa", "income": "Upper middle income"},
    "AD": {"name": "Andorra", "region": "Europe", "income": "High income"},
    "AO": {"name": "Angola", "region": "Africa", "income": "Lower middle income"},
    "AG": {"name": "Antigua and Barbuda", "region": "North America", "income": "High income"},
    "AM": {"name": "Armenia", "region": "Asia", "income": "Upper middle income"},
    "AZ": {"name": "Azerbaijan", "region": "Asia", "income": "Upper middle income"},
    "BS": {"name": "Bahamas", "region": "North America", "income": "High income"},
    "BB": {"name": "Barbados", "region": "North America", "income": "High income"},
    "BY": {"name": "Belarus", "region": "Europe", "income": "Upper middle income"},
    "BZ": {"name": "Belize", "region": "North America", "income": "Upper middle income"},
    "BJ": {"name": "Benin", "region": "Africa", "income": "Lower middle income"},
    "BT": {"name": "Bhutan", "region": "Asia", "income": "Lower middle income"},
    "BO": {"name": "Bolivia", "region": "South America", "income": "Lower middle income"},
    "BA": {"name": "Bosnia and Herzegovina", "region": "Europe", "income": "Upper middle income"},
    "BW": {"name": "Botswana", "region": "Africa", "income": "Upper middle income"},
    "BN": {"name": "Brunei", "region": "Asia", "income": "High income"},
    "BF": {"name": "Burkina Faso", "region": "Africa", "income": "Low income"},
    "BI": {"name": "Burundi", "region": "Africa", "income": "Low income"},
    "CV": {"name": "Cabo Verde", "region": "Africa", "income": "Lower middle income"},
    "KH": {"name": "Cambodia", "region": "Asia", "income": "Lower middle income"},
    "CM": {"name": "Cameroon", "region": "Africa", "income": "Lower middle income"},
    "CF": {"name": "Central African Republic", "region": "Africa", "income": "Low income"},
    "TD": {"name": "Chad", "region": "Africa", "income": "Low income"},
    "KM": {"name": "Comoros", "region": "Africa", "income": "Lower middle income"},
    "CD": {"name": "Congo, Democratic Republic of the", "region": "Africa", "income": "Low income"},
    "CG": {"name": "Congo, Republic of the", "region": "Africa", "income": "Lower middle income"},
    "CR": {"name": "Costa Rica", "region": "North America", "income": "Upper middle income"},
    "CU": {"name": "Cuba", "region": "North America", "income": "Upper middle income"},
    "DJ": {"name": "Djibouti", "region": "Africa", "income": "Lower middle income"},
    "DM": {"name": "Dominica", "region": "North America", "income": "Upper middle income"},
    "DO": {"name": "Dominican Republic", "region": "North America", "income": "Upper middle income"},
    "TL": {"name": "East Timor (Timor-Leste)", "region": "Asia", "income": "Lower middle income"},
    "EC": {"name": "Ecuador", "region": "South America", "income": "Upper middle income"},
    "SV": {"name": "El Salvador", "region": "North America", "income": "Lower middle income"},
    "GQ": {"name": "Equatorial Guinea", "region": "Africa", "income": "Upper middle income"},
    "ER": {"name": "Eritrea", "region": "Africa", "income": "Low income"},
    "SZ": {"name": "Eswatini", "region": "Africa", "income": "Lower middle income"},
    "FJ": {"name": "Fiji", "region": "Oceania", "income": "Upper middle income"},
    "GA": {"name": "Gabon", "region": "Africa", "income": "Upper middle income"},
    "GM": {"name": "Gambia", "region": "Africa", "income": "Lower middle income"},
    "GE": {"name": "Georgia", "region": "Asia", "income": "Upper middle income"},
    "GD": {"name": "Grenada", "region": "North America", "income": "High income"},
    "GT": {"name": "Guatemala", "region": "North America", "income": "Upper middle income"},
    "GN": {"name": "Guinea", "region": "Africa", "income": "Low income"},
    "GW": {"name": "Guinea-Bissau", "region": "Africa", "income": "Low income"},
    "GY": {"name": "Guyana", "region": "South America", "income": "Upper middle income"},
    "HT": {"name": "Haiti", "region": "North America", "income": "Low income"},
    "HN": {"name": "Honduras", "region": "North America", "income": "Lower middle income"},
    "IS": {"name": "Iceland", "region": "Europe", "income": "High income"},
    "IQ": {"name": "Iraq", "region": "Asia", "income": "Upper middle income"},
    "IE": {"name": "Ireland", "region": "Europe", "income": "High income"},
    "IL": {"name": "Israel", "region": "Asia", "income": "High income"},
    "CI": {"name": "Ivory Coast (Côte d'Ivoire)", "region": "Africa", "income": "Lower middle income"},
    "JM": {"name": "Jamaica", "region": "North America", "income": "Upper middle income"},
    "KZ": {"name": "Kazakhstan", "region": "Asia", "income": "Upper middle income"},
    "KI": {"name": "Kiribati", "region": "Oceania", "income": "Lower middle income"},
    "XK": {"name": "Kosovo", "region": "Europe", "income": "Upper middle income"},
    "KW": {"name": "Kuwait", "region": "Asia", "income": "High income"},
    "KG": {"name": "Kyrgyzstan", "region": "Asia", "income": "Lower middle income"},
    "LA": {"name": "Laos", "region": "Asia", "income": "Lower middle income"},
    "LV": {"name": "Latvia", "region": "Europe", "income": "High income"},
    "LS": {"name": "Lesotho", "region": "Africa", "income": "Lower middle income"},
    "LR": {"name": "Liberia", "region": "Africa", "income": "Low income"},
    "LY": {"name": "Libya", "region": "Africa", "income": "Upper middle income"},
    "LI": {"name": "Liechtenstein", "region": "Europe", "income": "High income"},
    "LU": {"name": "Luxembourg", "region": "Europe", "income": "High income"},
    "MG": {"name": "Madagascar", "region": "Africa", "income": "Low income"},
    "MW": {"name": "Malawi", "region": "Africa", "income": "Low income"},
    "MV": {"name": "Maldives", "region": "Asia", "income": "Upper middle income"},
    "ML": {"name": "Mali", "region": "Africa", "income": "Low income"},
    "MT": {"name": "Malta", "region": "Europe", "income": "High income"},
    "MH": {"name": "Marshall Islands", "region": "Oceania", "income": "Upper middle income"},
    "MR": {"name": "Mauritania", "region": "Africa", "income": "Lower middle income"},
    "MU": {"name": "Mauritius", "region": "Africa", "income": "Upper middle income"},
    "FM": {"name": "Micronesia", "region": "Oceania", "income": "Lower middle income"},
    "MC": {"name": "Monaco", "region": "Europe", "income": "High income"},

    "MN": {"name": "Mongolia", "region": "Asia", "income": "Lower middle income"},
    "ME": {"name": "Montenegro", "region": "Europe", "income": "Upper middle income"},
    "MA": {"name": "Morocco", "region": "Africa", "income": "Lower middle income"},
    "MZ": {"name": "Mozambique", "region": "Africa", "income": "Low income"},
    "NA": {"name": "Namibia", "region": "Africa", "income": "Upper middle income"},
    "NR": {"name": "Nauru", "region": "Oceania", "income": "High income"},
    "NP": {"name": "Nepal", "region": "Asia", "income": "Lower middle income"},
    "NI": {"name": "Nicaragua", "region": "North America", "income": "Lower middle income"},
    "NE": {"name": "Niger", "region": "Africa", "income": "Low income"},
    "KP": {"name": "North Korea", "region": "Asia", "income": "Low income"},
    "MK": {"name": "North Macedonia", "region": "Europe", "income": "Upper middle income"},
    "OM": {"name": "Oman", "region": "Asia", "income": "High income"},
    "PW": {"name": "Palau", "region": "Oceania", "income": "High income"},
    "PA": {"name": "Panama", "region": "North America", "income": "Upper middle income"},
    "PG": {"name": "Papua New Guinea", "region": "Oceania", "income": "Lower middle income"},
    "PY": {"name": "Paraguay", "region": "South America", "income": "Upper middle income"},
    "PE": {"name": "Peru", "region": "South America", "income": "Upper middle income"},
    "RW": {"name": "Rwanda", "region": "Africa", "income": "Low income"},
    "KN": {"name": "Saint Kitts and Nevis", "region": "North America", "income": "High income"},
    "LC": {"name": "Saint Lucia", "region": "North America", "income": "Upper middle income"},
    "VC": {"name": "Saint Vincent and the Grenadines", "region": "North America", "income": "Upper middle income"},
    "WS": {"name": "Samoa", "region": "Oceania", "income": "Lower middle income"},
    "SM": {"name": "San Marino", "region": "Europe", "income": "High income"},
    "ST": {"name": "Sao Tome and Principe", "region": "Africa", "income": "Lower middle income"},
    "SN": {"name": "Senegal", "region": "Africa", "income": "Lower middle income"},
    "SC": {"name": "Seychelles", "region": "Africa", "income": "High income"},
    "SL": {"name": "Sierra Leone", "region": "Africa", "income": "Low income"},
    "SG": {"name": "Singapore", "region": "Asia", "income": "High income"},
    "SB": {"name": "Solomon Islands", "region": "Oceania", "income": "Lower middle income"},
    "SO": {"name": "Somalia", "region": "Africa", "income": "Low income"},
    "SS": {"name": "South Sudan", "region": "Africa", "income": "Low income"},
    "LK": {"name": "Sri Lanka", "region": "Asia", "income": "Lower middle income"},
    "SD": {"name": "Sudan", "region": "Africa", "income": "Lower middle income"},
    "SR": {"name": "Suriname", "region": "South America", "income": "Upper middle income"},
    "SY": {"name": "Syria", "region": "Asia", "income": "Low income"},
    "TJ": {"name": "Tajikistan", "region": "Asia", "income": "Lower middle income"},
    "TO": {"name": "Tonga", "region": "Oceania", "income": "Upper middle income"},
    "TT": {"name": "Trinidad and Tobago", "region": "North America", "income": "High income"},
    "TN": {"name": "Tunisia", "region": "Africa", "income": "Lower middle income"},
    "TM": {"name": "Turkmenistan", "region": "Asia", "income": "Upper middle income"},
    "TV": {"name": "Tuvalu", "region": "Oceania", "income": "Upper middle income"},
    "UY": {"name": "Uruguay", "region": "South America", "income": "High income"},
    "UZ": {"name": "Uzbekistan", "region": "Asia", "income": "Lower middle income"},
    "VU": {"name": "Vanuatu", "region": "Oceania", "income": "Lower middle income"},
    "VE": {"name": "Venezuela", "region": "South America", "income": "Lower middle income"},
    "YE": {"name": "Yemen", "region": "Asia", "income": "Low income"},
    "ZM": {"name": "Zambia", "region": "Africa", "income": "Lower middle income"},
    "ZW": {"name": "Zimbabwe", "region": "Africa", "income": "Low income"},
    "TW": {"name": "Taiwan", "region": "Asia", "income": "High income"},
    "AT": {"name": "Austria", "region": "Europe", "income": "High income"},
    "AE": {"name": "United Arab Emirates", "region": "Asia", "income": "High income"},
    "BE": {"name": "Belgium", "region": "Europe", "income": "High income"},
    "BG": {"name": "Bulgaria", "region": "Europe", "income": "Upper middle income"},
    "CH": {"name": "Switzerland", "region": "Europe", "income": "High income"},
    "EG": {"name": "Egypt", "region": "Africa", "income": "Lower middle income"},
    "HU": {"name": "Hungary", "region": "Europe", "income": "High income"},
    "NL": {"name": "Netherlands", "region": "Europe", "income": "High income"},
    "PS": {"name": "Palestine", "region": "Asia", "income": "Lower middle income"},
    "RS": {"name": "Serbia", "region": "Europe", "income": "Upper middle income"},
    "CZ": {"name": "Czech Republic", "region": "Europe", "income": "High income"},
    "EE": {"name": "Estonia", "region": "Europe", "income": "High income"},
    "GL": {"name": "Greenland", "region": "North America", "income": "High income"},
    "GP": {"name": "Guadeloupe", "region": "North America", "income": "High income"},
    "IM": {"name": "Isle of Man", "region": "Europe", "income": "High income"},
    "JM": {"name": "Jamaica", "region": "North America", "income": "Upper middle income"},
    "LS": {"name": "Lesotho", "region": "Africa", "income": "Lower middle income"},
    "MF": {"name": "Saint Martin", "region": "North America", "income": "High income"},
    "MM": {"name": "Myanmar", "region": "Asia", "income": "Lower middle income"},
    "MQ": {"name": "Martinique", "region": "North America", "income": "High income"},
    "NE": {"name": "Niger", "region": "Africa", "income": "Low income"},
    "NI": {"name": "Nicaragua", "region": "North America", "income": "Lower middle income"},
    "PF": {"name": "French Polynesia", "region": "Oceania", "income": "Upper middle income"},
    "PR": {"name": "Puerto Rico", "region": "North America", "income": "High income"},
    "RE": {"name": "Réunion", "region": "Africa", "income": "Upper middle income"},
    "TG": {"name": "Togo", "region": "Africa", "income": "Low income"}
    }

    # Replace country codes with full names, regions, and incomes for relevant columns
    country_columns = [
        'OpenAlex Countries',
        'OpenAlex First Authors Countries',
        'OpenAlex Last Authors Countries',
        'OpenAlex Corresponding Authors Countries'
    ]

    for column in country_columns:
        df[f'{column} Full Name'] = df[column].apply(lambda x: np.nan if pd.isna(x) else ', '.join([str(country_mapping.get(str(code), {}).get("name", '')) for code in str(x).split(', ')]))
        df[f'{column} Region'] = df[column].apply(lambda x: np.nan if pd.isna(x) else ', '.join([str(country_mapping.get(str(code), {}).get("region", '')) for code in str(x).split(', ')]))
        df[f'{column} Income'] = df[column].apply(lambda x: np.nan if pd.isna(x) else ', '.join([str(country_mapping.get(str(code), {}).get("income", '')) for code in str(x).split(', ')]))

    return rename_columns(df)
    # return rename_columns(pd.DataFrame(publications_data))

# Layout

def layout():
    return dbc.Container([
        Navbar(),
        create_onboarding_modal(),

        dbc.Row(dbc.Col(html.H1('Publication Metadata Collector'), className="d-flex justify-content-center")),
        dbc.Row(dbc.Col(html.P("Select your input method to fetch and enrich publication data."), className="d-flex justify-content-center")),

        dbc.Row([
            dbc.Col(dcc.RadioItems(
                id='input-type',
                options=[
                    {'label': 'OpenAlex API    .', 'value': 'api'},
                    {'label': 'DOI Only    .', 'value': 'doi'},
                    {'label': 'Both API and DOI', 'value': 'both'}
                ],
                value='api',
                inline=True,
                className="mb-4"
            ), width=12, className="d-flex justify-content-center")
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Input(
                    id='api-input', 
                    type='text', 
                    placeholder='Enter OpenAlex API query', 
                    debounce=True, 
                    style={'display': 'block', 'width': '100%'},
                    className="mb-3 mx-auto"
                ),
                html.Div([
                    dcc.Upload(
                        id='doi-upload',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select a File')
                        ]),
                        accept='.csv, .txt',
                        style={'display': 'none'}
                    )
                ], style={'border': '1px dashed', 'padding': '10px', 'textAlign': 'center', 'margin-top': '10px'}),
                # html.Div(id='file-upload-alert', style={'display': 'none'}, color="info"),

                html.Div(
                    "Or manually enter DOIs (comma-separated):", 
                    style={'margin-top': '20px', 'display': 'none'}, 
                    id='manual-doi-label'
                ),
                dcc.Textarea(
                    id='manual-doi-input', 
                    placeholder='e.g., 10.1001/jama.2018.12345', 
                    style={'margin-top': '10px', 'display': 'none', 'height': '200px', 'width': '100%'},
                    className="mb-3 mx-auto"
                )
            ], width=5, className="justify-content-center align-items-center flex-column")
        ], justify="center"),



        dbc.Row([
            dbc.Col(html.Button('Submit', id='submit-button', className="mt-3 btn-primary"), className="d-flex justify-content-center")
        ]),

        dbc.Row(dbc.Col(dbc.Checklist(
            options=[
                {'label': 'Include Crossref Data', 'value': 'crossref'},
                {'label': 'Include Altmetric Data', 'value': 'altmetric'}
            ],
            value=[],
            id='data-options',
            inline=True,
            className="text-center"
        ), className="d-flex justify-content-center")),

        dbc.Row(dbc.Col(dbc.Alert(id='file-upload-alert', color="info", style={"display": "none"}), className="d-flex justify-content-center")),
        dbc.Row(dbc.Col(dbc.Alert(id='status-alert', color="info", style={"display": "none"}), className="d-flex justify-content-center")),
        dbc.Row(dbc.Col(html.Div(id='spinner-container', children=[
            dbc.Spinner(size="lg", color="primary")
        ], style={'display': 'none'}), className="d-flex justify-content-center")),

        dbc.Row([
            dbc.Col(dbc.Progress(id="progress-bar", value=0, striped=True, animated=True, style={"display": "none"}))
        ]),


        dbc.Row(dbc.Col(html.Button('Download Publications List', id='download-button', disabled=True, style={'display': 'none'}), className="d-flex justify-content-center")),
        dcc.Download(id='download-link'),

        dcc.Store(id='stored-data'),
        html.Div(id='table-container', className="mt-3"),

        Footer()
    ], fluid=True)#, className="justify-content-center align-items-center flex-column")


############################ Callbacks for the input fields ############################
@app.callback(
    Output("onboarding-modal", "is_open"),
    [Input("close-onboarding", "n_clicks")],
    [State("onboarding-modal", "is_open")],
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    [
        Output('api-input', 'style'),
        Output('doi-upload', 'style'),
        Output('manual-doi-label', 'style'),
        Output('manual-doi-input', 'style')
    ],
    [Input('input-type', 'value')]
)
def toggle_input_fields(input_type):
    if input_type == 'api':
        return (
            {'display': 'block', 'width': '100%'},  # Show API input
            {'display': 'none'},  # Hide file upload
            {'display': 'none'},  # Hide manual DOI label
            {'display': 'none'}   # Hide manual DOI input
        )
    elif input_type == 'doi':
        return (
            {'display': 'none'},  # Hide API input
            {'display': 'block', 'width': '100%'},  # Show file upload
            {'display': 'block'},  # Show manual DOI label
            {'display': 'block', 'width': '100%'}   # Show manual DOI input
        )
    elif input_type == 'both':
        return (
            {'display': 'block', 'width': '100%'},  # Show API input
            {'display': 'block', 'width': '100%'},  # Show file upload
            {'display': 'block'},  # Show manual DOI label
            {'display': 'block', 'width': '100%'}   # Show manual DOI input
        )
    else:
        return (
            {'display': 'none'},  # Hide all
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'none'}
        )

########################### Callbacks for the main layout ###########################
@app.callback(
    [
        Output('status-alert', 'children'),
        Output('status-alert', 'style'),
        Output('spinner-container', 'style'),
        Output('stored-data', 'data'),
        Output('table-container', 'children'),
        Output('download-button', 'disabled'),
        Output('download-button', 'style'),
        Output('file-upload-alert', 'children'),
        Output('file-upload-alert', 'style'),
        Output('progress-bar', 'style'),
        Output('progress-bar', 'value'),
        Output('progress-bar', 'label')
    ],
    [Input('input-type', 'value'), Input('submit-button', 'n_clicks'), Input('doi-upload', 'contents')],
    [State('api-input', 'value'), State('manual-doi-input', 'value'), State('data-options', 'value'), State('doi-upload', 'filename')],
    prevent_initial_call=True
)
def process_inputs(input_type, n_clicks, file_contents, api_input, manual_doi_input, data_options, filename):
    if n_clicks is None:
        raise PreventUpdate

    include_crossref = 'crossref' in data_options
    include_altmetric = 'altmetric' in data_options

    try:
        dois = []
        file_upload_alert = ""
        file_upload_alert_style = {'display': 'none'}

        if file_contents:
            dois = parse_uploaded_file(file_contents, filename)
            file_upload_alert = f"File '{filename}' uploaded successfully."
            file_upload_alert_style = {'display': 'block', 'color': 'success'}

        if manual_doi_input:
            manual_dois = [clean_doi(doi.strip()) for doi in manual_doi_input.split(',') if doi.strip()]
            dois.extend(manual_dois)

        if input_type == 'doi' and not dois:
            return (
                "No DOIs provided.",
                {'display': 'block', 'color': 'warning'},
                {'display': 'none'},
                None,
                None,
                True,
                {'display': 'none'},
                file_upload_alert,
                file_upload_alert_style,
                {'display': 'none'},
                0,
                ""
            )


        if input_type == 'api':
            works = fetch_openalex_publications(api_input)
        elif input_type == 'doi':
            works = fetch_works_by_doi(dois)
        elif input_type == 'both':
            api_works = fetch_openalex_publications(api_input)
            doi_works = fetch_works_by_doi(dois)
            works = api_works + doi_works
            # Remove duplicate works based on DOI
            unique_works = {work['doi']: work for work in works if 'doi' in work}
            works = list(unique_works.values())

        if not works:
            return (
            "No publications found.",
            {'display': 'block', 'color': 'warning'},
            {'display': 'none'},
            None,
            None,
            True,
            {'display': 'none'},
            file_upload_alert,
            file_upload_alert_style,
            {'display': 'none'},
            0,
            ""
            )
        # else:
        #     print (
        #     "Processing publications, please wait......",
        #     {'display': 'block', 'color': 'info'},
        #     {'display': 'none'},
        #     )
            

        df = build_publications_dataframe(works, include_crossref, include_altmetric)

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
            f"{len(df)} publications fetched successfully.",
            {'display': 'block', 'color': 'success'},
            {'display': 'none'},
            df.to_dict('records'),
            table,
            False,
            {'display': 'block'},
            file_upload_alert,
            file_upload_alert_style,
            {'display': 'block'},
            100,
            "Completed"
        )

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return (
            f"An error occurred: {e}",
            {'display': 'block', 'color': 'danger'},
            {'display': 'none'},
            None,
            None,
            True,
            {'display': 'none'},
            f"An error occurred while uploading the file: {e}",
            {'display': 'block', 'color': 'danger'},
            {'display': 'none'},
            0,
            ""
        )
########################### Callbacks for the download button ###########################
@app.callback(
    Output('download-link', 'data'),
    [Input('download-button', 'n_clicks')],
    [State('stored-data', 'data')],
    prevent_initial_call=True
)
def download_publications_list(n_clicks, stored_data):
    if not stored_data:
        raise PreventUpdate

    df = pd.DataFrame(stored_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"publications_list_{timestamp}.csv"
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
    app.layout = layout()
    app.run_server(debug=True)
