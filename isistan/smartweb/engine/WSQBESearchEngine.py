import ConfigParser

from gensim import corpora, models, similarities

from isistan.smartweb.core.SearchEngine import SmartSearchEngine
from isistan.smartweb.preprocess.StringPreprocessor import StringPreprocessor
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class WSQBESearchEngine(SmartSearchEngine):
    #
    # WSQBE engine implementation in python

    def __init__(self):
        super(WSQBESearchEngine, self).__init__()
        self._service_array = []
        self._dictionary = None
        self._corpus = None
        self._tfidf_corpus = None
        self._tfidf_model = None
        self._index = None
        self._word2vec_model = None
        self._preprocessor = StringPreprocessor('english.long')

    def unpublish(self, service):
        pass

    def _get_words(self, bag_of_words):
        return bag_of_words.get_words_list()

    def _after_publish(self, documents):
        self._dictionary = corpora.Dictionary(documents)
        self._corpus = [self._dictionary.doc2bow(document) for document in documents]
        self._tfidf_model = models.TfidfModel(self._corpus)
        self._tfidf_corpus = self._tfidf_model[self._corpus]
        self._index = similarities.MatrixSimilarity(self._tfidf_corpus)

    def publish(self, service):
        pass

    def find(self, query):
        transformer = StringTransformer()
        query_vector = self._dictionary.doc2bow(self._preprocessor(transformer.transform(query).get_words_list()))
        query_tfidf_vector = self._tfidf_model[query_vector]
        results = self._index[query_tfidf_vector]
        results = sorted(enumerate(results), key=lambda item: -item[1])
        result_list = []
        for tuple_result in results:
            result_list.append(self._service_array[tuple_result[0]])
        return result_list

    def number_of_services(self):
        pass
