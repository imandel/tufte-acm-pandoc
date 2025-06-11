#!/usr/bin/env python3
"""
Pandoc filter that:
1. Converts citet{key} into "Author [Number]" style citations
2. Extracts ACM conference metadata from LaTeX source and adds margin notes
"""

import panflute as pf
from pybtex.database.input import bibtex
import re
import os

BIB_DATA = {}
CONFERENCE_INFO = {}

def prepare(doc):
    """Prepare bibliography data and extract conference metadata."""
    # Handle bibliography files
    bib_files_meta = doc.get_metadata('bibliography')
    if bib_files_meta:
        # Normalize to list
        if isinstance(bib_files_meta, str):
            bib_files = [bib_files_meta]
        elif isinstance(bib_files_meta, list):
            bib_files = [pf.stringify(item) if not isinstance(item, str) else item for item in bib_files_meta]
        else:
            bib_files = []
        
        # Parse bibliography files
        parser = bibtex.Parser()
        for bib_file in bib_files:
            try:
                bib_data = parser.parse_file(bib_file)
                for key, entry in bib_data.entries.items():
                    BIB_DATA[key] = format_author_name(entry)
            except:
                continue  # Skip problematic files silently
    
    # Extract conference metadata from LaTeX files
    extract_conference_metadata()

def format_author_name(entry):
    """Extract author name from bibliography entry."""
    try:
        # Try author first, then editor
        if 'author' in entry.persons:
            persons = entry.persons['author']
            suffix = ""
        elif 'editor' in entry.persons:
            persons = entry.persons['editor']
            suffix = " (Ed.)"
        else:
            return entry.key
        
        # Format names based on count
        if len(persons) == 1:
            return ' '.join(persons[0].last_names) + suffix
        elif len(persons) == 2:
            first = ' '.join(persons[0].last_names)
            second = ' '.join(persons[1].last_names)
            return f"{first} and {second}" + suffix
        else:
            first = ' '.join(persons[0].last_names)
            return f"{first} et al." + suffix
    except:
        return entry.key

def extract_conference_info_from_text(text):
    """Extract conference information from LaTeX text."""
    if not text:
        return False
    
    found_something = False
    
    # Extract ACM conference information
    match = re.search(r'\\acmConference\[([^\]]+)\]\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}', text)
    if match:
        CONFERENCE_INFO['short_name'] = match.group(1)
        CONFERENCE_INFO['full_name'] = match.group(2)
        CONFERENCE_INFO['dates'] = match.group(3)
        CONFERENCE_INFO['location'] = match.group(4)
        CONFERENCE_INFO['full_citation'] = f"{match.group(2)} ({match.group(1)}), {match.group(3)}, {match.group(4)}"
        found_something = True
    
    # Extract DOI
    doi_match = re.search(r'\\acmDOI\{([^}]+)\}', text)
    if doi_match:
        CONFERENCE_INFO['doi'] = doi_match.group(1)
        found_something = True
    
    # Extract year
    year_match = re.search(r'\\acmYear\{(\d+)\}', text)
    if year_match:
        CONFERENCE_INFO['year'] = year_match.group(1)
        found_something = True
    
    # Extract copyright year
    copyright_year_match = re.search(r'\\copyrightyear\{(\d+)\}', text)
    if copyright_year_match:
        CONFERENCE_INFO['copyright_year'] = copyright_year_match.group(1)
        found_something = True
    
    # Extract book title
    book_title_match = re.search(r'\\acmBooktitle\{([^}]+)\}', text)
    if book_title_match:
        CONFERENCE_INFO['book_title'] = book_title_match.group(1)
        found_something = True
    
    return found_something

def extract_conference_metadata():
    """Extract conference metadata from various sources."""
    # Try to read from main LaTeX file
    for main_file in ['00_main.tex', 'main.tex', 'paper.tex']:
        if os.path.exists(main_file):
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if extract_conference_info_from_text(content):
                        break
            except:
                continue

def transform_elements(elem, doc):
    """Transform citations and extract LaTeX metadata."""
    
    # Handle citation transformation
    if isinstance(elem, pf.Cite) and elem.citations:
        if elem.citations[0].mode == 'AuthorInText':
            author_names = [BIB_DATA.get(cite.id, cite.id) for cite in elem.citations]
            return [pf.Str(" and ".join(author_names)), pf.Space, elem]
    
    # Extract conference info from raw LaTeX blocks/inlines
    elif isinstance(elem, pf.RawBlock) and elem.format == 'latex':
        extract_conference_info_from_text(elem.text)
    elif isinstance(elem, pf.RawInline) and elem.format == 'latex':
        extract_conference_info_from_text(elem.text)
    
    return None

def finalize(doc):
    """Add conference metadata to document after processing."""
    # Set metadata variables that can be used in templates
    if CONFERENCE_INFO.get('full_citation'):
        doc.metadata['conference'] = pf.MetaString(CONFERENCE_INFO['full_citation'])
    elif CONFERENCE_INFO.get('book_title'):
        doc.metadata['conference'] = pf.MetaString(CONFERENCE_INFO['book_title'])
    
    if CONFERENCE_INFO.get('doi'):
        doc.metadata['doi'] = pf.MetaString(CONFERENCE_INFO['doi'])
    
    if CONFERENCE_INFO.get('year'):
        doc.metadata['conference_year'] = pf.MetaString(CONFERENCE_INFO['year'])
    
    # Create conference info margin note if we have information
    if CONFERENCE_INFO:
        margin_content = []
        
        # Add conference citation
        if CONFERENCE_INFO.get('full_citation'):
            margin_content.append(pf.Str(CONFERENCE_INFO['full_citation']))
            margin_content.extend([pf.LineBreak(), pf.LineBreak()])
        elif CONFERENCE_INFO.get('book_title'):
            margin_content.append(pf.Str(CONFERENCE_INFO['book_title']))
            margin_content.extend([pf.LineBreak(), pf.LineBreak()])
        
        # Add DOI
        if CONFERENCE_INFO.get('doi'):
            margin_content.append(pf.Str("DOI: "))
            doi_link = pf.Link(pf.Str(CONFERENCE_INFO['doi']), 
                             url=f"https://doi.org/{CONFERENCE_INFO['doi']}")
            margin_content.append(doi_link)
            margin_content.append(pf.LineBreak())
        
        if margin_content:
            # Create the margin note span
            margin_note = pf.Span(*margin_content, classes=['marginnote'])
            
            # Try to attach to teaserfigure div first
            attached = False
            for i, block in enumerate(doc.content):
                if (isinstance(block, pf.Div) and 
                    hasattr(block, 'classes') and 
                    'teaserfigure' in block.classes):
                    
                    # Find first paragraph in teaser to attach to
                    for j, elem in enumerate(block.content):
                        if isinstance(elem, pf.Para):
                            elem.content.insert(0, margin_note)
                            attached = True
                            break
                    
                    # If no paragraph in teaser, create one
                    if not attached:
                        margin_para = pf.Para(margin_note)
                        block.content.insert(0, margin_para)
                        attached = True
                    break
            
            # Fallback to first paragraph if no teaser found
            if not attached:
                for i, block in enumerate(doc.content):
                    if isinstance(block, pf.Para):
                        block.content.insert(0, margin_note)
                        attached = True
                        break
    
    return doc

def main(doc=None):
    return pf.run_filter(transform_elements, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == '__main__':
    main()