from ieml.commons import GRAMMATICAL_CLASS_NAMES

remarkable_multiplication_lookup_table = {
    "U:U:": "wo", "U:A:": "wa", "U:S:": "y", "U:B:": "o", "U:T:": "e",
    "A:U:": "wu", "A:A:": "we", "A:S:": "u", "A:B:": "a", "A:T:": "i",
    "S:U:": "j",  "S:A:": "g",  "S:S:": "s", "S:B:": "b", "S:T:": "t",
    "B:U:": "h",  "B:A:": "c",  "B:S:": "k", "B:B:": "m", "B:T:": "n",
    "T:U:": "p",  "T:A:": "x",  "T:S:": "d", "T:B:": "f", "T:T:": "l"
}

REMARKABLE_ADDITION = {
    "O": {'U', 'A'},
    "M": {'S', 'B', 'T'},
    "F": {'U', 'A', 'S', 'B', 'T'},
    "I": {'E', 'U', 'A', 'S', 'B', 'T'}
}

PRIMITIVES = {
    'E',
    'U',
    'A',
    'S',
    'B',
    'T'
}

MAX_SINGULAR_SEQUENCES = 360
MAX_SIZE_HEADER = 12

character_value = {
    'E': 0x1,
    'U': 0x2,
    'A': 0x4,
    'S': 0x8,
    'B': 0x10,
    'T': 0x20

}

MAX_LAYER = 6

AUXILIARY_CLASS = GRAMMATICAL_CLASS_NAMES.inv['AUXILIARY']
VERB_CLASS = GRAMMATICAL_CLASS_NAMES.inv['VERB']
NOUN_CLASS = GRAMMATICAL_CLASS_NAMES.inv['NOUN']