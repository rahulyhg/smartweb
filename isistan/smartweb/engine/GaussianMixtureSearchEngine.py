from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.mixture import GMM

from isistan.smartweb.persistence.WordBag import WordBag
from isistan.smartweb.preprocess.text import TfidfVectorizer
from isistan.smartweb.core.SearchEngine import SmartSearchEngine
from isistan.smartweb.preprocess.StringPreprocessorAdapter import StringPreprocessorAdapter
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class GaussianMixtureSearchEngine(SmartSearchEngine):
    #
    # Registry implementation using clusters

    def __init__(self):
        super(GaussianMixtureSearchEngine, self).__init__()
        self._service_array = []
        self._cluster_index = None
        self._cluster = {}
        self._document_cluster = {}
        self._tfidf_matrix = None

    def load_configuration(self, configuration_file):
        super(GaussianMixtureSearchEngine, self).load_configuration(configuration_file)
        self._vectorizer = TfidfVectorizer(sublinear_tf=False,
                                           analyzer='word', lowercase=False, use_bm25idf=self._use_bm25idf,
                                           bm25_tf=self._use_bm25tf, k = self._bm25_k,
                                           preprocessor=StringPreprocessorAdapter('english.long'))

    def unpublish(self, service):
        pass

    def _preprocess(self, bag_of_words):
        return bag_of_words.get_words_str()

    def _after_publish(self, documents):
        self._tfidf_matrix = self._vectorizer.fit_transform(documents)
        self._cluster_index = GMM(n_components=8)
        labels_ = self._cluster_index.fit_predict(self._tfidf_matrix.toarray())
        i = 0
        self._document_cluster = {}
        for document in documents:
            if not labels_[i] in self._document_cluster:
                self._document_cluster[labels_[i]] = []
            self._document_cluster[labels_[i]].append((document, i))
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
        query = StringTransformer().transform(query)
        query_array = self._vectorizer.transform([self._query_transformer.transform(query).get_words_str()]).toarray()
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
