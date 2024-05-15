# pages/methodology.py
from dash import html
from components.navbar import Navbar  # Adjust according to your file structure
from components.footer import Footer
import dash_bootstrap_components as dbc

def layout():
    return html.Div([
        Navbar(),
        dbc.Row(dbc.Col(html.H1("OpenAlex Data Enricher Application Guide"), className="d-flex justify-content-center")),
        
        dbc.Row(dbc.Col(html.H2("Introduction")), className="page-padding"),
        dbc.Row(dbc.Col(html.P(
            "Welcome to the OpenAlex Data Enricher, a tool designed to streamline the process of retrieving and enriching academic publications data. "
            "By using this tool, you can quickly access and preprocess publication data from OpenAlex, making it readily available for bibliometrics, scientometrics, "
            "research collaboration studies, or network analysis studies. This application also enriches the data with Altmetric and Crossref metadata."
        )), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Tools and Libraries Used")), className="page-padding"),
        dbc.Row(dbc.Col(html.Ul([
            html.Li("Dash: A Python framework for building analytical web applications."),
            html.Li("Pandas: A data manipulation and analysis library."),
            html.Li("Requests: A library for making HTTP requests."),
            html.Li("Dash Bootstrap Components: Bootstrap components for Dash applications."),
            html.Li("Flask Caching: A Flask extension for adding cache support to Flask applications."),
            html.Li("OpenAlex API: An API for accessing academic publication data."),
            html.Li("Crossref API: An API for accessing publication metadata."),
            html.Li("Altmetric API: An API for accessing publication altmetrics data."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Methodology")), className="page-padding"),
        dbc.Row(dbc.Col(html.P(
            "Our application utilizes a combination of reliable data sources and sophisticated algorithms to fetch and enrich publication information:"
        )), className="page-padding"),
        dbc.Row(dbc.Col(html.Ul([
            html.Li("User Input: Users input an API link from OpenAlex to fetch publication data."),
            html.Li("Data Fetching: The application fetches publication data from OpenAlex using cursor-based pagination to handle large datasets."),
            html.Li("Data Enrichment: The fetched data is enriched with additional metadata from Crossref and Altmetric APIs."),
            html.Li("Data Processing: The enriched data is processed to extract relevant information, including authors, institutions, keywords, and citation counts."),
            html.Li("Data Display: The processed data is displayed in a table, and users can download the data as a CSV file."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Building Queries on OpenAlex")), className="page-padding"),
        dbc.Row(dbc.Col(html.P(
            "To collect data from OpenAlex, you need to construct a query that specifies the parameters for your search. Follow these steps to build your query and obtain the API link:"
        )), className="page-padding"),
        dbc.Row(dbc.Col(html.Ol([
            html.Li([
                "Visit the OpenAlex API documentation at: ",
                html.A("OpenAlex API Documentation", href="https://docs.openalex.org/", target="_blank")
            ]),
            html.Li("Identify the parameters you need for your search, such as authorships, institutions, publication year, title, and abstract search terms, etc."),
            html.Li("Construct your query by combining these parameters. For example, to search for publications on HIV/AIDS from 2014 to 2024 in articles, reviews, and letters from institutions in Africa, your query might look like this:"),
            html.Pre(html.Code(
                "https://api.openalex.org/works?filter=authorships.institutions.continent:q15,publication_year:2014-2024,"
                "title_and_abstract.search:hiv+OR+aids+OR+%22Human+Immunodeficiency+Virus%22+OR+%22HIV/AIDS%22+OR+%22Human+Immunodeficiency+Viruses%22+OR+"
                "%22human+immuno-deficiency+virus%22+OR+%22Acquired+Immune+Deficiency+Syndrome%22+OR+%22Acquired+Immunodeficiency+Syndrome%22,"
                "type:types/article|types/preprint|types/review|types/letter"
            )),
            html.Li("Copy the generated API link and paste it into the search input of the OpenAlex Data Enricher application."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Step-by-Step Guide")), className="page-padding"),
        dbc.Row(dbc.Col(html.Ol([
            html.Li("Enter the OpenAlex API link: On the main page, you'll find an input box. Paste your API link here."),
            html.Li("Select Data Options: Check the boxes if you want to include Crossref and Altmetric data."),
            html.Li("Submit Search: Click the 'Submit' button to initiate the search."),
            html.Li("Review Your Publications: Once fetched, your publications will be displayed on the screen. You can review the list directly within the application."),
            html.Li("Download Option: A 'Download Publications List' button allows you to export the list of publications in CSV format for your convenience."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Using the Application")), className="page-padding"),
        dbc.Row(dbc.Col(html.Ol([
            html.Li("Input Search Parameters: Enter your search terms in the input field. For example, 'HIV OR AIDS'."),
            html.Li("Select Data Options: Check the boxes if you want to include Crossref and Altmetric data."),
            html.Li("Submit Search: Click the 'Submit' button to start fetching the data."),
            html.Li("View Data: The fetched data will be displayed in a table. You can filter and sort the data directly in the table."),
            html.Li("Download Data: Click the 'Download Publications List' button to download the data as a CSV file."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("FAQs")), className="page-padding"),
        dbc.Row(dbc.Col(html.Ul([
            # html.Li("Q: What is an ORCID ID? A: ORCID provides a persistent digital identifier that distinguishes you from every other researcher."),
            # html.Li("Q: Can I fetch publications without an ORCID ID? A: Currently, our application requires an ORCID ID to fetch publications."),
            html.Li("Q: What is OpenAlex? A: OpenAlex is an index of millions of interconnected entities across the global research system, including works, authors, institutions, and more."),
            html.Li("Q: How do I build a query on OpenAlex? A: Refer to the 'Building Queries on OpenAlex' section above for detailed instructions."),
            html.Li("Q: Can I include Crossref and Altmetric data? A: Yes, you can select the options to include Crossref and Altmetric data when you submit your search."),
            html.Li("Q: Why does it take a long time to fetch data? A: Fetching data from Crossref and Altmetric APIs can take time. You can choose to exclude these options if you only need basic publication data."),
            html.Li("Q: How can I download the fetched data? A: After the data is fetched, you can click the 'Download Publications List' button to download the data as a CSV file."),
            html.Li("Q: What if I encounter an error? A: If you encounter an error, please check your API link and search parameters. For further assistance, contact us at cognosxx@gmail.com."),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Contact Information")), className="page-padding"),
        dbc.Row(dbc.Col(html.P(
            "For further assistance or to provide feedback, please contact us at cognosxx@gmail.com. "
            "We are committed to improving your experience and appreciate your input."
        )), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Links to Further Resources")), className="page-padding"),
        dbc.Row(dbc.Col(html.Ul([
            # html.Li(html.A("ORCID", href="https://orcid.org/", target="_blank")),
            html.Li(html.A("Crossref", href="https://www.crossref.org/", target="_blank")),
            html.Li(html.A("Altmetric", href="https://www.altmetric.com/", target="_blank")),
            html.Li(html.A("OpenAlex", href="https://openalex.org/", target="_blank")),
        ])), className="page-padding"),
        
        dbc.Row(dbc.Col(html.H2("Conclusion")), className="page-padding"),
        dbc.Row(dbc.Col(html.P(
            "The OpenAlex Data Enricher aims to simplify the retrieval and enrichment of publication information for researchers and academics. "
            "By leveraging the OpenAlex API, we provide a quick and efficient way to access and download your publication list enriched with additional metadata. "
            "For any queries or feedback, don't hesitate to reach out to us."
        )), className="page-padding"),
        
        Footer(),
    ])
