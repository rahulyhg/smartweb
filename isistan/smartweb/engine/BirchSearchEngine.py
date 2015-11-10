from os.path import join

from sklearn.cluster import Birch
from sklearn.neighbors import NearestNeighbors

from isistan.smartweb.preprocess.text import TfidfVectorizer
from isistan.smartweb.core.SearchEngine import SmartSearchEngine
from isistan.smartweb.persistence.WordBag import WordBag
from isistan.smartweb.preprocess.StringPreprocessorAdapter import StringPreprocessorAdapter
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class BirchSearchEngine(SmartSearchEngine):
    #
    # Registry implementation using clusters

    def __init__(self):
        super(BirchSearchEngine, self).__init__()
        self._service_array = []
        self._cluster_index = None
        self._cluster = {}
        self._document_cluster = {}
        self._tfidf_matrix = None

    def load_configuration(self, configuration_file):
        super(BirchSearchEngine, self).load_configuration(configuration_file)
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
        self._cluster_index = Birch(n_clusters=20)
        self._cluster_index.fit(self._tfidf_matrix.toarray())
        i = 0
        self._document_cluster = {}
        for document in documents:
            if not self._cluster_index.labels_[i] in self._document_cluster:
                self._document_cluster[self._cluster_index.labels_[i]] = []
            self._document_cluster[self._cluster_index.labels_[i]].append((document, i))
            i += 1
        print 'Number of clusters: ' + str(len(self._document_cluster))
        for label in self._document_cluster:
            print 'Label elements: ' + str(len(self._document_cluster[label]))
        for label in self._document_cluster:
            if len(self._document_cluster[label]) < 10:
                self._cluster[label] = NearestNeighbors(len(self._document_cluster[label]), algorithm='brute', metric='euclidean')
            else:
                self._cluster[label] = NearestNeighbors(10, algorithm='brute', metric='euclidean')
            tfidf_matrix = self._vectorizer.transform(doc[0] for doc in self._document_cluster[label])
            self._cluster[label].fit(tfidf_matrix.toarray())

    def publish(self, service):
        pass

    def find(self, query):
        transformer = StringTransformer()
        query_array = self._vectorizer.transform([transformer.transform(query).get_words_str()]).toarray()
        target_label = self._cluster_index.predict(query_array)[0]
        target_indexes = self._cluster[target_label].kneighbors(query_array, return_distance=False)[0]
        result = []
        for target in target_indexes:
            result.append(self._document_cluster[target_label][target][1])
        result_list = []
        for index in result:
            result_list.append(self._service_array[index])
        return result_list

    def number_of_services(self):
        pass
