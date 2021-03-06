# MRH, Dec 2021

import requests
import xml.etree.ElementTree as et
import regex as re

tag_remove = ['italic', 'bold', 'sup', 'sub', 'underline', 'title', 'sec', 'p',
             'list', 'list-item', 'named-content']
total_remove = ['xref', 'table-wrap', 'fig', 'label', 'a', 'inline-formula']

def extract_clean(text, tag_remove=tag_remove, total_remove=total_remove):
    """XML string will come in.
    Everything within <body>...</body> will come out,
    every tag in tag_remove is gone (but content still there),
    every tag in total_remove is gone, with it contents also removed,
    every special character removed, e.g. &#x0003e;
    Line breaks replaced by spaces.
    Opening tags may have extra info, removed through regex: 
    e.g. '<xref[\s\S]*?>' removes tags like <xref rid="ppat.100...>
    
    Inputs:
    text: XML string
    tag_remove: list of tags (only opening tags, without parameters and "<") 
                for which the content will stay, tags removed
    total_remove: list of tags (only opening, without parameters and "<")
                  which willl be removed, including their content
                  
    Output:
    Clean text string, ready for language model
    
    """
    
    assert type(text) == str
    
    if '<body>' not in text: 
        print("Can't find the body, returning nothing!")
        return ''
    
    body_pos = text.find("<body>") + len("<body>")
    end_pos = text.find("</body>")
    
    text = text[body_pos:end_pos]
    
    for t in tag_remove:
        pattern = f'<{t}[\s\S]*?>' 
        text = re.sub(pattern, ' ', text, count=10000)
        pattern = f'</{t}>'
        text = re.sub(pattern, ' ', text, count=10000)
        
    for t in total_remove:
        pattern = f'<{t}[\s\S]*?>[\s\S]*?</{t}>'
        text = re.sub(pattern, ' ', text, count=10000)
        
    pattern = '&#x[\S]{5};'
    text = re.sub(pattern, ' ', text, count=10000)
    text = re.sub('\\n', ' ', text, count=10000)
    
    return text


def perform_query(query, page_size=25):
    """Query to perform on Europe PMC, returning
    a list of PMC IDs, which can be queried later
    
    Params
    -------
    query: str
      A string with keywords such as 'trichome', 'covid-19'. Multiple keywords have to be separated with %20 such as 
      'trichome%20%tomato'
    page_size: int
      An integer specifying the number of articles to retrieve per page. The default value is 25, the maximum is 1000
    
    Returns
    -------
    IDs: list
      A list of Europe PubMed Central identifiers e.g. ['PMC6480907', 'PMC8497795', 'PMC8514689', 'PMC8590222', 'PMC8245418'] 
    """
    # Check if page size < 1000
    assert isinstance(page_size, int), 'page_size parameter has to be a positive integer'
    assert page_size <= 1000, 'page_size parameter has to be lower than 1000'
        
    # Get data and write XML (URL should result from a query)
    full_query = query + '&pageSize=' + str(page_size) 
    URL = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={full_query}"
    response = requests.get(URL)
    data = response.content.decode()
    
    # Parse XML and extract sensible tags
    root = et.XML(data)
    IDs = []
    for pmc in root.iter("pmcid"):
        IDs.append(pmc.text)
        
    return IDs


def retrieve_paper(PMCID):
    """For a given PMCID,
    retrieve the papaer from Europe PMC. 
    Decoded plain text content will be returned."""
    
    URL = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML"
    response = requests.get(URL)
    data = response.content.decode()
    return data
