"""Dictionaries of expressions used across the package"""

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
    'article_identifier': r'^[\s]*[\[\s*]*A[A-za-z]{6}[\s]*[0-9]{1,8}[\s]*[0-9]*\b(?=[\n]*[0-9]\.|[\n]*\(|[\n]*[A-Z]|[\s]*[A-Z]|[\s]*–|[\s]*-|)(?!\s*of\s|\s*shall\s|\s*is\s|[0-9]*,|[0-9]* and|[0-9]*[\n]{1,}Article|,|[a-z]|[0-9]*\([0-9]{1,3}\)|[ \t]*\([0-9]|[ ]*TFEU|[ ]*of|[ ]*shall)',
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
