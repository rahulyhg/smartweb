import urllib
import urllib2
import httplib
import json
from InformationSource import InformationSource
from isistan.smartweb.preprocess.StringTransformer import StringTransformer

__author__ = 'ignacio'


class FreebaseInformationSource(InformationSource):
    #
    # Obtains information about terms using freebase as a source

    _NUMBER_OF_RETRIES = 10
    _NUMBER_OF_SENTENCES = 3
    _SEARCH_SERVICE_URL = 'https://www.googleapis.com/freebase/v1/search'
    _TOPIC_SERVICE_URL = 'https://www.googleapis.com/freebase/v1/topic'

    def __init__(self, api_key):
        self._api_key = api_key
        self._cache = {}

    def search(self, query):
        additional_words = []
        query = query.encode('utf-8')
        n_retries = 0
        retry = True
        if query in self._cache:
            print 'found information for query: ' + query
            return self._cache[query]
        params = {
            'query': query,
            'key': self._api_key
        }
        search_url = self._SEARCH_SERVICE_URL + '?' + urllib.urlencode(params)
        while retry and n_retries < self._NUMBER_OF_RETRIES:
            try:
                retry = False
                response = json.loads(urllib2.urlopen(search_url).read())
                if len(response['result']) > 0:
                    topic_id = response['result'][0]['mid']
                    if topic_id in self._cache:
                        print 'found information for query: ' + query
                        return self._cache[topic_id]
                    params = {
                        'key': self._api_key,
                        'filter': 'suggest'
                    }
                    topic_search_url = self._TOPIC_SERVICE_URL + topic_id + '?' + urllib.urlencode(params)
                    topic = json.loads(urllib2.urlopen(topic_search_url).read())
                    if '/common/topic/article' in topic['property']:
                        if '/common/document/text' in topic['property']['/common/topic/article']['values'][0]['property']:
                            sentences = topic['property']['/common/topic/article']['values'][0]['property']['/common/document/text']['values'][0]['value'].split('.')
                            if sentences is not None:
                                print 'found information for query: ' + query
                                for i in range(0, min(len(sentences), self._NUMBER_OF_SENTENCES)):
                                    transformer = StringTransformer()
                                    additional_sentence = transformer.transform(sentences[i]).get_words_list()
                                    additional_words.extend(additional_sentence)
                                self._cache[topic_id] = additional_words
                                self._cache[query] = additional_words
                            else:
                                print 'information not found for query: ' + query
                        else:
                            print 'information not found for query: ' + query
                else:
                    print 'information not found for query: ' + query
            except (urllib2.HTTPError, httplib.BadStatusLine, urllib2.URLError):
                print 'retry'
                retry = True
                n_retries += 1

        return additional_words