import feedparser
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

ARXIV_CS_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.CC", "cs.CE", "cs.CG", "cs.GT", "cs.CV",
    "cs.CY", "cs.CR", "cs.DS", "cs.DB", "cs.DL", "cs.DM", "cs.DC",
    "cs.ET", "cs.FL", "cs.GL", "cs.GR", "cs.AR", "cs.HC", "cs.IR",
    "cs.IT", "cs.LG", "cs.LO", "cs.MS", "cs.MA", "cs.MM", "cs.NI",
    "cs.NE", "cs.NA", "cs.OS", "cs.OH", "cs.PF", "cs.PL", "cs.RO",
    "cs.SE", "cs.SD", "cs.SC", "cs.SI", "cs.SY"
]

def fetch_daily_papers(category: Optional[str] = None, max_results: int = 50) -> List[Dict]:
    """
    Fetch daily arXiv CS papers, optionally filtered by category.
    Returns a list of paper dictionaries.
    """
    papers = []
    base_url = "http://export.arxiv.org/api/query?"
    query = f"search_query=cat:cs.*"
    if category and category in ARXIV_CS_CATEGORIES:
        query = f"search_query=cat:{category}"
    query += f"&sortBy=submittedDate&sortOrder=descending"
    query += f"&max_results={max_results}"
    query += f"&start=0"
    
    try:
        feed = feedparser.parse(base_url + query)
        for entry in feed.entries:
            paper = {
                'id': entry.id.split('/abs/')[-1],
                'title': entry.title.replace('\n', ' ').strip(),
                'authors': [author.name for author in entry.authors],
                'published': entry.published,
                'updated': entry.updated,
                'summary': entry.summary,
                'pdf_link': entry.link if 'link' in entry else None,
                'primary_category': entry.tags[0]['term'] if entry.tags else 'cs',
                'all_categories': [tag['term'] for tag in entry.tags],
                'doi': entry.doi if 'doi' in entry else None
            }
            for link in entry.links:
                if link.rel == 'alternate' and link.type == 'text/html':
                    paper['arxiv_url'] = link.href
                elif link.title == 'pdf':
                    paper['pdf_link'] = link.href
            papers.append(paper)
    except Exception as e:
        print(f"Error fetching papers: {e}")
    return papers

def fetch_paper_details(paper_id: str) -> Optional[Dict]:
    """
    Fetch detailed metadata for a specific arXiv paper by its ID.
    """
    query_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
    try:
        feed = feedparser.parse(query_url)
        if len(feed.entries) == 0:
            return None
        entry = feed.entries[0]
        paper = {
            'id': paper_id,
            'title': entry.title.replace('\n', ' ').strip(),
            'authors': [author.name for author in entry.authors],
            'published': entry.published,
            'updated': entry.updated,
            'summary': entry.summary,
            'pdf_link': entry.link if 'link' in entry else None,
            'primary_category': entry.tags[0]['term'] if entry.tags else 'cs',
            'all_categories': [tag['term'] for tag in entry.tags],
            'doi': entry.doi if 'doi' in entry else None,
            'comment': entry.get('arxiv_comment', ''),
            'journal_ref': entry.get('arxiv_journal_ref', ''),
            'affiliations': []
        }
        for link in entry.links:
            if link.rel == 'alternate' and link.type == 'text/html':
                paper['arxiv_url'] = link.href
            elif link.title == 'pdf':
                paper['pdf_link'] = link.href
        return paper
    except Exception as e:
        print(f"Error fetching paper details: {e}")
        return None

def generate_citation(paper: Dict, format: str = "bibtex") -> str:
    """
    Generate citation for a paper in specified format.
    Supported formats: 'bibtex', 'plain'
    """
    if format == "bibtex":
        authors = " and ".join(paper['authors'])
        title = paper['title'].replace('{', '\{').replace('}', '\}')
        year = datetime.strptime(paper['published'], '%Y-%m-%dT%H:%M:%SZ').year
        citation = f"""@article{{{paper['id']},
    author = {{{authors}}},
    title = {{{{{title}}}}},
    year = {{{year}}},
    archivePrefix = {{arXiv}},
    eprint = {{{paper['id']}}},
    primaryClass = {{{paper['primary_category']}}}
}}"""
    else:
        authors = ", ".join(paper['authors'])
        title = paper['title']
        year = datetime.strptime(paper['published'], '%Y-%m-%dT%H:%M:%SZ').year
        citation = f"{authors}. \"{title}\". arXiv preprint arXiv:{paper['id']} ({year})."
    return citation

def save_papers_to_json(papers: List[Dict], filename: str = "daily_papers.json"):
    """
    Save fetched papers to a JSON file.
    """
    try:
        with open(filename, 'w') as f:
            json.dump(papers, f, indent=2)
        print(f"Papers saved to {filename}")
    except Exception as e:
        print(f"Error saving papers: {e}")

def load_papers_from_json(filename: str = "daily_papers.json") -> List[Dict]:
    """
    Load papers from a JSON file.
    """
    try:
        with open(filename, 'r') as f:
            papers = json.load(f)
        return papers
    except Exception as e:
        print(f"Error loading papers: {e}")
        return []