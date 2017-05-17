from bidict import bidict

from ieml.commons import LANGUAGES
from ieml.ieml_objects.commons import IEMLObjects
from ieml.script.operator import script
import os
import yaml
from metaclasses import Singleton
import numpy as np


class Term(IEMLObjects):
    closable = True

    __term_instances = {}

    def __new__(cls, s):
        if isinstance(s, str) and s[0] == '[' and s[-1] == ']':
            s = s[1:-1]
        s = script(s)

        if s not in cls.__term_instances:
            cls.__term_instances[s] = super(Term, cls).__new__(cls)

        return cls.__term_instances[s]

    def __init__(self, s):
        if isinstance(s, Term):
            self.script = s.script
        else:
            self.script = script(s)

        self.grammatical_class = self.script.script_class

        super().__init__([])

        self._relations = {}

        # if term in a dictionary, those values will be set
        self.translation = None
        self.inhibitions = None
        self.root = None
        self.rank = None
        self.index = None

    def relations(self, relation_name):
        if relation_name not in self._relations:
            from models.relations import RelationsQueries
            self._relations[relation_name] = \
                [Term(s) for s in RelationsQueries.relations(self.script, relation_title=relation_name)]

        return self._relations[relation_name]

    __hash__ = IEMLObjects.__hash__

    def __eq__(self, other):
        if not isinstance(other, Term):
            return False

        return self.script == other.script

    def _do_gt(self, other):
        return self.script > other.script

    def compute_str(self, children_str):
        return "[" + str(self.script) + "]"

    @property
    def empty(self):
        return self.script.empty

    @property
    def defined(self):
        return all(self.__getattribute__(p) is not None for p in ['translation', 'inhibitions', 'root', 'rank', 'index'])



def save_dictionary(directory):
    """
    Save the dictionary to a file.
    the roots argument must be the form:
    {
    root_p => {
        paradigms => [{
            paradigm => '',
            translation => {
                fr => '',
                en => ''
            }, ...],
        inhibitions => ['', ...]
        translation => {
                fr => '',
                en => ''
            }
        }
    }
    :param dictionary:
    :param directory:
    :return:
    """

    def _get_translations(term):
        return {l: Dictionary().translations[l][term] for l in LANGUAGES }

    save = {str(root.script): {
        'translation': _get_translations(root),
        'inhibitions': root.inhibitions,
        'paradigms': [{
            'paradigm': str(p.script),
            'translation': _get_translations(p)
        } for p in Dictionary().terms.values() if p.root == root]
    } for root in Dictionary().roots}

    file = os.path.join(directory, "dictionary.yml")
    with open(file, 'w') as fp:
        yaml.dump(save, fp)


def load_dictionary(directory):
    file = os.path.join(directory, "dictionary.yml")

    with open(file, 'r') as fp:
        roots = yaml.load(fp)

    dictionary = Dictionary()

    for r_p, v in roots.items():
        dictionary.add_term(r_p, root=True, inhibitions=v['inhibitions'], translation=v['translation'])
        for p in v['paradigms']:
            dictionary.add_term(p['paradigm'], root=False, translation=p['translation'])

    dictionary.compute_relations()
    return dictionary


class Dictionary(metaclass=Singleton):
    def __init__(self):

        super().__init__()

        self.terms = {}
        self.translations = {l: bidict() for l in LANGUAGES}
        self.roots = {}
        self.tables = {}
        self.index = []

    def add_term(self, script, root=False, inhibitions=(), translation=None):

        term = Term(script)

        if term.script in self.terms:
            print("Term %s already defined."%str(term))
            return

        roots_p = {root_term for root_term in self.roots if term.script in root_term.script}

        if len(roots_p) == 1:
            root_p = next(roots_p.__iter__())
            if root:
                raise ValueError("Root paradigm intersection with term %s when adding root term %s"%
                                 (str(root_p), str(term)))

            self._define_term(term, root_p=root_p, inhibitions=inhibitions, translation=translation)

        elif len(roots_p) > 1:
            raise ValueError("Can't define the term %s in the dictionary, the term is in multiples root paradigms [%s]"%
                             (str(term), ', '.join(map(str, roots_p))))
        elif root:
            if not term.script.paradigm:
                raise ValueError("Can't add the singular sequence term %s as a root paradigm."%str(term))

            self._define_root(term, inhibitions, translation)

        else:
            raise ValueError("Can't add term %s to the dictionary, it is not defined within a root paradigm."%str(term))

    def _define_term(self, term, root_p, inhibitions, translation):

        self.set_translation(term, translation)

        term.root = root_p
        self.roots[root_p].append(term)

        term.inhibitions = inhibitions

        self.terms[term.script] = term

    def _define_root(self, term, inhibitions, translation):
        self.roots[term] = list()
        self._define_term(term, root_p=term, inhibitions=inhibitions, translation=translation)

        # for ss in term.script.singular_sequences:
        #     self.add_term(ss, root=False)

    # def _define_table(self, term):

    def __len__(self):
        return len(self.terms)

    def set_translation(self, term, translation):
        if not isinstance(translation, dict) or len(translation) != 2 or any(not isinstance(v, str) for v in translation.values()):
            raise ValueError("Invalid translation format for term %s."%str(term))

        for l in LANGUAGES:
            if l not in translation:
                raise ValueError("Missing translation for %s language for term %s"%(l, str(term)))

            if translation[l] in self.translations[l].inv:
                raise ValueError("Translation %s provided for term %s already used for term %s."%
                                 (translation[l], str(self.translations[l].inv[translation[l]]), str(term)))

            self.translations[l][term] = translation[l]

        term.translation = translation

    def compute_relations(self):
        self.index = sorted(self.terms.values())
        for i, t in enumerate(self.index):
            t.index = i

        self.contains = np.zeros(shape=(len(self), len(self)), dtype=np.int8)

        for r_p, v in self.roots.items():
            paradigms = {t for t in v if t.script.paradigm}
            indexes = [t.index for t in v]
            self.contains[r_p.index, indexes] = 1

            for p in paradigms:
                contains = [self.terms[ss] for ss in p.script.singular_sequences] + [k for k in paradigms if k in p]
                p.contains = contains
                contains = [c.index for c in contains]

                self.contains[p.index, contains] = 1

        # rel_shape = (len(self),)*2
        #
        # def test(i, j):
        #     return self.index[i].script in self.index[j].script
        # # rel_contain = lambda i, j:
        # self.contained = np.fromfunction(np.vectorize(test), shape=rel_shape, dtype=np.int32)



if __name__ == '__main__':
    print(os.getcwd())
    d = load_dictionary('../../data/dictionary')
    print(d.contains)
    print(len(d))
