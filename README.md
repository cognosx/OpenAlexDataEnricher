OpenAlex Data Enricher Application Guide
Introduction

Welcome to the OpenAlex Data Enricher, a tool designed to streamline the process of retrieving and enriching academic publications data. By using this tool, you can quickly access and preprocess publication data from OpenAlex, making it readily available for bibliometrics, scientometrics, research collaboration studies, or network analysis studies. This application also enriches the data with Altmetric and Crossref metadata.
Tools and Libraries Used

    Dash: A Python framework for building analytical web applications.
    Pandas: A data manipulation and analysis library.
    Requests: A library for making HTTP requests.
    Dash Bootstrap Components: Bootstrap components for Dash applications.
    Flask Caching: A Flask extension for adding cache support to Flask applications.
    OpenAlex API: An API for accessing academic publication data.
    Crossref API: An API for accessing publication metadata.
    Altmetric API: An API for accessing publication altmetrics data.

Methodology

Our application utilizes a combination of reliable data sources and sophisticated algorithms to fetch and enrich publication information:

    User Input: Users input an API link from OpenAlex to fetch publication data.
    Data Fetching: The application fetches publication data from OpenAlex using cursor-based pagination to handle large datasets.
    Data Enrichment: The fetched data is enriched with additional metadata from Crossref and Altmetric APIs.
    Data Processing: The enriched data is processed to extract relevant information, including authors, institutions, keywords, and citation counts.
    Data Display: The processed data is displayed in a table, and users can download the data as a CSV file.

Building Queries on OpenAlex

To collect data from OpenAlex, you need to construct a query that specifies the parameters for your search. Follow these steps to build your query and obtain the API link:

    Visit the OpenAlex API documentation at: OpenAlex API Documentation
    Identify the parameters you need for your search, such as authorships, institutions, publication year, title, and abstract search terms, etc.
    Construct your query by combining these parameters. For example, to search for publications on HIV/AIDS from 2014 to 2024 in articles, reviews, and letters from institutions in Africa, your query might look like this:

    https://api.openalex.org/works?filter=authorships.institutions.continent:q15,publication_year:2014-2024,title_and_abstract.search:hiv+OR+aids+OR+%22Human+Immunodeficiency+Virus%22+OR+%22HIV/AIDS%22+OR+%22Human+Immunodeficiency+Viruses%22+OR+%22human+immuno-deficiency+virus%22+OR+%22Acquired+Immune+Deficiency+Syndrome%22+OR+%22Acquired+Immunodeficiency+Syndrome%22,type:types/article|types/preprint|types/review|types/letter

    Copy the generated API link and paste it into the search input of the OpenAlex Data Enricher application.

Step-by-Step Guide

    Enter the OpenAlex API link: On the main page, you'll find an input box. Paste your API link here.
    Select Data Options: Check the boxes if you want to include Crossref and Altmetric data.
    Submit Search: Click the 'Submit' button to initiate the search.
    Review Your Publications: Once fetched, your publications will be displayed on the screen. You can review the list directly within the application.
    Download Option: A 'Download Publications List' button allows you to export the list of publications in CSV format for your convenience.

Using the Application

    Input Search Parameters: Enter your search terms in the input field. For example, 'HIV OR AIDS'.
    Select Data Options: Check the boxes if you want to include Crossref and Altmetric data.
    Submit Search: Click the 'Submit' button to start fetching the data.
    View Data: The fetched data will be displayed in a table. You can filter and sort the data directly in the table.
    Download Data: Click the 'Download Publications List' button to download the data as a CSV file.

FAQs

    Q: What is OpenAlex? A: OpenAlex is an index of millions of interconnected entities across the global research system, including works, authors, institutions, and more.
    Q: How do I build a query on OpenAlex? A: Refer to the 'Building Queries on OpenAlex' section above for detailed instructions.
    Q: Can I include Crossref and Altmetric data? A: Yes, you can select the options to include Crossref and Altmetric data when you submit your search.
    Q: Why does it take a long time to fetch data? A: Fetching data from Crossref and Altmetric APIs can take time. You can choose to exclude these options if you only need basic publication data.
    Q: How can I download the fetched data? A: After the data is fetched, you can click the 'Download Publications List' button to download the data as a CSV file.
    Q: What if I encounter an error? A: If you encounter an error, please check your API link and search parameters. For further assistance, contact us at cognosxx@gmail.com.

Contact Information

For further assistance or to provide feedback, please contact us at cognosxx@gmail.com. We are committed to improving your experience and appreciate your input.
Links to Further Resources

    Crossref
    Altmetric
    OpenAlex

Conclusion

The OpenAlex Data Enricher aims to simplify the retrieval and enrichment of publication information for researchers and academics. By leveraging the OpenAlex API, we provide a quick and efficient way to access and download your publication list enriched with additional metadata. For any queries or feedback, don't hesitate to reach out to us.
