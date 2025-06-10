#!/usr/bin/env python3
"""
Pandoc filter that converts \citet{key} into "Author [Number]" style citations.
"""

import panflute as pf
from pybtex.database.input import bibtex

BIB_DATA = {}

def prepare(doc):
    bib_files_meta = doc.get_metadata('bibliography')
    if not bib_files_meta:
        return
    
    # Normalize to list
    if isinstance(bib_files_meta, str):
        bib_files = [bib_files_meta]
    elif isinstance(bib_files_meta, list):
        bib_files = [pf.stringify(item) if not isinstance(item, str) else item for item in bib_files_meta]
    else:
        return
    
    # Parse bibliography files
    parser = bibtex.Parser()
    for bib_file in bib_files:
        try:
            bib_data = parser.parse_file(bib_file)
            for key, entry in bib_data.entries.items():
                BIB_DATA[key] = format_author_name(entry)
        except:
            continue  # Skip problematic files silently

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

def transform_elements(elem, doc):
    """Transform \citet citations to author name format."""
    if isinstance(elem, pf.Cite) and elem.citations:
        if elem.citations[0].mode == 'AuthorInText':
            author_names = [BIB_DATA.get(cite.id, cite.id) for cite in elem.citations]
            return [pf.Str(" and ".join(author_names)), pf.Space, elem]
    return None

def main(doc=None):
    return pf.run_filter(transform_elements, prepare=prepare, doc=doc)