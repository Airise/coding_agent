import os
import json
import argparse
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

def create_papers_directory():
    """Create the papers directory if it doesn't exist."""
    papers_dir = Path("project/arxiv_cs_daily/papers")
    papers_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {papers_dir}")

def fetch_daily_papers():
    """Fetch daily arXiv CS papers."""
    # arXiv API query for computer science papers from the last day
    base_url = "http://export.arxiv.org/api/query?"
    query = "search_query=cat:cs*&sortBy=submittedDate&sortOrder=descending&max_results=100"
    url = base_url + query
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching papers: {e}")
        return None

def parse_papers_data(raw_data):
    """Parse raw arXiv data into structured format."""
    if not raw_data:
        return []
    
    root = ET.fromstring(raw_data)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    papers = []
    for entry in root.findall('atom:entry', namespace):
        paper = {}
        
        # Extract paper ID
        id_elem = entry.find('atom:id', namespace)
        if id_elem is not None:
            paper['id'] = id_elem.text.split('/')[-1]
        
        # Extract title
        title_elem = entry.find('atom:title', namespace)
        if title_elem is not None:
            paper['title'] = title_elem.text.strip()
        
        # Extract authors
        authors = []
        for author_elem in entry.findall('atom:author', namespace):
            name_elem = author_elem.find('atom:name', namespace)
            if name_elem is not None:
                authors.append(name_elem.text)
        paper['authors'] = authors
        
        # Extract submission date
        published_elem = entry.find('atom:published', namespace)
        if published_elem is not None:
            paper['submission_date'] = published_elem.text
        
        # Extract summary/abstract
        summary_elem = entry.find('atom:summary', namespace)
        if summary_elem is not None:
            paper['abstract'] = summary_elem.text.strip()
        
        # Extract categories
        categories = []
        for category_elem in entry.findall('atom:category', namespace):
            term = category_elem.get('term')
            if term and term.startswith('cs.'):
                categories.append(term)
        paper['categories'] = categories
        
        # Extract PDF link
        links = entry.findall('atom:link', namespace)
        for link in links:
            if link.get('title') == 'pdf':
                paper['pdf_url'] = link.get('href')
        
        if paper.get('id') and paper.get('title'):
            papers.append(paper)
    
    return papers

def generate_index_page(papers_by_category):
    """Generate the main index page with categorized navigation."""
    # Define arXiv CS categories for navigation
    cs_categories = [
        'cs.AI', 'cs.CL', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.GT', 'cs.CV',
        'cs.CY', 'cs.CR', 'cs.DS', 'cs.DB', 'cs.DL', 'cs.DM', 'cs.DC',
        'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR', 'cs.AR', 'cs.HC', 'cs.IR',
        'cs.IT', 'cs.LG', 'cs.LO', 'cs.MS', 'cs.MA', 'cs.MM', 'cs.NI',
        'cs.NE', 'cs.NA', 'cs.OS', 'cs.OH', 'cs.PF', 'cs.PL', 'cs.RO',
        'cs.SE', 'cs.SD', 'cs.SC', 'cs.SI', 'cs.SY', 'cs.TH'
    ]
    
    # Sort categories alphabetically
    cs_categories.sort()
    
    # Generate navigation HTML
    nav_html = '<nav class="category-nav">\n'
    nav_html += '  <ul>\n'
    nav_html += '    <li><a href="#all" class="category-link active" data-category="all">All Papers</a></li>\n'
    for category in cs_categories:
        nav_html += f'    <li><a href="#{category}" class="category-link" data-category="{category}">{category}</a></li>\n'
    nav_html += '  </ul>\n'
    nav_html += '</nav>\n'
    
    # Generate papers HTML
    papers_html = '<div class="papers-container">\n'
    
    # All papers section
    papers_html += '  <div id="all" class="category-section active">\n'
    papers_html += '    <h2>All Papers</h2>\n'
    papers_html += '    <div class="papers-list">\n'
    
    all_papers = []
    for category, papers in papers_by_category.items():
        all_papers.extend(papers)
    
    # Sort all papers by submission date (newest first)
    all_papers.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
    
    for paper in all_papers:
        paper_id = paper.get('id', '')
        title = paper.get('title', 'Untitled')
        submission_date = paper.get('submission_date', '')
        categories = paper.get('categories', [])
        
        # Format date
        if submission_date:
            date_obj = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
        else:
            formatted_date = 'Unknown date'
        
        # Get primary category for display
        primary_category = categories[0] if categories else 'cs.GEN'
        
        papers_html += f'      <div class="paper-item" data-categories="{" ".join(categories)}">\n'
        papers_html += f'        <h3><a href="papers/{paper_id}.html">{title}</a></h3>\n'
        papers_html += f'        <div class="paper-meta">\n'
        papers_html += f'          <span class="submission-time">{formatted_date}</span>\n'
        papers_html += f'          <span class="arxiv-tag">[{primary_category}]</span>\n'
        papers_html += f'        </div>\n'
        papers_html += f'      </div>\n'
    
    papers_html += '    </div>\n'
    papers_html += '  </div>\n'
    
    # Individual category sections
    for category in cs_categories:
        papers_html += f'  <div id="{category}" class="category-section">\n'
        papers_html += f'    <h2>{category}</h2>\n'
        papers_html += f'    <div class="papers-list">\n'
        
        category_papers = papers_by_category.get(category, [])
        category_papers.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
        
        if not category_papers:
            papers_html += '      <p class="no-papers">No papers in this category today.</p>\n'
        else:
            for paper in category_papers:
                paper_id = paper.get('id', '')
                title = paper.get('title', 'Untitled')
                submission_date = paper.get('submission_date', '')
                
                if submission_date:
                    date_obj = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = 'Unknown date'
                
                papers_html += f'      <div class="paper-item">\n'
                papers_html += f'        <h3><a href="papers/{paper_id}.html">{title}</a></h3>\n'
                papers_html += f'        <div class="paper-meta">\n'
                papers_html += f'          <span class="submission-time">{formatted_date}</span>\n'
                papers_html += f'          <span class="arxiv-tag">[{category}]</span>\n'
                papers_html += f'        </div>\n'
                papers_html += f'      </div>\n'
        
        papers_html += '    </div>\n'
        papers_html += '  </div>\n'
    
    papers_html += '</div>\n'
    
    # Read template and replace placeholders
    template_path = Path("project/arxiv_cs_daily/templates/index_template.html")
    if template_path.exists():
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        html_content = template.replace('{{NAVIGATION}}', nav_html)
        html_content = html_content.replace('{{PAPERS}}', papers_html)
        html_content = html_content.replace('{{BUILD_DATE}}', datetime.now().strftime('%Y-%m-%d'))
        
        # Write to output file
        output_path = Path("project/arxiv_cs_daily/index.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Generated index page: {output_path}")
    else:
        print("Error: Index template not found")

def generate_detail_pages(papers):
    """Generate individual detail pages for each paper."""
    template_path = Path("project/arxiv_cs_daily/templates/detail_template.html")
    if not template_path.exists():
        print("Error: Detail template not found")
        return
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    for paper in papers:
        paper_id = paper.get('id')
        if not paper_id:
            continue
        
        # Prepare paper data
        title = paper.get('title', 'Untitled')
        authors = paper.get('authors', [])
        submission_date = paper.get('submission_date', '')
        abstract = paper.get('abstract', 'No abstract available.')
        categories = paper.get('categories', [])
        pdf_url = paper.get('pdf_url', '#')
        
        # Format date
        if submission_date:
            date_obj = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M UTC')
        else:
            formatted_date = 'Unknown date'
        
        # Generate authors HTML
        authors_html = '<ul class="authors-list">\n'
        for author in authors:
            authors_html += f'  <li>{author}</li>\n'
        authors_html += '</ul>\n'
        
        # Generate categories HTML
        categories_html = '<div class="paper-categories">\n'
        for category in categories:
            categories_html += f'  <span class="category-tag">{category}</span>\n'
        categories_html += '</div>\n'
        
        # Generate citation data
        bibtex_citation = f"""@misc{{{paper_id},
  title = {{{title}}},
  author = {{{' and '.join(authors)}}},
  year = {{{date_obj.year if submission_date else 'Unknown'}}},
  eprint = {{{paper_id}}},
  archivePrefix = {{arXiv}},
  primaryClass = {{{categories[0] if categories else 'cs'}}}
}}"""
        
        # Generate HTML citation
        html_citation = f"""<div class="citation">
  {', '.join(authors)}. "{title}". <i>arXiv preprint</i> {paper_id} ({date_obj.year if submission_date else 'Unknown'}).
</div>"""
        
        # Replace placeholders in template
        html_content = template.replace('{{PAPER_TITLE}}', title)
        html_content = html_content.replace('{{PAPER_ID}}', paper_id)
        html_content = html_content.replace('{{AUTHORS}}', authors_html)
        html_content = html_content.replace('{{SUBMISSION_DATE}}', formatted_date)
        html_content = html_content.replace('{{ABSTRACT}}', abstract)
        html_content = html_content.replace('{{CATEGORIES}}', categories_html)
        html_content = html_content.replace('{{PDF_URL}}', pdf_url)
        html_content = html_content.replace('{{BIBTEX_CITATION}}', bibtex_citation)
        html_content = html_content.replace('{{HTML_CITATION}}', html_citation)
        html_content = html_content.replace('{{BUILD_DATE}}', datetime.now().strftime('%Y-%m-%d'))
        
        # Write detail page
        output_path = Path(f"project/arxiv_cs_daily/papers/{paper_id}.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    print(f"Generated {len(papers)} detail pages")

def build_site():
    """Main function to build the entire site."""
    parser = argparse.ArgumentParser(description='Build arXiv CS Daily website')
    parser.add_argument('--test', action='store_true', help='Use test data instead of fetching from arXiv')
    args = parser.parse_args()
    
    print("Building arXiv CS Daily website...")
    
    # Create papers directory
    create_papers_directory()
    
    # Fetch or load papers data
    if args.test:
        print("Using test data...")
        # Create some test data
        papers = [
            {
                'id': '2401.12345',
                'title': 'Test Paper on Machine Learning',
                'authors': ['John Doe', 'Jane Smith'],
                'submission_date': '2024-01-01T12:00:00Z',
                'abstract': 'This is a test abstract for a machine learning paper.',
                'categories': ['cs.LG', 'cs.AI'],
                'pdf_url': 'https://arxiv.org/pdf/2401.12345.pdf'
            },
            {
                'id': '2401.67890',
                'title': 'Another Test Paper on Computer Vision',
                'authors': ['Alice Johnson', 'Bob Wilson'],
                'submission_date': '2024-01-01T10:30:00Z',
                'abstract': 'This is a test abstract for a computer vision paper.',
                'categories': ['cs.CV'],
                'pdf_url': 'https://arxiv.org/pdf/2401.67890.pdf'
            }
        ]
    else:
        print("Fetching papers from arXiv...")
        raw_data = fetch_daily_papers()
        if not raw_data:
            print("Failed to fetch papers. Exiting.")
            return
        papers = parse_papers_data(raw_data)
    
    print(f"Found {len(papers)} papers")
    
    # Organize papers by category
    papers_by_category = {}
    for paper in papers:
        categories = paper.get('categories', [])
        for category in categories:
            if category not in papers_by_category:
                papers_by_category[category] = []
            papers_by_category[category].append(paper)
    
    # Generate pages
    generate_index_page(papers_by_category)
    generate_detail_pages(papers)
    
    print("Site build completed successfully!")

if __name__ == "__main__":
    build_site()