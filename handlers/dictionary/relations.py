from bidict import bidict

from handlers.dictionary.commons import script_parser, terms_db
from ieml.exceptions import CannotParse
from models.relations.relations_queries import RelationsQueries
from ieml.script.constants import OPPOSED_SIBLING_RELATION, ASSOCIATED_SIBLING_RELATION, CROSSED_SIBLING_RELATION, \
    TWIN_SIBLING_RELATION, FATHER_RELATION, SUBSTANCE, ATTRIBUTE, MODE, CHILD_RELATION, CONTAINED_RELATION, \
    CONTAINS_RELATION,ELEMENTS

relation_name_table = bidict({
    "Crossed siblings": CROSSED_SIBLING_RELATION,
    "Associated siblings": ASSOCIATED_SIBLING_RELATION,
    "Twin siblings": TWIN_SIBLING_RELATION,
    "Opposed siblings": OPPOSED_SIBLING_RELATION,

    "Ancestors in mode": FATHER_RELATION + '.' + MODE,
    "Ancestors in attribute": FATHER_RELATION + '.' + ATTRIBUTE,
    "Ancestors in substance": FATHER_RELATION + '.' + SUBSTANCE,

    "Descendents in mode": CHILD_RELATION + '.' + MODE,
    "Descendents in attribute": CHILD_RELATION + '.' + ATTRIBUTE,
    "Descendents in substance": CHILD_RELATION + '.' + SUBSTANCE,


    "Contained in": CONTAINED_RELATION,
    "Belongs to Paradigm": 'ROOT',
    "Contains": CONTAINS_RELATION
})

def get_relation_visibility(body):
    term_db_entry = terms_db.get_term(body["ieml"])
    inhibited_relations = [relation_name_table.inv[rel_name] for rel_name in term_db_entry["INHIBITS"]]
    return {"viz": inhibited_relations}


def add_relation_visiblity():
    pass


def remove_relation_visibility():
    pass


def toggle_relation_visibility():
    pass


def get_relations(term):
    try:
        script_ast = script_parser.palarse(term)
        all_relations = []
        for relation_type, relations in RelationsQueries.relations(script_ast, pack_ancestor=True).values():
            if relations: # if there aren't any relations, we skip
                all_relations.append({
                    "reltype" : relation_name_table.inv[relation_type],
                    "rellist" : [{"ieml" : rel,
                                  "exists": True,
                                  "visible": True}
                                 for rel in relations],
                    "exists" : True,
                    "visible" : True
                })
        return all_relations
    except CannotParse:
        pass # TODO : maybe define an error