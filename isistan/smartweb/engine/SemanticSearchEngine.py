import ConfigParser
from os.path import join

from gensim import corpora, models, similarities

from LSAModelFactory import LSAModelFactory
from LDAModelFactory import LDAModelFactory
from isistan.smartweb.core.SearchEngine import SmartSearchEngine
from isistan.smartweb.persistence.WordBag import WordBag
from isistan.smartweb.preprocess.StringPreprocessor import StringPreprocessor
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class SemanticSearchEngine(SmartSearchEngine):
    #
    # Registry implementation using Latent Semantic Analysis

    def __init__(self):
        super(SemanticSearchEngine, self).__init__()
        self._service_array = []
        self._dictionary = None
        self._corpus = None
        self._tfidf_corpus = None
        self._tfidf_model = None
        self._model_factory = None
        self._model = None
        self._index = None
        self._preprocessor = StringPreprocessor('english.long')
        self._number_of_topics = 200

    def load_configuration(self, configuration_file):
        super(SemanticSearchEngine, self).load_configuration(configuration_file)
        
        config = ConfigParser.ConfigParser()
        config.read(configuration_file)

        self._number_of_topics = config.getint('RegistryConfigurations', 'number_of_topics')
        algorithm = config.get('RegistryConfigurations', 'algorithm')
        if algorithm == 'LDA':
            self._model_factory = LDAModelFactory()
        elif algorithm == 'LSA':
            self._model_factory = LSAModelFactory()

    def unpublish(self, service):
        pass

    def publish_services(self, service_list):
        transformer = self._create_document_transformer(service_list)
        documents = []
        current_document = 1;
        for document in service_list:
            print "Loading document " + str(current_document) + " of " + str(len(service_list))
            if self._load_corpus_from_file:
                bag_of_words = WordBag().load_from_file(join(self._corpus_path, self._get_document_filename(document)))
            else:
                if self._document_expansion:
                    bag_of_words = self._semantic_transformer.transform(transformer.transform(document))
                else:
                    bag_of_words = transformer.transform(document)
            if self._save_corpus:
                bag_of_words.save_to_file(join(self._corpus_path, self._get_document_filename(document)))
            words = bag_of_words.get_words_list()
            documents.append(self._preprocessor(words))
            self._service_array.append(document)
            current_document += 1
       
        self._dictionary = corpora.Dictionary(documents)
        self._corpus = [self._dictionary.doc2bow(document) for document in documents]

        self._tfidf_model = models.TfidfModel(self._corpus)
        self._tfidf_corpus = self._tfidf_model[self._corpus]
        self._model = self._model_factory.create(self._tfidf_corpus,
                                                 self._dictionary,
                                                 self._number_of_topics)
        self._index = similarities.MatrixSimilarity(self._model[self._corpus])

    def publish(self, service):
        pass

    def find(self, query):
        transformer = StringTransformer()
        query_vector = self._dictionary.doc2bow(self._preprocessor(transformer.transform(query).get_words_list()))
        query_tfidf_vector = self._tfidf_model[query_vector]
        query_lsi_vector = self._model[query_tfidf_vector]
        results = self._index[query_lsi_vector]
        results = sorted(enumerate(results), key=lambda item: -item[1])
        result_list = []
        for tuple_result in results:
            result_list.append(self._service_array[tuple_result[0]])
        return result_list

    def number_of_services(self):
        pass