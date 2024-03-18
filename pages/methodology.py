# pages/methodology.py
from dash import html
from components.navbar import Navbar  # Adjust according to your file structure
from components.footer import Footer

import dash_bootstrap_components as dbc

def layout():
    return html.Div([
            Navbar(),
            dbc.Row(dbc.Col(html.H1("Publications Fetcher Application Guide"), className="d-flex justify-content-center")),
            dbc.Row(dbc.Col(html.H2("Introduction")), className="page-padding"),
            dbc.Row(dbc.Col(html.P(
                "Welcome to the Publications Fetcher, a tool designed to streamline the process of retrieving your academic publications. "
                "By simply entering your ORCID ID, you can quickly access a list of your publications. This application aims to save time and effort "
                "in tracking down your research outputs, making them readily available for review or download."
            )), className="page-padding"),
            dbc.Row(dbc.Col(html.H2("Methodology Details")), className="page-padding"),
            dbc.Row(dbc.Col(html.P(
                "Our application utilizes a combination of reliable data sources and sophisticated algorithms to fetch publication information:"
            )), className="page-padding"),
            dbc.Row(dbc.Col(html.Ul([
                html.Li("ORCID Integration: By entering your ORCID ID, the app queries the ORCID API to retrieve a list of publications associated with your account."),
                html.Li("Crossref and Altmetric: For each publication, we further enrich the data by fetching metadata from Crossref and altmetrics from Altmetric.com. "
                        "This provides comprehensive details about each publication, including titles, authors, journal information, and more."),
                html.Li("Data Accuracy and Privacy: We prioritize the accuracy of the data fetched and the privacy of our users. "
                        "No personal information is stored or used beyond the scope of publication fetching."),
            ], className="page-padding"))),
            dbc.Row(dbc.Col(html.H2("Step-by-Step Guide")), className="page-padding"),
            dbc.Row(dbc.Col(html.Ol([
                html.Li("Start by Entering Your ORCID ID: On the main page, you'll find an input box. Enter your ORCID ID in the format 0000-0002-1825-0097."),
                html.Li("Submit Your ID: Click the 'Submit' button to initiate the search."),
                html.Li("Review Your Publications: Once fetched, your publications will be displayed on the screen. You can review the list directly within the application."),
                html.Li("Download Option: A 'Download Publications List' button allows you to export the list of publications in CSV format for your convenience."),
            ], className="page-padding"), className="mb-3")),
            dbc.Row(dbc.Col([
                html.H2("Visual Aids"),
                html.P("Throughout the guide, we provide screenshots and videos demonstrating each step to ensure clarity and ease of use.")
            ], className="page-padding")),
            dbc.Row(dbc.Col(html.H2("FAQs")), className="page-padding"),
            dbc.Row(dbc.Col(html.Ul([
                html.Li("Q: What is an ORCID ID? A: ORCID provides a persistent digital identifier that distinguishes you from every other researcher."),
                html.Li("Q: Can I fetch publications without an ORCID ID? A: Currently, our application requires an ORCID ID to fetch publications."),
            ], className="page-padding"))),
            dbc.Row(dbc.Col([
                html.H2("Contact Information"),
                html.P("For further assistance or to provide feedback, please contact us at cognosxx@gmail.com. "
                       "We are committed to improving your experience and appreciate your input.")
            ], className="page-padding")),
            dbc.Row(dbc.Col(html.H2("Links to Further Resources")), className="page-padding"),
            dbc.Row(dbc.Col(html.Ul([
                html.Li(html.A("ORCID", href="https://orcid.org/", target="_blank")),
                html.Li(html.A("Crossref", href="https://www.crossref.org/", target="_blank")),
                html.Li(html.A("Altmetric", href="https://www.altmetric.com/", target="_blank")),
            ], className="page-padding"))),
            dbc.Row(dbc.Col([
                html.H2("Conclusion"),
                html.P("The Publications Fetcher aims to simplify the retrieval of publication information for researchers and academics. "
                       "By leveraging your ORCID ID, we provide a quick and efficient way to access and download your publication list. "
                       "For any queries or feedback, don't hesitate to reach out to us.")
            ], className="page-padding")),
            Footer(),
        ],
    )
