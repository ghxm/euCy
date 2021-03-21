"""Dictionaries of expressions used across the package"""

import re

structure = {
    'enacting_start': r'HA[A-Z]+[\s]*ADOPTED[\s]*THIS[\s]*[A-Z]*[:]{0,1}|HA[A-Z]+[\s]*DECIDED[\s]AS[\s][A-Z]+[:]{0,1}|DECIDES\s*AS.*?\s|DECLARE[S]*.*?\s|(?=HEREBY\s*RECOMMEND(?:S))',
    'enacting_start_lenient': r'(?=^\s*H[A-Z]{2,6}?(?<!ING)\b\s+[^a-z]+(?:$|:))',
    'annex_start': r'^(?=\s*^(?=ANNEX|LEGISLATIVE FINANCIAL STATEMENT))|^(?=\s*ANNEX[\s]*(?:[^\n]){0,20}[\n\r]|[\n\r]|\s*[0-9IXV]*))',
    'citations_start': r'(?:^)(?=[A-Z][a-z]+ing|After)',
    'recitals_start_whereas': r'(?=(?:[,\.]|^|^\s*\([0-9]\))\s*Whereas[:]{0,1},*)',
    'recitals_start_having': r'(?=^Having regard to the following.{0,5}$)',
    'article_start': r'(?=^\s*ARTICLE\s*(?:[0-9]|[Oo]ne)[A-Za-z0-9,\- ]{0,200}$|^\s*SOLE\s*ARTICLE\s*$)',
    'article_1_start': r'(?=^\s*ARTICLE\s*(?:1|[Oo]ne)[A-Za-z0-9,\- ]{0,200}$|^\s*SOLE\s*ARTICLE\s*$)',
    'done_at_start': r'^(?=\s*Done[\s]+(?:a[a-z]*\s*|in\s+|\.{2,3}\s+))',
    'toc_start': r'.(?=TABLE[\s]*OF[\s]*CONTENTS|TOC)',
    'toc_start_lenient': r'^(?=[\s*]Contents)',
    'toc_lines': r'(?:^[A-Za-z ]+\s+[0-9IXV]+\s+[^\n]{2,200}$)+?(?=\s+(?:^[A-Za-z ]+\s+[0-9IXV]+\s+[^\n]{2,200}$))',
    'proposal_start': r'^\s*proposal\s*for\s*'
}


elements = {
    'recital': r'(?:(?:(?<=^)\s*\([0-9]{1,3}\s*(?=\)))|(?:(?<=^)\s*[0-9]{1,3}\s*(?=\.))).*',
    'recital_whereas': r'^Whereas[^\:\n]+',
    'citation': structure['citations_start'] +r'(?:.*)',
    'article_identifier': r'^[\s]*[\[\s*]*A[A-za-z]{6}[\s]*[0-9]{1,8}[\s]*[0-9]*[a-z]{0,1}(?:\sbis){0,1}\b(?=[\n]*[0-9]\.|[\n]*\(|[\n]*[A-Z]|[\s]*[A-Z]|[\s]*–|[\s]*-|)(?!\s*of\s|\s*shall\s|\s*is\s|[0-9]*,|[0-9]* and|[0-9]*[\n]{1,}Article|,|[a-z]|[0-9]*\([0-9]{1,3}\)|[ \t]*\([0-9]|[ ]*TFEU|[ ]*of|[ ]*shall)',
    'single_article_identifier': r'(?:^Sole\s*Article|^Single\s*Article)\s*$',
    'article_num': r'Article\s*([0-9 ]+(?:[a-z]\s)*)',
    'article_any_num': r'[0-9 ]+(?:[a-z]\s)*',
    'article_num_element': r'(?:(?<=^)(?:([0-9]\.)|((?:\(){0,1}(?:[a-z]{1,2}|[0-9]+)\))))',
    'article_num_paragraph': r'(?<=^)(?:([0-9]+\.))',
    'article_unnum_paragraph': r'(?<=[A-Za-z0-9 ]{8}).*?(^)[ ]*(?=[A-Z0-9][^\n]{20,})',
    'article_subpar_start': r'(?:^)[ ]*(?=[A-Z0-9][^\n]{10,})',
    'article_point_id': r'(?:^(?:\(){0,1}(?:[a-z]{1,2}|[0-9]+)\))',
    'article_indent_id': r'(?:^[ ]*-)',
    'article_section_titles': r'(?:^[ ]*(?:Section|Chapter|TITLE))'
}

entities = {
        'references': {
        'ref_stopwords': r'$|shall\s|with\s|by\s|will\s|\sany\s|are\s|in\sorder\s|notwithstanding\s|for\s|not\s|until\s|under\s|entry\s*into\s*force\s*of',
        'prefixes': r'(?:of|with|in|to|this)',
        'subpar_elements': r'(?:(?:sub)*paragraph[s]*|point[s]*|sentence[s]*|indent[s]*|section[s]*|parts[s]*)',
        'elements': r'(?:article[s]*|paragraph[s]*|point[s]*|sentence[s]*|indent[s]*|annex[es]*|(?<!other\s)part(?:[^a-z]}|s)|section[s]*|chapter[s]*|title[s]*)',
        'element_nums': r'(?:[0-9IVX \(\)]+(?:[a-z ]\))*(?:(?:[ 0-9\(\)]|[a-z]{0,3}|[ABC])[\s\.]+)*\s*)',
        'separators': r'(?:[,& \s]|(?:and)|(?:or)|(?:to|-)|(?:et\s*seq[\.]*)\s*)',
        'qualifiers': r'(?:(?:of|to)*\s*(?:the|this)\s*(?:present)*)',
        'act_type_prefixes': r'(?:draft)',
        'act_subtype_prefixes': r'(?:Council|Parliament|Cooperation|Commission|Unece|International)',
        'act_types': r'(?:thereof|hereto|TFEU|TEU|Regulation[s]*|Protocol[s]*|Decision[s]*|Directive[s]*|Resolution[s]*|Recommendation[s]*|Treat[yies]+|Protocol[s]*|Convention[s]*|Agreement[s]*|Arrangement[s]*|Report[s]*|Resolution[s]*|Opinion[s]*)',
        'act_identifiers': r'(?:.*?(?:[\n;%]|(?<!\.)\.(?!\.+)|\[[0-9]+\]|$|entry\s*into\s*force\s*of|shall\s|in\sorder\s|because\s|\sany\s|and\s(?=[A-Z]{5,})|and\sin|or\sin|will\s|by\s|with\s|are\s|\sis\s|notwithstanding\s|for\s|not\s|until\s|under\s))',
    },
    'non_references':  [r'This [A-Z]+[a-z]* shall',
                        r'hereinafter\s*referred\s*to\s*as'],
    'split_references': [r'(?<=.{7})(.(?=(?:hereinafter\s*referred\s*to\s*as|annexed\sto|attached\sto|referred\sto\sin)))|(?:(?:and|or|with|under|by)\s|[,\n;\.])(?!\s*this)(?=\s*(?:(?:article[s]*|paragraph[s]*|point[s]*|sentence[s]*|indent[s]*|annex[es]*|(?<!other\s)part(?:[^a-z]}|s)|section[s]*|chapter[s]*|title[s]*)|(?:[^0-9\(\)]*?(?:TFEU|TEU|Regulation[s]*|Decision[s]*|Directive[s]*|Resolution[s]*|Recommendation[s]*|Treat[yies]+|Protocol[s]*|Convention[s]*|Agreement[s]*|Arrangement[s]*|Report[s]*|Resolution[s]*|Opinion[s]*))))']

}

entities['references']['act_types_el'] = re.sub (r'thereof', "(?:(?:(?:of|with|in|under)\\\s)Article|Paragraph|Annex)|thereof", entities['references']['act_types'])
entities['references']['ref_element_acts'] = f'{entities["references"]["elements"]}.{{0,35}}of{entities["references"]["act_identifiers"]}'
entities['references']['ref_elements'] =f'{entities["references"]["elements"]}\s*(?:\s|{entities["references"]["elements"]}|{entities["references"]["separators"]}|{entities["references"]["prefixes"]}|{entities["references"]["element_nums"]})+'
entities['references']['ref_acts'] = f'(?:{entities["references"]["prefixes"]}|{entities["references"]["qualifiers"]})*{entities["references"]["act_type_prefixes"]}*\s*{entities["references"]["act_subtype_prefixes"]}*\s*(?:[a-z0-9-,]+\s+){{0,1}}{entities["references"]["act_types"]}\s*{entities["references"]["act_identifiers"]}'
