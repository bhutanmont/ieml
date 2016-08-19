import itertools

from ieml.script.exceptions import InvalidScriptCharacter, InvalidScript, IncompatiblesScriptsLayers, TooManySingularSequences
from ieml.commons import TreeStructure
from ieml.script.constants import MAX_LAYER, MAX_SINGULAR_SEQUENCES
from ieml.script.constants import LAYER_MARKS, PRIMITVES, remarkable_multiplication_lookup_table, REMARKABLE_ADDITION, \
    character_value, AUXILIARY_CLASS, VERB_CLASS, NOUN_CLASS


class Script(TreeStructure):
    """ A parser is defined by a character (PRIMITIVES, REMARKABLE_ADDITION OR REMARKABLE_MULTIPLICATION)
     or a list of parser children. All the element in the children list must be an AdditiveScript or
     a MultiplicativeScript."""
    def __init__(self, children=None, character=None):
        super().__init__()

        if children:
            self.children = children
        else:
            self.children = []

        if character:
            self.character = character
        else:
            self.character = None

        # Layer of this parser
        self.layer = None

        # If it is a a paradigm
        self.paradigm = None

        # If the parser is composed with E
        self.empty = None

        # The number of singular sequence (if paradigm it is one, self)
        self.cardinal = None

        # The singular sequences
        self._singular_sequences = None

        # The contained paradigms (tables)
        self._tables = []

        # The canonical string to compare same layer and cardinal parser (__lt__)
        self.canonical = None

        # class of the parser, one of the following : VERB (1), AUXILIARY (0), and NOUN (2)
        self.script_class = None

    def __add__(self, other):
        if not isinstance(other, Script):
            raise InvalidScript()

        return AdditiveScript(children=[self, other])

    def __eq__(self, other):
        if not isinstance(other, Script):
            return False

        if self._str is None or other._str is None:
            return NotImplemented

        return self._str == other._str

    def __hash__(self):
        """Since the IEML string for any proposition AST is supposed to be unique, it can be used as a hash"""
        return self.__str__().__hash__()

    def __lt__(self, other):
        if not isinstance(self, Script) or not isinstance(other, Script):
            return NotImplemented

        if self == other:
            return False

        if self.layer != other.layer:
            # order by layer
            return self.layer < other.layer
        else:
            # Cardinal of 1 the minimum, null_script is minimum
            if isinstance(self, NullScript):
                return True

            if isinstance(other, NullScript):
                return False

            if self.cardinal != other.cardinal:
                # then by number of singular sequence
                return self.cardinal < other.cardinal
            else:
                # Compare the canonical form
                if self.canonical != other.canonical:
                    return self.canonical < other.canonical
                elif self.layer != 0:
                    # layer != 0 => children is set, no children are for layer 0 (MultiplicativeScript)
                    if isinstance(self, other.__class__):
                        # if they are the same class
                        # Compare the children in alphabetical order
                        iterator = iter(other.children)
                        for s in self.children:
                            try:
                                o = iterator.__next__()
                                if o != s:
                                    return s < o
                            except StopIteration:
                                return False
                        # self have fewer elements, all equals to the first of other's children, self is lower.
                        return True
                    else:
                        # not an instance, one is multiplicative, other one is additive
                        # They have the same number of singular sequence so the multiplicative is fewer :
                        # each variable of the addition have less singular sequence than the multiplication parser
                        return isinstance(self, MultiplicativeScript)
                else:
                    # Layer 0
                    # Compare the value of the character or the sum
                    if isinstance(self, AdditiveScript):
                        # The character value is the sum of all character of the addition
                        self_char_value = sum((character_value[c.character] for c in self.children))
                    else:
                        self_char_value = character_value[self.character]

                    if isinstance(other, AdditiveScript):
                        # The character value is the sum of all character of the addition
                        other_char_value = sum((character_value[c.character] for c in other.children))
                    else:
                        other_char_value = character_value[other.character]

                    return self_char_value < other_char_value

    def __getitem__(self, index):
        return self.children[index]

    def _compute_singular_sequences(self):
        pass

    def __contains__(self, item):
        if not isinstance(item, Script):
            return False

        return set(item.singular_sequences).issubset(set(self.singular_sequences))

    @property
    def singular_sequences(self):
        if self._singular_sequences:
            return self._singular_sequences

        self._singular_sequences = self._compute_singular_sequences()
        return self._singular_sequences


class AdditiveScript(Script):
    """ Represent an addition of same layer scripts."""
    def __init__(self, children=None, character=None):
        _character = None
        _children = []

        if children:
            _children = children

        if character in REMARKABLE_ADDITION:
            _character = character
            _children = REMARKABLE_ADDITION_SCRIPT[_character]
        elif character is not None:
            raise InvalidScriptCharacter(character)
        else:
            if len(_children) == 0:
                raise InvalidScript()

        # check all children are the same layer
        l = _children[0].layer
        for c in _children:
            if c.layer != l:
                raise IncompatiblesScriptsLayers(_children[0], c)

        if _children:

            to_remove = []
            to_add = []
            # remove the sub addition
            for c in _children:
                if isinstance(c, AdditiveScript):
                    to_remove.append(c)
                    to_add.extend(c.children)

            _children.extend(to_add)
            # Remove duplicate children
            _children = list(set(c for c in _children if c not in to_remove))

        # make a character with the children if possible
        if l == 0:
            _char_set = set(map(lambda e: str(e)[0], _children))
            for key, value in REMARKABLE_ADDITION.items():
                if _char_set == value:
                    _character = key
                    break

        super().__init__(children=_children, character=_character)

        if self.character:  # remarkable addition
            self.layer = 0
            self.empty = False
            self.paradigm = True
            self.cardinal = len(REMARKABLE_ADDITION[self.character])
        else:
            self.layer = self.children[0].layer
            self.empty = all((e.empty for e in self.children))
            self.paradigm = len(self.children) > 1 or any(child.paradigm for child in self.children)
            self.cardinal = sum((e.cardinal for e in self.children))

        if self.cardinal > MAX_SINGULAR_SEQUENCES:
            raise TooManySingularSequences(self.cardinal)

        self.script_class = max(c.script_class for c in self)

        self._do_precompute_str()
        self.__order()

    def _do_precompute_str(self):
        self._str = \
            (self.character + LAYER_MARKS[0]) if self.character is not None \
            else '+'.join([str(child) for child in self.children])

    def __order(self):
        # Ordering of the children
        self.children.sort()

        if self.layer == 0:
            value = 0b0
            for child in self:
                value |= character_value[child.character]
            self.canonical = bytes([value])
        else:
            self.canonical = b''.join([child.canonical for child in self])

    def _compute_singular_sequences(self):
        # Generating the singular sequence
        if not self.paradigm:
            return [self]
        else:
            # additive proposition has always children set
            s = [sequence for child in self.children for sequence in child.singular_sequences]
            s.sort()
            return s


class MultiplicativeScript(Script):
    """ Represent a multiplication of three scripts of the same layer."""
    def __init__(self, substance=None, attribute=None, mode=None, children=None, character=None):
        if not (substance or children or character):
            raise InvalidScript()

        # Build children
        if children is None:
            children = [substance, attribute, mode]

        _children = []
        for child in children:
            if child is not None:
                _children.append(child)
            else:
                break

        # Replace all the corresponding children to character
        _character = None
        if character is not None:
            if character == 'E':
                raise InvalidScript()

            _character = character
            if _character in PRIMITVES:
                _children = []
                layer = 0
            elif _character in REMARKABLE_MULTIPLICATION_SCRIPT:
                _children = REMARKABLE_MULTIPLICATION_SCRIPT[_character]
                layer = 1
            else:
                raise InvalidScriptCharacter(character)
        else:
            layer = _children[0].layer

        for i, c in enumerate(_children):
            elem = c
            if isinstance(c, AdditiveScript) and len(c.children) == 1:
                elem = c.children[0]
            _children[i] = elem

        # Replace the empty values
        for i, c in enumerate(_children):
            if c.empty:
                _children[i] = NullScript(layer=c.layer)

        # Fill the children to get a size of 3
        if _character not in PRIMITVES:
            for i in range(len(_children), 3):
                _children.append(NullScript(layer=layer))

        # Add the character to children corresponding to specific combinaison
        _str_children = self._render_children(_children, _character)
        if _str_children in remarkable_multiplication_lookup_table:
            _character = remarkable_multiplication_lookup_table[_str_children]

        super().__init__(children=_children, character=_character)

        # Compute the attributes of this parser
        if self.character:
            self.layer = 0 if self.character in PRIMITVES else 1
            self.paradigm = False
            self.cardinal = 1
            self.empty = self.character == 'E'
        else:
            self.layer = _children[0].layer + 1
            self.empty = all((e.empty for e in self.children))
            self.paradigm = any((e.paradigm for e in self.children))

            self.cardinal = 1
            for e in self.children:
                self.cardinal = self.cardinal * e.cardinal

        if self.layer == 0:
            self.script_class = VERB_CLASS if self.character in REMARKABLE_ADDITION['O'] else NOUN_CLASS
        else:
            self.script_class = self.children[0].script_class

        if self.layer != 0:
            # check number of children
            if not len(self.children) == 3:
                raise InvalidScript()

            # check every child of the same layer
            if not self.children[0].layer == self.children[1].layer == self.children[2].layer:
                raise InvalidScript()

            # check layer
            if not self.layer == self.children[0].layer + 1:
                raise InvalidScript()

        if self.cardinal > MAX_SINGULAR_SEQUENCES:
            raise TooManySingularSequences(self.cardinal)

        self._do_precompute_str()
        self.__order()

    def _render_children(self, children=None, character=None):
        if character:
            return character
        else:
            empty = True
            result = ''
            for i, c in enumerate(reversed(children)):
                if not c.empty:
                    empty = False

                if not empty or not c.empty or i == 2:
                    result = str(c) + result
            return result

    def _do_precompute_str(self):
        self._str = self._render_children(self.children, self.character) + LAYER_MARKS[self.layer]

    def __order(self):
        if self.layer == 0:
            self.canonical = bytes([character_value[self.character]])
        else:
            self.canonical = b''.join([child.canonical for child in self])

    def _compute_singular_sequences(self):
        # Generate the singular sequence
        if not self.paradigm:
            return [self]
        else:
            children_sequences = []
            for i in range(0, 3):
                if not self.children[i].empty:
                    children_sequences.append([(i, c) for c in self.children[i].singular_sequences])

            s = []
            for triplet in itertools.product(*children_sequences):
                children = self.children[:]
                for tpl in triplet:
                    children[tpl[0]] = tpl[1]

                sequence = MultiplicativeScript(children=children)
                s.append(sequence)

            s.sort()
            return s


class NullScript(Script):
    def __init__(self, layer):
        super().__init__(children=[])
        self.layer = layer
        self.paradigm = False
        self.empty = True
        self.cardinal = 1
        self.character = 'E'

        self._do_precompute_str()
        self.canonical = bytes([character_value[self.character]] * pow(3, self.layer))
        self.script_class = AUXILIARY_CLASS

    def __iter__(self):
        if self.layer == 0:
            return [].__iter__()

        return ([NULL_SCRIPTS[self.layer - 1]] * 3).__iter__()

    def _do_precompute_str(self):
        result = self.character
        for l in range(0, self.layer + 1):
            result = result + LAYER_MARKS[l]

        self._str = result

    def _compute_singular_sequences(self):
        return [self]


NULL_SCRIPTS = [NullScript(level) for level in range(0, MAX_LAYER)]

# Building the remarkable multiplication to parser
REMARKABLE_MULTIPLICATION_SCRIPT = {
    "wo": [MultiplicativeScript(character='U'), MultiplicativeScript(character='U'), NullScript(layer=0)],
    "wa": [MultiplicativeScript(character='U'), MultiplicativeScript(character='A'), NullScript(layer=0)],
    "y": [MultiplicativeScript(character='U'), MultiplicativeScript(character='S'), NullScript(layer=0)],
    "o": [MultiplicativeScript(character='U'), MultiplicativeScript(character='B'), NullScript(layer=0)],
    "e": [MultiplicativeScript(character='U'), MultiplicativeScript(character='T'), NullScript(layer=0)],

    "wu": [MultiplicativeScript(character='A'), MultiplicativeScript(character='U'), NullScript(layer=0)],
    "we": [MultiplicativeScript(character='A'), MultiplicativeScript(character='A'), NullScript(layer=0)],
    "u": [MultiplicativeScript(character='A'), MultiplicativeScript(character='S'), NullScript(layer=0)],
    "a": [MultiplicativeScript(character='A'), MultiplicativeScript(character='B'), NullScript(layer=0)],
    "i": [MultiplicativeScript(character='A'), MultiplicativeScript(character='T'), NullScript(layer=0)],

    "j": [MultiplicativeScript(character='S'), MultiplicativeScript(character='U'), NullScript(layer=0)],
    "g": [MultiplicativeScript(character='S'), MultiplicativeScript(character='A'), NullScript(layer=0)],
    "s": [MultiplicativeScript(character='S'), MultiplicativeScript(character='S'), NullScript(layer=0)],
    "b": [MultiplicativeScript(character='S'), MultiplicativeScript(character='B'), NullScript(layer=0)],
    "t": [MultiplicativeScript(character='S'), MultiplicativeScript(character='T'), NullScript(layer=0)],

    "h": [MultiplicativeScript(character='B'), MultiplicativeScript(character='U'), NullScript(layer=0)],
    "c": [MultiplicativeScript(character='B'), MultiplicativeScript(character='A'), NullScript(layer=0)],
    "k": [MultiplicativeScript(character='B'), MultiplicativeScript(character='S'), NullScript(layer=0)],
    "m": [MultiplicativeScript(character='B'), MultiplicativeScript(character='B'), NullScript(layer=0)],
    "n": [MultiplicativeScript(character='B'), MultiplicativeScript(character='T'), NullScript(layer=0)],

    "p": [MultiplicativeScript(character='T'), MultiplicativeScript(character='U'), NullScript(layer=0)],
    "x": [MultiplicativeScript(character='T'), MultiplicativeScript(character='A'), NullScript(layer=0)],
    "d": [MultiplicativeScript(character='T'), MultiplicativeScript(character='S'), NullScript(layer=0)],
    "f": [MultiplicativeScript(character='T'), MultiplicativeScript(character='B'), NullScript(layer=0)],
    "l": [MultiplicativeScript(character='T'), MultiplicativeScript(character='T'), NullScript(layer=0)]
}

# Building the remarkable addition to parser
REMARKABLE_ADDITION_SCRIPT = {key: [MultiplicativeScript(character=c) if c != 'E' else NullScript(layer=0) for c in REMARKABLE_ADDITION[key]] for key in REMARKABLE_ADDITION}
