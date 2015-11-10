import ConfigParser
from os.path import join

from isistan.smartweb.preprocess.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors

from isistan.smartweb.core.SearchEngine import SmartSearchEngine
from isistan.smartweb.persistence.WordBag import WordBag
from isistan.smartweb.preprocess.StringPreprocessorAdapter import StringPreprocessorAdapter
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class LSASearchEngine(SmartSearchEngine):
    #
    # Registry implementation using kd-tree

    def __init__(self):
        super(LSASearchEngine, self).__init__()
        self._service_array = []        
        self._lsi_index = None
        self._tfidf_matrix = None
        self._svd_matrix = None

    def load_configuration(self, configuration_file):
        super(LSASearchEngine, self).load_configuration(configuration_file)
        config = ConfigParser.ConfigParser()
        config.read(configuration_file)
        number_of_topics = config.getint('RegistryConfigurations', 'number_of_topics')
        self._svd = TruncatedSVD(n_components=number_of_topics)
        self._vectorizer = TfidfVectorizer(sublinear_tf=False,
                                           analyzer='word', lowercase=False, use_bm25idf=self._use_bm25idf,
                                           bm25_tf=self._use_bm25tf, k = self._bm25_k,
                                           preprocessor=StringPreprocessorAdapter('english.long'))

    def unpublish(self, service):
        pass

    def publish_services(self, service_list):
        transformer = self._create_document_transformer(service_list)
        documents = []
        current_document = 1
        for document in service_list:
            print 'Loading document ' + str(current_document) + ' of ' + str(len(service_list))         
            if self._load_corpus_from_file:
                bag_of_words = WordBag().load_from_file(join(self._corpus_path, self._get_document_filename(document)))
            else:
                if self._document_expansion:
                    bag_of_words = self._semantic_transformer.transform(transformer.transform(document))
                else:
                    bag_of_words = transformer.transform(document)
            if self._save_corpus:
                bag_of_words.save_to_file(join(self._corpus_path, self._get_document_filename(document)))
            words = bag_of_words.get_words_str()
            documents.append(words)
            self._service_array.append(document)
            current_document += 1
        self._tfidf_matrix = self._vectorizer.fit_transform(documents)
        self._svd_matrix = self._svd.fit_transform(self._tfidf_matrix.toarray())
        self._lsi_index = NearestNeighbors(10, algorithm='brute', metric='euclidean')
        self._lsi_index.fit(self._svd_matrix)

    def publish(self, service):
        pass

    def find(self, query):
        transformer = StringTransformer()
        query_array = self._vectorizer.transform([transformer.transform(query).get_words_str()])
        query_array = self._svd.transform(query_array.toarray())
        result = self._lsi_index.kneighbors(query_array, return_distance=False)[0]
        result_list = []
        for index in result:
            result_list.append(self._service_array[index])
        return result_list

    def number_of_services(self):
        pass
