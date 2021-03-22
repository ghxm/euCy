from euplexcy import utils
from euplexcy import regex as euplexre
from spacy.tokens import Doc
from spacy.tokens.span import Span
from spacy.tokens.token import Token
from euplexcy import structure, elements
import warnings
import re
import itertools



class ReferenceMatcher:

    """Custom matcher for references."""

    def __init__(self, label = "REFERENCE"):

        if not Span.has_extension("references"):
            Span.set_extension("references", default = None)

        if not Doc.has_extension("parts"):
            self.EuplexStructure = structure.Structure()
        if not Doc.has_extension("article_elements"):
            self.EuplexElements = elements.Elements()

        self.label = label


    def __call__(self, doc):

        # check if doc has parts groups and article elements custom attributes
        # or check in function?
        # maybe check here and restrict function to detection only?

        # article for article in match_Ref
        if not Span.has_extension("element_type") or doc.spans.get('articles', None) is None:
            doc = self.EuplexStructure (doc)
        if not Doc.has_extension("article_elements") or doc._.article_elements is None:
            doc = self.EuplexElements(doc)

        matches = []

        # @TODO: add option to matcher to either match on article or on subpar basis

        for art in doc._.article_elements:
            for i, par in enumerate(art['pars']):
                for subpar in art['subpars'][i]: # pass subpars to reference matching
                    matches.extend(reference_spans(subpar, label = self.label)) # extend the list by the list of matches (entities) in the article)
        return matches

        # @TODO return matches as Spans with label = "REFERENCE", and extension ._. for further details, such as the references contained in the Span as a list (to account for Article 1-5 bc spacy does not allow overlapping labels)



def _has_element_num(text):
    words = text.split()
    words = [w for w in words if re.search(euplexre.entities['references']['elements'], w) is None]
    text = " ".join(words)
    if re.search(r'[0-9]|[XVI]{1,3}(?![a-z])|(?:^|\s)\([a-z]{1,2}\)(?:\.| |$)|^[IVX]+$', text.strip()) is not None:
        return True
    else:
        return False

def _elements(text):
    elements_list =  [m for m in re.findall ('[a-z]*' + euplexre.entities['references']['elements'] + '[a-z]*', text, flags=re.MULTILINE|re.IGNORECASE)]
    return([e for e in elements_list if re.search('^' + euplexre.entities['references']['elements'] + '$', e, flags=re.MULTILINE|re.IGNORECASE) is not None])


def _has_element(text):
    if len(_elements(text))>0:
        return True
    else:
        return False

def _has_cap_element(text):

    """Internal function to check whether the given text has a capitalized or upper case element name"""

    if any([e.istitle() for e in _elements(text)]):
        return True
    else:
        return False

def _has_subpar_element(text):
    if re.search(euplexre.entities['references']['subpar_elements'], text, flags=re.IGNORECASE) is not None:
        return True
    else:
        return False

def _has_subpar_element_num (token):
    if isinstance(token, Token):
        if token.like_num:
            return True
        text = token.text

    if re.search(euplexre.entities['references']['element_nums'], text) is not None:
        return True
    else:
        return False


def _acts(text):
    acts_list = [m for m  in re.findall ('[a-z]*' + euplexre.entities['references']['act_types'] + '[a-z]*', text, flags=re.MULTILINE|re.IGNORECASE)]
    return [a for a in acts_list if re.search('^' + euplexre.entities['references']['act_types'] + '$', a, flags=re.MULTILINE|re.IGNORECASE) is not None]

def _has_act(text):
    if len (_acts (text)) > 0:
        return True
    else:
        return False

def _has_act_identifier(text): # check whether text contains an act identifier
    words = text.split()
    words = [w for w in words if re.search(euplexre.entities['references']['act_types'], w) is None]
    text = " ".join(words)
    if re.search(r'\([A-Z]{2,}\)|of\s*the|to\s*the|[0-9]|\/|between\sthe|International', text) is not None:
        return True
    else:
        return False

def _is_act_identifier(text): # check whether word in part of an act identifier
    if _has_act_identifier(text):
        return True
    else:
        if re.search(r'No|\([a-z]+\)|[\.]{2,}', text, flags=re.IGNORECASE) is not None:
            return True
        else:
            False

def _has_cap_act(text):
    if any ([a.istitle () if re.search(r'thereof|hereto', a) is None else True for a in _acts (text) ]):
        return True
    else:
        return False

def  _has_separator(text):
    if re.search(r'[,;]|and|or', text) is not None:
        return True
    else:
        False

def _is_not_act(token): # function to inspect tokens that look like acts, but may not be actual references

    context_l = "".join([t.text_with_ws for t in utils.get_n_left(6, token, ignore_ws = True)])
    # context_r = "".join([t.text_with_ws for t in utils.get_n_right(5, token, ignore_ws = True)])

    if re.search(r'entry\s*into\s*force\s*of\s*this', context_l, flags=re.IGNORECASE) is not None:
        return True
    if re.search(r'(?:an|a|any)\s+', context_l, flags=re.IGNORECASE) is not None and re.search(r'(?:the|this)\s+', context_l, flags=re.IGNORECASE) is None:
        return True
    if not token.text.istitle():
        return True
    if token.text.isupper() and re.search(r'SECTION|PART|TITLE', falgs=re.IGNORECASE) is not None:
        return True

    return False


def _has_range_indicator(token_text):

    if re.search(r'to|-|et *seq[\.]*', token_text, flags=re.IGNORECASE) is not None:
        return True
    else:
        return False

def _has_qualifier(text):
    if re.search(euplexre.entities['references']['qualifiers'], text) is not None:
        return True
    else:
        return False


# resolve ranges
def _resolve_range(text):
    # identify range in text
    range_match = re.search (r'(?:\(*([0-9]+(?:[a-z]{0,1})|[a-z]|[IXV])\)*)\s*(?:to|-)\s*(?:\(*([0-9]+(?:[a-z]{0,1})|[a-z]|[IXV])\)*)', text)
    if range_match is not None:
        lower = range_match.group (1)
        upper = range_match.group (2)
    else:
        [text]


    try:
        input = "num"
        lower = int (lower)
        upper = int (upper)
    except:
        try:
            if re.search (r'[IVX]', lower.upper ()) is not None and re.search (r'[IVX]', upper.upper ()) is not None:
                try:
                    input = "roman"
                    lower = utils.roman_to_int (lower.upper ())
                    upper = utils.roman_to_int (upper.upper ())
                except:
                    return [text]
            elif re.search (r'[a-z]', lower.lower ()) is not None and re.search (r'[a-z]', upper.lower ()) is not None:

                try:
                    input = "letter"
                    if len (lower) > 1:
                        lower = lower[-1]
                    if len (upper) > 1:
                        upper = upper[-1]
                    lower = utils.letter_to_int (lower.lower())
                    upper = utils.letter_to_int (upper.lower())
                except:
                    return [text]
        except:
            return [text]

    try:
        range_nums = [i for i in range (lower, upper + 1)]
    except:
        return [text]


    if input == "num":
        return [str(num) for num in range_nums]
    elif input == "roman":
        return [utils.int_to_roman (num) for num in range_nums]
    elif input == "letter":
        return [utils.int_to_letter (num) for num in range_nums]


def match_reference_text(span, match_on = "all"):
    # return a list of reference-like text regex match elements for a given text (text, pos, sentence/line)

    if match_on == "sentences":
        sentences = utils.get_sentences (span, min_sen_length=10)
    elif match_on == "all":
        sentences = [span]

    ref_match_list = []

    def add_to_match_list(match, sentence, type):
        ref_match_list.append (
            {'match': match.group (0),
             'type': type,
             'start': sentence.start_char + match.start (),
             'end': sentence.start_char + match.end (),
             'sentence': match.string,
             'string_start': match.start (),
             'string_end': match.end ()}
        )

    for sentence in sentences:
        # 1 Capture all element .... of ... act/act_el
        matches_element_act = re.finditer (euplexre.entities['references']['ref_element_acts'], sentence.text, flags=re.IGNORECASE|re.MULTILINE)
        [add_to_match_list (match, sentence, type="element_act") for match in matches_element_act]

        # 2 Capture all element .*
        matches_element = re.finditer (euplexre.entities['references']['ref_elements'], sentence.text, flags=re.IGNORECASE|re.MULTILINE)
        [add_to_match_list (match, sentence, type="element") for match in matches_element]

        # 3 Capture all acts
        matches_act = re.finditer (euplexre.entities['references']['ref_acts'], sentence.text, flags=re.IGNORECASE|re.MULTILINE)
        [add_to_match_list (match, sentence, type="act") for match in matches_act]

    return ref_match_list


def reference_spans(doclike, label = "REFERENCE", match_on = "all"):

    """Wrapper for the whole process of identifying references, taking a doc or span object and returning a set of spans with the referneces contained in the span listed in the ._.references extension = [{ref1}, {ref2}]"""

    def range_intersect(r1, r2):
        return range (max (r1.start, r2.start), min (r1.stop, r2.stop)) or None

    def _combine_overlapping_matches(match_list):

        combined_list_1 = []
        combined_list_2 = []

        def add_matches(ma1,ma2):

            ma_a = None

            # if 2 is contained in 1
            if ma1['string_start'] <= ma2['string_start'] and ma1['string_end'] >= ma2['string_end']:
                if (ma1['type'] == "element_act" and (ma2['type'] == "element")) or (ma1['type'] == "act" and (ma2['type'] == "element")): # if element is contained in element_act or element is contained in act (rely onn splitting later on to differentiate both)
                    ma_a = ma1
            # if 1 is contained in two
            if ma2['string_start'] <= ma1['string_start'] and ma2['string_end'] >= ma1['string_end']:
                if (ma2['type'] == "element_act" and (ma1['type'] == "element")) or (ma2['type'] == "act" and (ma1['type'] == "element")):
                    ma_a = ma2

            if ma_a is None:
                ma_a = {
                    'type': ma1['type'],
                    'start': ma1['start'],
                    'end': ma2['end'],
                    'string_start': ma1['string_start'],
                    'string_end': ma2['string_end'],
                    'sentence': ma1['sentence'],
                    'match': ma1['sentence'][ma1['string_start']:ma2['string_end']]
                }

            return(ma_a)

        matches_type_1 = [m for m in match_list if m['type'] == "element_act"]
        matches_type_o = [ma for ma in match_list if ma['type'] != "element_act"]

        for m1 in matches_type_1: # 2 and 3 into 1
            for mo in list(matches_type_o):
                m1_range = range (m1['string_start'], m1['string_end'])
                if m1['sentence']==mo['sentence']:
                    mo_range = range(mo['string_start'], mo['string_end'])
                    if range_intersect(m1_range, mo_range) is not None or (m1_range.stop == mo_range.start):
                        m1 = add_matches(m1, mo)
                        matches_type_o.remove(mo)
                    #else:
                    #    combined_list_1.append(mo)

            combined_list_1.append(m1)

        # add remaining matches of types 2 and 3 again
        combined_list_1 = combined_list_1 + matches_type_o

        # 3 into 2
        matches_type_1 = [ma for ma in combined_list_1 if ma['type'] == "element_act"]
        matches_type_2 = [ma for ma in combined_list_1 if ma['type'] == "element"]
        matches_type_3 = [ma for ma in combined_list_1 if ma['type'] == "act"]

        for m2 in matches_type_2:
            for m3 in list(matches_type_3):
                m2_range = range (m2['string_start'], m2['string_end'])
                if m2['sentence']==m3['sentence']:
                    m3_range = range(m3['string_start'], m3['string_end'])
                    if range_intersect(m2_range, m3_range) is not None:
                        m2 = add_matches(m2, m3)
                        matches_type_3.remove(m3)


            combined_list_2.append(m2)

        # add remaining type 3 matches again
        combined_list_2 = matches_type_1 + combined_list_2 + matches_type_3

        return(combined_list_2)

    def _process_match(match):

        def split_match(match):
            """Split a match into references in case of multiple references per match
            e.g. paragraph 1, the manufacturer or importer shall notify the Agency of the following information in the format specified by the Agency in accordance with Article 108: may be one match
            return list of split matches (match dicts)
            """

            def _split_match_dict(match, pos = []):

                """Split a match dictionary according to  a list of (start, end) tuples and return a matching number of match dictionariess"""

                match_splits = [] # list of reference matches within match
                match_pos = [] # list of reference match start and end position (filled from pos list below)

                if len (pos) > 0:

                    for i, p in enumerate(pos):
                        if i==0: # if first match, set start pos to 0, to matcb strin gup to first pos
                            match_start = 0
                        else:
                            match_start = pos[i-1][1] # the end of the prev match
                        match_end = p[0]

                        match_pos.append((match_start, match_end))

                        # add match for part after last ref match pos (end of match string)
                        if i == len(pos)-1:
                            match_pos.append((p[1], p[1]  + len(match['match'])))

                    # additional

                    for s in match_pos:
                        match_splits.append ({
                            'type': None,
                            'start': match['start'], # i of first spacy token of sentence
                            'end': match['end'], # i of last spacy token of sentence
                            'string_start': match['string_start'] + s[0],  # i of first char of match within the sentence string
                            'string_end': match['string_start'] + s[1], # i of last char of match within the sentence string
                            'sentence': match['sentence'],
                            'match': match['match'][s[0]:s[1]]
                        })

                else:
                    match_splits.append (match)

                return match_splits

            # split any ref stop word (anything thats not an element/act or a number) + element/act
            new_ref_pos = [(m.start(), m.end()) for reg in euplexre.entities['split_references'] for m in re.finditer(reg, match['match'], flags=re.IGNORECASE|re.MULTILINE) ]

            match_splits = _split_match_dict(match, new_ref_pos)

            return match_splits

        cleaned_matches = []

        # @TODO first split and if, call process matches again for all parts bzw loop over?
        ## e.g. paragraph 1, the manufacturer or importer shall notify the Agency of the following information in the format specified by the Agency in accordance with Article 108: may be one match
        # and ACT/ELEMENT
        # or ACT/AELEMENT
        # , ACT/ELEMENT
        # . ACT/ELEMENT
        # .........


        split_matches = split_match(match)

        for submatch in split_matches:

            if len(submatch['match'].strip())==0: #  sort out empty matches
                continue

            submatch_span = doclike[utils.char_to_token (submatch['string_start'], doclike_char_token):utils.char_to_token (submatch['string_end'], doclike_char_token, alignment_mode="expand")]

            if submatch_span.text.strip() != submatch['match'].strip():
                submatch_span_aligned = utils.align_span_with_text(submatch_span, submatch['match'], right = True, left = False)


                if submatch_span_aligned is not None:
                    # check for some common fallacies, if passes, assign aligned span as new submatch_span
                    if len(submatch_span_aligned.text.strip()) - len(submatch['match'].strip()) < -1:
                        pass
                    elif len(submatch_span_aligned.text.strip()) > len(submatch_span.text.strip()):
                        pass
                    else:
                        submatch_span = submatch_span_aligned


            match_token_text = submatch_span.text


            if not _has_element(match_token_text) and not _has_act(match_token_text):
                continue

            # rule out any non-references via regex dict
            if any([re.search(p, match_token_text, flags=re.IGNORECASE) is not None for p in euplexre.entities['non_references']]):
                continue
            # if no element and only act and act is Article
            if re.search(euplexre.entities['references']['elements'], match_token_text, flags=re.IGNORECASE) is None and re.search(euplexre.entities['references']['act_types'], match_token_text, flags=re.IGNORECASE) is None:
                continue

            # if reference is merely self ref to whole act (list re.findall construction is necessary bc regex matches whitespace)
            if not _has_element_num(match_token_text) and re.search(r'(?:this|present)\s+[A-Z]+[a-z]*', match_token_text, flags=re.MULTILINE) is not None:
                continue

            # Element only without num (e.g. of Articles, of an Article, this Article, this Title etc)
            if _has_element(match_token_text) and not _has_element_num(match_token_text):
                if re.search(r'annex', match_token_text, flags=re.IGNORECASE) is None:
                    continue

            # Act without capitalization (e.g. "unanimous agreement")
            if _has_act(match_token_text) and not _has_cap_act(match_token_text):
                continue

            # for acts/elements only check for this before (use n left)
            if _has_act(match_token_text) and not _has_element(match_token_text):

                act_match = re.search(euplexre.entities['references']['act_types'], match_token_text.strip(), flags=re.MULTILINE | re.IGNORECASE)



                if act_match is not None:
                    act_match_token = submatch_span[utils.char_to_token(act_match.start()+1, submatch_span)]

                    act_match_token_text = act_match_token.text

                    if len(act_match_token_text.strip()) < 3:
                        act_match_token_text = act_match.group(0).strip()

                    if act_match.start() < 3:
                        # get n 2 lef tokens and check
                        prefix = [t.text.lower() for t in utils.get_n_left(3, act_match_token)]
                        suffix = [t.text.lower() for t in utils.get_n_right(3, act_match_token)]
                    else:
                        # get string until act match
                        prefix = submatch['sentence'][submatch['string_start']+act_match.start()-12:submatch['string_start']+act_match.start()].lower()
                        suffix = submatch['sentence'][submatch['string_start']+act_match.end():submatch['string_start']+act_match.end()+15].lower()

                    # check if plural
                    if act_match_token_text.strip().lower().endswith('s') and not _has_act_identifier(match_token_text) and 'the' not in prefix:
                        continue


                    # check prefix for 'this'
                    if "this" in prefix:
                        continue
                    if " a " in prefix:
                        continue
                    # check if act is 'quoted'
                    if any([True for fix in list(prefix) if re.search(r"[‘’\']", fix)]) and [True for fix in list(suffix) if re.search(r"[‘’\']", fix)]:
                        continue
                    # check for 'the text of the Agreement is attache to this decision'
                    if 'text' in prefix:
                        continue
                    # @TODO (see issues notes) what about the Regulation if defined before
                else:
                    continue

            submatch['submatch_span'] = submatch_span

            cleaned_matches.append(submatch)


        return cleaned_matches


    doclike_char_token = utils.chars_to_tokens_dict (doclike, input="as_ref", output="as_ref")

    # first, match the possible references in the text

    match_list = match_reference_text(doclike, match_on="all")

    # then, combine overlapping candidates
    match_list_c = _combine_overlapping_matches(match_list)

    # the loop over candidates and try to parse references
    # if references in match, add to the entity match list
    ents_list = [] # list of entity spans that is returned

    for matc in match_list_c:

        #mat_refs = _parse_refs(mat) # this shall return references from a match dict
        #if mat_refs is not None and len(mat_refs > 0):
        # safety checks
        processed_matches = _process_match(matc)
        for mat in processed_matches:
            mat_span = mat['submatch_span']
            ents_list.append((label,mat_span.start, mat_span.end))
    return(ents_list)


def resolve_reference_entities(entity):  # or count?
    """Identify and label the references contianed in a ref entity
    return list of references (as dictionaries) contained in a match/string
    # @TODO: hier weiter
    """

    reference_list = []

    def _add_reference(subpar_element, subpar_element_num, element, element_num, act, act_id, type = None, relation = None):

        # @TODO if type None, determine

        # if relation None, determine
        # if hereto in act -> int
        if relation is None:

            relation = "external"

            # if this -> int
            if act is not None:
                if re.search(f'^\s*this\s*{euplexre.entities["references"]["act_type_prefixes"]}*\s*{euplexre.entities["references"]["act_subtype_prefixes"]}*\s*(?:[a-z0-9-,]+\s+){{0,1}}{euplexre.entities["references"]["act_types"]}',
                             act, flags=re.MULTILINE) is not None:
                    relation = "internal"

            # if len (act) == 0 -> int
            else:
                relation = "internal"

        reference_list.append({
            'type': type,
            'relation': relation,
            'subpar_element': subpar_element,
            'subpar_element_num': subpar_element_num,
            'element': element,
            'element_num': element_num,
            'act': act,
            'act_id': act_id,
        })

    entity_parts = {'prefix': [],
                    'subpar_element': [],
                    'subpar_element_num': [],
                    'element': [],
                    'element_num': [],
                    'act': [],
                    'act_id': [],
                    'suffix': [],
                    'other': []}
    last_token = None
    last_token_sep = False
    append_next_token_to = None
    append_this = False


    for token in entity:

        if token.is_space:
            continue
        if append_next_token_to is not None:
            if _has_element_num(token.text) or _has_act_identifier(token.text):
                entity_parts[append_next_token_to][-1] += token.text_with_ws
                append_next_token_to = None
                continue
            elif re.search('^in$', token.text, flags = re.MULTILINE) is not None: # if filler between separator, try next token
                continue
            else:
                append_next_token_to = None

        # check if 'this'
        if token.text.lower() == 'this':
            append_this = True
            continue

        # CHECK FOR (SUBPAR) ELEMENTS and ACTS
        # check for (sub)paragraoh level elements
        if _has_subpar_element(token.text):
            if append_this and len(entity_parts['subpar_element']) == 0:
                entity_parts['subpar_element'].append ('this ' + token.text_with_ws)
                append_this = False
            else:
                append_this = False
                entity_parts['subpar_element'].append (token.text_with_ws)

            last_token = "subpar_element"
            continue
        # check if element
        elif _has_element(token.text):
            if append_this and len(entity_parts['element']) == 0:
                entity_parts['element'].append('this ' + token.text_with_ws)
                append_this = False
            else:
                append_this = False
                entity_parts['element'].append (token.text_with_ws)

            last_token = "element"
            continue
        # check if act
        elif _has_act(token.text) and not _is_not_act(token):
            if append_this and len(entity_parts['act']) == 0:
                entity_parts['act'].append ('this ' + token.text_with_ws)
                append_this = False
            else:
                append_this = False
                entity_parts['act'].append(token.text_with_ws)
            last_token = "act"
            continue

        append_this = False


        # CHECK FOR IDENTIFIERS/NUMS
        if last_token == "subpar_element":
            # check if numlike or has element tim
            if _has_qualifier (token.text):  # check for qualifier ('of')
                continue
            if _has_subpar_element_num (token):
                if not last_token_sep:
                    entity_parts['subpar_element_num'].append (token.text_with_ws)
                else:
                    entity_parts['subpar_element_num'].append (token.text_with_ws)
                    last_token_sep = False

                last_token = "subpar_element_num"
                continue
        elif last_token == "element":
            # check if numlike or has element tim
            if _has_element_num(token.text):
                if not last_token_sep:
                    entity_parts['element_num'].append(token.text_with_ws)

                else:
                    entity_parts['element_num'].append(token.text_with_ws)
                    last_token_sep = False

                last_token = "element_num"
                continue
            elif 'annex' in entity_parts['element'][-1].lower() and not _has_element_num(token.text): # annex does not need num
                entity_parts['element_num'].append("")
                last_token = "element_num"
                continue
        elif last_token == "act":
            if _is_act_identifier (token.text):
                if not last_token_sep:
                    entity_parts['act_id'].append(token.text_with_ws)
                else:
                    entity_parts['act_id'].append (token.text_with_ws)
                    last_token_sep = False
                last_token = "act_id"
                continue
        # append to previous subpar_element_num, element_num or act_id depending on last_token
        elif last_token == "element_num" or last_token == "act_id" or last_token ==  "subpar_element_num":
            if _has_separator(token.text):
                last_token_sep = True
                continue
            elif _has_qualifier(token.text): # check for qualifier ('of')
                continue

            if last_token  == "act_id":
                if _is_act_identifier (token.text):
                    if not last_token_sep:
                        entity_parts['act_id'][-1]  += token.text_with_ws
                    else:
                        entity_parts['act_id'].append (token.text_with_ws)
                        last_token_sep = False
                    last_token = "act_id"
                    continue
            elif last_token == "subpar_element_num":
                if 'annex' not in entity_parts.get('subpar_element', [" "])[-1].lower() and _has_range_indicator (token.text):
                    entity_parts['subpar_element_num'][-1] += " " + token.text + " "
                    last_token = "subpar_element_num"
                    append_next_token_to = "subpar_element_num"  # overwrite any other logic and append
                    continue
                if _has_subpar_element_num (token):
                    if not last_token_sep:
                        entity_parts['subpar_element_num'][-1] += (token.text_with_ws)
                    else:
                        entity_parts['subpar_element_num'].append (token.text_with_ws)
                        last_token_sep = False
                    last_token = "subpar_element_num"
                    continue
            elif last_token == "element_num":
                if 'annex' not in entity_parts.get('element', [" "])[-1].lower() and _has_range_indicator (token.text):
                    entity_parts['element_num'][-1] += " " + token.text + " "
                    last_token = "element_num"
                    append_next_token_to = "element_num"  # overwrite any other logic and append
                    continue
                if _has_element_num (token.text):
                    if not last_token_sep:
                        entity_parts['element_num'][-1] += (token.text_with_ws)
                    else:
                        entity_parts['element_num'].append (token.text_with_ws)
                        last_token_sep = False
                    last_token = "element_num"
                    continue

        # HANDLE NON-MATCHING TOKENS
        # append to last token
        if last_token is None or last_token == "prefix":
            entity_parts['prefix'].append(" " + token.text_with_ws)
            last_token = 'prefix'
        elif last_token == "element_num" or last_token ==  "act_id" or last_token == "subpar_element_num" or last_token == "subpar_element":
            entity_parts['suffix'].append (token.text_with_ws)
            last_token = 'suffix'
        elif last_token is not None:
            if last_token == 'suffix':
                entity_parts['suffix'].append (token.text_with_ws)
                last_token = 'suffix'
            elif not last_token_sep:
                entity_parts[last_token][-1] += token.text_with_ws
            else:
                entity_parts["other"].append(token.text_with_ws)
                last_token_sep = False
                last_token = "other"

    if len(entity_parts['act_id'])>1:
        # check for valid act ids
        entity_parts['act_id'] = [id for id in entity_parts['act_id'] if id.lower().strip() != "no"]

    for e in entity_parts['element_num']:
        # @TODO check for valid element nums
        pass

    for s in entity_parts['subpar_element_num']:
        # @TODO check for valid element num
        pass


    # if all parts empty except for one, e.g. Element or Act, check for n left (e.g. acts: a/an -> no ref, the (draft) (Commssion) (something) -> ref) and n right (?)
    ## if only 'this Regulation' -> discard
    ## if only thereof in any element/act ->  discard

    # FILTER OUT NON-REFERENCES
    # sort out any subpar_element, element without nums
    if all([len(entity_parts[key])==0 for key in ['element', 'act', 'act_id', 'subpar_element_num', 'subpar_element']]):
        entity_parts['element_num'] = []
    if all([len(entity_parts[key])==0 for key in ['element', 'element_num', 'act', 'act_id', 'subpar_element_num']]):
        entity_parts['subpar_element_num'] = []
    if any(['thereof' in act.lower() for act in entity_parts['act']]) and all([len(entity_parts[key])==0 for key in ['element', 'element_num', 'subpar_element', 'subpar_element_num']]):

        entity_parts['act'] = [act for act in entity_parts['act'] if not 'thereof' in act.lower() and not 'this' in act.lower()]
        if len(entity_parts['act']) == 0:
            entity_parts['act_id'] = []

    # @TODO see notes for reference rules



    # make sure subpar_element_num level is reduced to one except if range or plural (make sure 'subpar_element' is always of max len 1)
    if len(entity_parts['subpar_element'])>1:
        entity_parts['subpar_element'] = [" ".join (entity_parts['subpar_element'])]
        if len(entity_parts['subpar_element_num']) > 0 and not any([_has_range_indicator(s) for s in entity_parts['subpar_element_num']]) and not any([s.strip().lower().endswith('s') for s in entity_parts['subpar_element']]):
            entity_parts['subpar_element_num'] = [entity_parts['subpar_element_num'][-1]]

    # RESOLVE RANGES
    subpar_element_nums_resolved = []
    for num in entity_parts['subpar_element_num']:
        if not _has_range_indicator(num):
            subpar_element_nums_resolved.append(num)
        else:
            subpar_element_nums_resolved.extend(_resolve_range(num))
    entity_parts['subpar_element_num'] = subpar_element_nums_resolved

    element_nums_resolved = []
    for num in entity_parts['element_num']:
        if not _has_range_indicator(num):
            element_nums_resolved.append(num)
        else:
            element_nums_resolved.extend(_resolve_range(num))
    entity_parts['element_num'] = element_nums_resolved

    #  pre-determine some special case relation types
    relation = None
    # if n right contain amendment specifications -> external
    context = entity.text_with_ws + "".join([t.text_with_ws for t in utils.get_n_right(5, entity[-1])])
    if re.search('(?:is|are).{1,4}(deleted|amended|replaced)', context) is not None:
        relation = "external"

    def _num_element_combinations(elements, element_nums):
        if len(element_nums)==0:
            return([(e, "") for e in elements])
        else:
            return [(" ".join(elements), num) for num in element_nums]


    subpar_refs = _num_element_combinations(entity_parts['subpar_element'], entity_parts['subpar_element_num'])
    element_refs = _num_element_combinations(entity_parts['element'], entity_parts['element_num'])
    act_refs = _num_element_combinations(entity_parts['act'], entity_parts['act_id'])


    i_subpar = 0
    i_element = 0
    i_act = 0

    n_subpar = len(subpar_refs)
    n_element  = len(element_refs)
    n_act = len(act_refs)

    if n_subpar >  i_subpar:

        while n_subpar > i_subpar:

            subpar = None
            subpar_num = None
            element  = None
            element_num = None
            act = None
            act_id = None

            subpar = subpar_refs[i_subpar][0]
            subpar_num = subpar_refs[i_subpar][1]

            if i_element < n_element:
                element = element_refs[i_element][0]
                element_num = element_refs[i_element][1]

            if i_act < n_act:
                act = act_refs[i_act][0]
                act_id = act_refs[i_act][1]

            _add_reference(relation = relation, subpar_element = subpar, subpar_element_num=subpar_num, element=element, element_num=element_num, act = act, act_id=act_id)

            i_subpar += 1

        i_element += 1
        i_act += 1


    if n_element > i_element:
        while n_element > i_element:

            subpar = None
            subpar_num = None
            element  = None
            element_num = None
            act = None
            act_id = None

            if i_element < n_element:
                element = element_refs[i_element][0]
                element_num = element_refs[i_element][1]

            if i_act < n_act:
                act = act_refs[i_act][0]
                act_id = act_refs[i_act][1]

            _add_reference(relation = relation, subpar_element = subpar, subpar_element_num=subpar_num, element=element, element_num=element_num, act = act, act_id=act_id)

            i_element += 1
        i_act += 1

    while n_act > i_act:

        subpar = None
        subpar_num = None
        element  = None
        element_num = None
        act = None
        act_id = None


        if i_act < n_act:
            act = act_refs[i_act][0]
            act_id = act_refs[i_act][1]

        _add_reference(relation = None, subpar_element = subpar, subpar_element_num=subpar_num, element=element, element_num=element_num, act = act, act_id=act_id)

        i_act += 1

    return reference_list
