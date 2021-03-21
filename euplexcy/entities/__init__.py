from spacy.pipeline import EntityRuler
from spacy.tokens.span import Span
from spacy.tokens import Doc
from euplexcy.entities import references

# @TODO: add EntitySearch class here
# @TODO: add extra filed with classes and ufncitons/methods that inherit from EntitySarch in this directory, e.g. references.py class References

class EntitySearch(EntityRuler):

    """A custom EntityRuler object allowing for a custom Matcher (e.g. used for references)
    Custom logic, e.g. search by paragraph etc for references, is implemented in the Matcher"""

    def __init__(self, matcher, add_details_as_label = False, extension_detail_prefix = "", **kwargs):

        # super etc
        super().__init__(**kwargs)

        if not Span.has_extension("references"):
            Span.set_extension("references", default = None)


        self.matcher = matcher()


    def match(self, doc: Doc): # overwrite match function for parent object (this is called in the __call__ function), return matches

        # match references
        matches = self.matcher(doc)

        return matches

    def set_annotations(self, doc, matches):
        """Modify the document in place"""
        entities = list (doc.ents)
        new_entities = []
        seen_tokens = set ()
        for label, start, end in matches:
            span = Span (doc, start, end, label=label)

            span._.references = references.resolve_reference_entities(span)

            if any (t.ent_type for t in span) and not self.overwrite:
                continue
            # check for end - 1 here because boundaries are inclusive
            if start not in seen_tokens and end - 1 not in seen_tokens:
                new_entities.append (span)
                entities = [
                    e for e in entities if not (e.start < end and e.end > start)
                ]
                seen_tokens.update (range (start, end))
        doc.ents = entities + new_entities
