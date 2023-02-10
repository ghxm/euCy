import re

def find_title(doc):

    text = doc.text
    long_lines = re.findall(r'^.*?(?:[A-Za-z]+[ ]+[A-Za-z ,\.]{5,}|ANNEX|Annex).*', text, re.MULTILINE)
    for i, line in enumerate(long_lines):
        if not any([re.search(term, line) is not None for term in [re.compile('Important legal notice', flags=re.IGNORECASE),
                                                                   re.compile('^European Commission$', flags=re.MULTILINE),
                                                                   re.compile('^\|\s*.*?\s*\|$', flags = re.MULTILINE),
                                                                   re.compile('^@', flags=re.MULTILINE),
                                                                   re.compile('EXPLANATORY MEMORANDUM', flags=re.IGNORECASE),
                                                                   re.compile('CONTEXT OF THE PROPOSAL', flags=re.IGNORECASE),
                                                                   re.compile ('Official Journal of the European Union', flags=re.IGNORECASE),
                                                                   re.compile('Avis juridique important', flags=re.IGNORECASE)]]):
            title = line
            if i>1 and 'Proposal for a' in long_lines[i-1]:
                title = long_lines[i-1] + " " + title
            for y in range(i+1, len(long_lines)):
                if re.search('proposal for a', title, flags=re.IGNORECASE) is not None and re.search('proposal for a', long_lines[y], flags=re.IGNORECASE) is not None:
                    # if Proposal for a already in title, break (prevent double title)
                    break
                if len(long_lines) > i and re.search(r'^(?:on|[a-z]+ing|to the)|.*?(?:Proposal|Decision|Directive|Regulation|Report|Communication)',
                                                     long_lines[y], flags=re.MULTILINE|re.IGNORECASE) is not None and re.search(r'\*/$', title.strip(), flags=re.MULTILINE) is None:
                    title = title + " " + long_lines[y]
                else:
                    break
            if len(title) > 30 or any(re.search(term, title, flags=re.IGNORECASE|re.MULTILINE) is not None for term in ['Implementing', 'Decision', 'Regulation', 'Directive', 'Report', '^Annex', 'Communication', 'Recommendation']):
                break

    return title
