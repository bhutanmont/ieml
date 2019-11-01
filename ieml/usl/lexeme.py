import itertools
from typing import List

from ieml.dictionary.script import Script
from ieml.usl import USL, PolyMorpheme, check_polymorpheme
from ieml.usl.constants import ADDRESS_SCRIPTS, ACTANTS_SCRIPTS, ADDRESS_PROCESS_VALENCE_SCRIPTS, \
    check_lexeme_scripts, SYNTAGMATIC_FUNCTION_ACTANT_TYPE_SCRIPT, SYNTAGMATIC_FUNCTION_QUALITY_TYPE_SCRIPT, \
    SYNTAGMATIC_FUNCTION_PROCESS_TYPE_SCRIPT, DEPENDANT_QUALITY, INDEPENDANT_QUALITY


def check_lexeme(lexeme, role=None):
    for pm in [lexeme.pm_flexion, lexeme.pm_content]:
        if not isinstance(pm, PolyMorpheme):
            raise ValueError("Invalid arguments to create a Lexeme, expects a Polymorpheme, not a {}."
                             .format(pm.__class__.__name__))

        check_polymorpheme(pm)

    check_lexeme_scripts(lexeme.pm_flexion.constant,
                         lexeme.pm_content.constant,
                         role=role)



class Lexeme(USL):
    """A lexeme without the PA of the position on the tree (position independant lexeme)"""

    syntactic_level = 2

    def __init__(self, pm_flexion: PolyMorpheme, pm_content: PolyMorpheme):
        super().__init__()
        self.pm_flexion = pm_flexion
        self.pm_content = pm_content

        # self.address = PolyMorpheme(constant=[m for m in pm_address.constant if m in ADDRESS_SCRIPTS])
        self.grammatical_class = self.pm_content.grammatical_class

        self._str = []
        for pm in [self.pm_content, self.pm_flexion]:
            if not self._str and pm.empty:
                continue
            self._str.append("({})".format(str(pm)))

        self._str = ''.join(reversed(self._str))
        if not self._str:
            self._str = "()"

    def do_lt(self, other):
        return self.pm_flexion < other.pm_flexion or \
               (self.pm_flexion == other.pm_flexion and self.pm_content < other.pm_content)

    def _compute_singular_sequences(self):
        if self.pm_flexion.is_singular and (self.pm_content is None or self.pm_content.is_singular):
            return [self]
        else:
            _product = [self.pm_flexion,
                        self.pm_content]
            _product = [p.singular_sequences for p in _product if p is not None]

            return [Lexeme(*ss)
                    for ss in itertools.product(*_product)]

    @property
    def morphemes(self):
        return sorted(set(self.pm_flexion.morphemes + self.pm_content.morphemes))