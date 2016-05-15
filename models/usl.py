from .base_queries import DBConnector, Tag
from .constants import TEXT_COLLECTION, HYPERTEXT_COLLECTION
from .exceptions import InvalidTags, TextAlreadyExists, HypertextAlreadyExists
import re
from pymongo.errors import DuplicateKeyError

class TextQueries(DBConnector):
    def __init__(self):
        super().__init__()
        self.texts = self.db[TEXT_COLLECTION]

    def _write_text_to_db(self, text, tags):
        try:
            self.texts.insert_one({
                "_id" : str(text),
                "TAGS" : tags,
                "PROPOSITIONS" : [str(e) for e in text.childs]
            })
        except DuplicateKeyError:
            raise TextAlreadyExists()

    def get_text_from_ieml(self, text_ieml):
        return self.texts.find_one({"_id" : text_ieml})

    def save_text(self, text, tags):
        if not Tag.check_tags(tags):
            raise InvalidTags()

        self._write_text_to_db(text, tags)

    def search_text(self, search_string):
        regex = re.compile(search_string)
        result = self.texts.find({'$or': [
                        {'_id': {'$regex': regex}},
                        {'TAGS.FR': {'$regex': regex}},
                        {'TAGS.EN': {'$regex': regex}}]})
        return list(result)

    def check_tag_exist(self, tag, language):
        return self.texts.find_one({'TAGS.' + language: tag}) is not None

    def update_tags(self, ieml, tags_dict):
        """Updates the tag of a text identified by the input IEML"""
        self.texts.update_one({'_id': ieml},
                              {'$set': {'TAGS': tags_dict}})


class HyperTextQueries(TextQueries):
    def __init__(self):
        super().__init__()
        self.hypertexts = self.db[HYPERTEXT_COLLECTION]

    def _write_hypertext_to_db(self, hypertext, tags):
        try:
            self.hypertexts.insert_one({
                "TAGS": tags,
                "_id": str(hypertext),
                "TEXTS": [str(t) for t in hypertext.texts],
                "HYPERLINK": [
                    {'substance': transition[0],
                    'attribute': transition[1],
                    'mode': transition[2].to_ieml_list()} for transition in hypertext.transitions
                ]
            })
        except DuplicateKeyError:
            raise HypertextAlreadyExists()

    def save_hypertext(self, hypertext, tag):
        if not Tag.check_tags(tag):
            raise InvalidTags()

        self._write_hypertext_to_db(hypertext, tag)

    def check_tag_exist(self, tag, language):
        return self.texts.find_one({'TAGS.' + language: tag}) is not None and super().check_tag_exist(tag, language)

    def update_tags(self, ieml, tags_dict):
        """Updates the tag of a text identified by the input IEML"""
        self.hypertexts.update_one({'_id': ieml},
                                   {'$set': {'TAGS': tags_dict}})
