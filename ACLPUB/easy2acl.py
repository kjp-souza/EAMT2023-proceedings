#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# easy2acl.py - Convert data from EasyChair for use with ACLPUB
#
# Original Author: Nils Blomqvist
# Forked/modified by: Asad Sayeed
# Further modifications and docs (for 2019 Anthology): Matt Post
# Index for LaTeX book proceedings: Mehdi Ghanimifard and Simon Dobnik
# Recent changes and improvements for EAMT 2020: Fernando Batista
#
# Please see the previous documentation in the README file at http://github.com/acl-org/easy2acl.

import os
import sys
import argparse
import logging
import re

from csv import DictReader
from glob import glob
from shutil import copy
from unicode_tex import unicode_to_tex
from pybtex.database import BibliographyData, Entry
from PyPDF2 import PdfFileReader

def texify(string):
    """Return a modified version of the argument string where non-ASCII symbols have
    been converted into LaTeX escape codes.

    """
    return ' '.join(map(unicode_to_tex, string.split())).replace(r'\textquotesingle', "'")

def read_metadata(fname='meta.txt'):
    metadata = {'chairs': []}
    with open(fname, encoding="utf-8") as metadata_file:
        for line in metadata_file:
            key, value = line.rstrip().split(maxsplit=1)
            if key == 'chairs':
                metadata[key].append(value)
            else:
                metadata[key] = value

    for key in 'abbrev volume_name title short_booktitle booktitle month year location publisher chairs'.split():
        if key not in metadata:
            print('Fatal: missing key "{}" from "meta" file'.format(key))
            sys.exit(1)

    return metadata

def read_papers(fname):
    '''
    Read the file containing the list of accepted papers, in the order they appear in the proceedings.
    Each accepted submission is represented using a dictionary and stored in a list.
    Order in this file is used to determine program order.
    '''
    accepted = []
    with open(fname, encoding="utf-8") as accepted_file:
        for line in accepted_file:
            if (line.strip() == "") or line.startswith("#"):
                pass
            else:
                entry = line.strip().split("\t")
                sid = entry[0]
                info = {"id": sid, "title": entry[2], "authors": entry[1].replace(' and', ',').split(', ') }
                if len(entry) == 4:
                    info["page"] = int(entry[3])
                accepted.append(info)
        logging.info("Found {} accepted files".format(len(accepted)))
    return accepted

def read_abstracts(fname, papers):
    '''Read abstracts'''
    known_titles = {p["title"]:p["id"] for p in papers}

    paper_info = re.compile(r'<div class="paper">.*?<span class="authors">(.*?)</span>\n<span class="title">(.*?)</span></div>\n<div class="abstract">(.*?)</div>', re.S)

    abstracts = {}
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            lines = "".join(f.readlines())
            for paper in paper_info.findall(lines):
                title = paper[1].strip()
                title = re.sub(r"&amp;", "\&", title)
                if title in known_titles:
                    logging.debug("This is paper: {}".format(known_titles[title]))
                    abstracts[known_titles[title]] = paper[2].strip()
                else:
                    logging.warning("Paper not found: {}".format(title))
                    sys.exit(1)
        logging.info("Found {} abstracts".format(len(abstracts)))
    else:
        logging.info('No abstracts available.')

    return abstracts


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description="Creates ACLPUB Proceedings based on EasyChair data", epilog="v1.0")
    PARSER.add_argument("-debug", action='store_true', default=False, help="Turns on debug information")
    PARSER.add_argument("-meta", dest="meta", default="info/meta.txt", help="meta file")
    PARSER.add_argument("-papers", dest="papers", default="info/papers.tsv", help="List of accepted papers. Format: PaperID\ttitle\tauthors\tpage(optional)")
    PARSER.add_argument("-abstracts", dest="abstracts", default="info/abstracts.html", help="File containing the abstracts (optional)")
    args = PARSER.parse_args()

    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    metadata = read_metadata(args.meta)
    papers = read_papers(args.papers)
    abstracts = read_abstracts(args.abstracts, papers)

    venue = metadata["abbrev"]
    volume_name = metadata["volume_name"]
    year = metadata["year"]

    #
    # Find all relevant PDFs
    #

    # The PDF of the full proceedings
    logging.info("VENUE: {} {} pdf/{}_{}.pdf".format(venue, year, venue, year))
    full_pdf_file = 'pdf/{}_{}.pdf'.format(venue, year)
    if not os.path.exists(full_pdf_file):
        logging.error("Fatal: could not find full volume PDF '{}'".format(full_pdf_file))
        sys.exit(1)

    # The PDF of the frontmatter
    frontmatter_pdf_file = 'pdf/{}_{}_frontmatter.pdf'.format(venue, year)
    if not os.path.exists(frontmatter_pdf_file):
        logging.error("Fatal: could not find frontmatter PDF file '{}'".format(frontmatter_pdf_file))
        sys.exit(1)

    # File locations of all PDFs (seeded with PDF for frontmatter)
    pdfs = {'0': frontmatter_pdf_file }
    for pdf_file in glob('pdf/{}_{}_paper_*.pdf'.format(venue, year)):
        sid = pdf_file.split('_')[-1].replace('.pdf', '')
        pdfs[sid] = pdf_file

    # List of accepted papers (seeded with frontmatter)
    papers.insert(0, {"id": "0", "title": metadata['booktitle'], "authors": metadata['chairs']})

    #
    # Create Anthology tarball
    #

    # Create destination directories
    for dir in ['bib', 'pdf']:
        dest_dir = os.path.join('proceedings/cdrom', dir)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

    # Copy over "meta" file
    logging.info('COPYING meta -> proceedings/meta')
    copy(args.meta, 'proceedings/meta')

    final_bibs = []
    start_page = 1
    for paper_id, entry in enumerate(papers):
        sid, paper_title = entry["id"], entry["title"]
        authors = ' and '.join (entry["authors"])
        if "page" in entry:
            if start_page != entry["page"]:
                logging.info("Initial page changed for paper {}: {} -> {}".format(paper_id, start_page, entry["page"]))
                start_page = entry["page"]

        if not sid in pdfs:
            logging.error('Fatal: no PDF found for paper {}, ID={}'.format(paper_id, sid))
            sys.exit(1)

        pdf_path = pdfs[sid]
        dest_path = 'proceedings/cdrom/pdf/{}.{}-{}.{}.pdf'.format(year, venue, volume_name, paper_id)

        copy(pdf_path, dest_path)
        logging.info('COPYING {} -> {}'.format(pdf_path, dest_path))

        bib_path = dest_path.replace('pdf', 'bib')
        if not os.path.exists(os.path.dirname(bib_path)):
            os.makedirs(os.path.dirname(bib_path))

        anthology_id = os.path.basename(dest_path).replace('.pdf', '')

        bib_type = 'proceedings' if sid == '0' else 'inproceedings'
        bib_entry = Entry(bib_type, [
            ('author', texify(authors)),
            ('title', paper_title),
            ('year', metadata['year']),
            ('month', metadata['month']),
            ('address', metadata['location']),
            ('publisher', metadata['publisher']),
        ])

        # Add page range if not frontmatter
        if paper_id > 0:
            with open(pdf_path, 'rb') as in_:
                file = PdfFileReader(in_)
                last_page = start_page + file.getNumPages() - 1
                bib_entry.fields['pages'] = '{}--{}'.format(start_page, last_page)
                start_page = last_page + 1

        # Add the abstract if present
        if sid in abstracts:
            bib_entry.fields['abstract'] = abstracts.get(sid)

        # Add booktitle for non-proceedings entries
        if bib_type == 'inproceedings':
            bib_entry.fields['booktitle'] = metadata['booktitle']

        try:
            bib_string = BibliographyData({ anthology_id: bib_entry }).to_string('bibtex')
        except TypeError as e:
            logging.error('Fatal: Error in BibTeX-encoding paper {}'.format(sid))
            sys.exit(1)
        final_bibs.append(bib_string)
        with open(bib_path, 'w', encoding="utf-8") as out_bib:
            print(bib_string, file=out_bib)
            logging.info('CREATED {}'. format(bib_path))

    # Create an index for LaTeX book proceedings
    if not os.path.exists('book-proceedings'):
        os.makedirs('book-proceedings')

    with open('book-proceedings/all_papers.tex', 'w', encoding="utf-8") as book_file:
        for entry in papers:
            sid = entry["id"]
            paper_title = entry["title"]
            authors = entry["authors"]
            if sid == "0":
                continue
            if len(authors) > 1:
                authors = ', '.join(authors[:-1]) + ' and ' + authors[-1]
            else:
                authors = authors[0]

            print("""\goodpaper{{../{pdf_file}}}{{{title}}}%
    {{{authors}}}\n""".format(authors=texify(authors), pdf_file=pdfs[sid], title=texify(paper_title)), file=book_file)


    # Write the volume-level bib with all the entries
    dest_bib = 'proceedings/cdrom/{}-{}.bib'.format(venue, year)
    with open(dest_bib, 'w', encoding="utf-8") as whole_bib:
        print('\n'.join(final_bibs), file=whole_bib)
        logging.info('CREATED {}'.format(dest_bib))

    # Copy over the volume-level PDF
    dest_pdf = dest_bib.replace('bib', 'pdf')
    logging.info('COPYING {} -> {}'.format(full_pdf_file, dest_pdf))
    copy(full_pdf_file, dest_pdf)
