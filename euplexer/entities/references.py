from euplexer import utils
from euplexer import regex as euplexre
from spacy.tokens import Doc
from spacy.tokens.span import Span
from euplexer import structure, elements
import warnings
import re



class ReferenceMatcher:

    """Custom matcher for references."""

    # @TODO: may be customized with additional "normal" spacy matcher object

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

        # article for article in mathc_Ref
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
            if ma1['start'] <= ma2['start'] and ma1['end'] >= ma2['end']:
                if ma1['type'] == "element_act" and (ma2['type'] == "element"):
                    ma_a = ma1

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

        def _has_element_num(text):
            words = text.split()
            words = [w for w in words if re.search(euplexre.entities['references']['elements'], w) is None]
            text = " ".join(words)
            if re.search(r'[0-9]| [XVI]{1,3}(?![a-z])| \([a-z]{1,2}\) ', text) is not None:
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

        def _acts(text):
            acts_list = [m for m  in re.findall ('[a-z]*' + euplexre.entities['references']['act_types'] + '[a-z]*', text, flags=re.MULTILINE|re.IGNORECASE)]
            return [a for a in acts_list if re.search('^' + euplexre.entities['references']['act_types'] + '$', a, flags=re.MULTILINE|re.IGNORECASE) is not None]

        def _has_act(text):
            if len (_acts (text)) > 0:
                return True
            else:
                return False

        def _has_cap_act(text):
            if any ([a.istitle () if re.search(r'thereof|hereto', a) is None else True for a in _acts (text) ]):
                return True
            else:
                return False


        cleaned_matches = []

        # @TODO first split and if, call process matches again for all parts bzw loop over?
        ## e.g. paragraph 1, the manufacturer or importer shall notify the Agency of the following information in the format specified by the Agency in accordance with Article 108: may be one match
        # and ACT/ELEMENT
        # or ACT/AELEMENT
        # , ACT/ELEMENT
        # . ACT/ELEMENT
        # .........
        split_match = [match]

        for submatch in split_match:

            submatch_span = doclike[utils.char_to_token (submatch['string_start'], doclike_char_token):utils.char_to_token (
                submatch['string_end'], doclike_char_token)]
            match_token_text = submatch_span.text

            if 'informed decisions' in submatch['match']:
                print("DEBUG")
                pass

            if not _has_element(match_token_text) and not _has_act(match_token_text):
                continue

            # rule out any non-references via regex dict
            if any([re.search(p, match_token_text) is not None for p in euplexre.entities['non_references']]):
                continue
            # if no element and only act and act is Article
            if re.search(euplexre.entities['references']['elements'], match_token_text, flags=re.IGNORECASE) is None and re.search(euplexre.entities['references']['act_types'], match_token_text, flags=re.IGNORECASE) is None:
                continue

            # if reference is merely self ref to whole act (list re.findall construction is necessary bc regex matches whitespace)
            if not _has_element_num(match_token_text) and re.search(r'(?:this|present)\s+[A-Z]+[a-z]*', match_token_text, flags=re.MULTILINE) is not None:
                continue

            # Element only without num (e.g. of Articles, of an Article, this Article, this Title etc)
            if _has_element(match_token_text) and not _has_element_num(match_token_text):
                continue

            # Act without capitalization (e.g. "unanimous agreement")
            if _has_act(match_token_text) and not _has_cap_act(match_token_text):
                continue

            # for acts/elements only check for this before (use n left)
            if _has_act(match_token_text) and not _has_element(match_token_text):
                act_match = re.search(euplexre.entities['references']['act_types'], match_token_text.strip(), flags=re.MULTILINE | re.IGNORECASE)
                if act_match is not None and act_match.start() < 1:
                    # get n 2 lef tokens and check
                    prefix = [t.text for t in utils.get_n_left(3, submatch_span[0])]
                elif act_match is not None:
                    # get string until act match
                    prefix = submatch['match'][:act_match.start()]
                else:
                    continue

                # check prefix for 'this'
                if "this" in prefix:
                    continue
                if " a " in prefix:
                    continue
                # @TODO (see issues notes) what abbout the Regulation if defined before

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

            mat_span = doclike[utils.char_to_token (mat['string_start'], doclike_char_token):utils.char_to_token (mat['string_end'], doclike_char_token)]
            ents_list.append((label,mat_span.start, mat_span.end))


    return(ents_list)





# count references

def parse_refs(match):  # or count?
    # return list of references (as dictionaries) contained in a match/string
    # @TODO: hier weiter

    match_span = doclike[utils.char_to_token (match['string_start'], doclike_char_token):]

    match_references = []

    def _token_type(token):

        pass

    def _is_separator(token):

        # check if it matches any ausschlusskriterien
        pass

    def _is_reference():

        # check if it matches any ausschlusskriterien
        pass

    def _ref_type():

        pass

    def _add_ref(ref_text, id, num, element, act, ref_type, match, multiple=False):
        # add reference dict to list with dict on details in
        # assign id
        pass

    prefix = ""
    element = ""
    act = ""
    current_id = 1

    match_ref = []

    for i, token in enumerate (match_span):
        # annotate token in Token._.reference['type', 'id']
        # only acts can  appear
        if _token_type (token) == "element":
            if current_ref_part == "element":
                pass
                # if token a subpart of article
                # -> part of same
                # else:
                # iterate id
            # new ref
            current_ref_part = "element"
            last_token_separator = True
        elif _token_type (token) == "num":
            if current_ref_part == "num":
                pass
                #  num = num + token
            elif current_ref_part == "element" or last_token_separator:
                pass
                # add new ref with element + token(as num)
            current_ref_part = "num"


        # is act tpye, identifier(?)
        ## add with prefix, get id back
        ## set prefix to ""
        ## set current id to id
        ## else
        # add to prefix
        elif not _is_separator (token) or _is_last_token (token):
            pass  ## for any not seaprator
            ## add to refernece identifiers or suffix with id
            # set current id to new id
        else:
            pass
            new_ref = True
            # iterate id

    # try to find act and check if theres a separator, if yes, split and try both

    # rename all keys to "match_"...
    # to differentiate from reference
    # or put match in separate dict within reference dict

    # for all remaining matches:
    # parse_match()
    # rigorously check for elements and determine int or ext

    # ( ) check if separator in match

    # check if multiple elements/acts (is this possible from regex? proabably)

    ## if yes, split

    # identify the references in a given match, use text for context
    # return: a list of reference dictionaries (text, pos, type, accuracy)
    # was it matched as part of group 1 (could bbe both) or group 2 (more likely to be ext)

    # watch out for subspecifications (article 1 paragraph 2) -> 1 ref and connectors (and, or, ,) -> multiple refs

    # there may be multiple references in a text, e.g. 4 to 5 or a match that accidentally contians more than one ref! (split by \n?)

    # do not count: .... (list of regexes that, if they match, disqualify the text as a ref) (widen text search by match pos +-)

    # if 1
    # split by act  1 bzw  what appens if 1 then 2 or 3 in same paragraph
    # parse_match(rest)
    # continue(first_part)
    # if 1 or 2
    # check for ranges and lists
    # create new ref for each and add all
    # if 3 add

    # examine references for content
    # multiple
    # non-counted ref etc

    # return list of references
    # (might be multiple of same match)
    # inclduing ref_type etc

    pass
