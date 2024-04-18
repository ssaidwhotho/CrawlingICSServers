class CounterObject:
    def __init__(self):
        self.unique_pages = 0
        self.ics_subdomains = {}
        self.word_count = {}
        self.longest_page = (None, 0)
        self.stopwords = [
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
    'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot',
    'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing',
    "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
    "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd",
    "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
    'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if',
    'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me',
    'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', "ought", 'our', 'ours', 'ourselves',
    'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's",
    'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the',
    'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these',
    'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through',
    'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd",
    "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when',
    "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why',
    "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll",
    "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']


    def increment_unique_pages(self):
        self.unique_pages += 1

    def increment_ics_subdomains(self, subdomain):
        if subdomain in self.ics_subdomains:
            self.ics_subdomains[subdomain] += 1
        else:
            self.ics_subdomains[subdomain] = 1

    def increment_word(self, word):
        if word in self.word_count:
            self.word_count[word] += 1
        else:
            self.word_count[word] = 1

    def increment_words(self, words):
        for word in words:
            if word in self.word_count:
                self.word_count[word] += 1
            else:
                self.word_count[word] = 1

    def remove_stopwords(self):
        for word in self.stopwords:
            if word in self.word_count:
                del self.word_count[word]

    def set_longest_page(self, url, word_count):
        self.longest_page = (url, word_count)

    def get_unique_pages(self):
        return self.unique_pages

    def get_ics_subdomains(self):
        return self.ics_subdomains

    def get_ics_subdomain_count(self):
        return len(self.ics_subdomains) #len(dict) returns the amount of keys, right?

    def get_word_count(self):
        return self.word_count

    def get_longest_page_count(self):
        return self.longest_page[1]

    def get_longest_page_url(self):
        return self.longest_page[0]
