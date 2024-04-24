from utils.hasher import Hash


class CounterObject:
    def __init__(self):
        self.all_page_data = {}
        self.unique_pages = 0
        self.ics_subdomains = {}
        self.word_count = {}
        self.longest_page = (None, 0)
        self._hasher = Hash()
        self.documents = {}  # dict of bit represented documents
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

    def add_new_page(self, url, word_list):
        """Adds a new page to the counter object and writes the data to a file."""
        self.all_page_data[url] = word_list
        with open("data.txt", "a+") as f:
            f.write(f"{url}: {word_list}\n\n\n\n")

        with open("allInfo.txt", "w+") as f1:
            f1.write(f"Unique Pages: {self.unique_pages}\n\n")
            f1.write(f"Longest Page: {self.longest_page}\n\n")
            f1.write(f"50 Most Common Words: {self.get_50_most_common_words()}\n\n")
            f1.write(f"ICS Subdomains: {self.ics_subdomains}\n\n")
            f1.write(f"Word Count: {self.word_count}\n\n")

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

    def get_prev_urls(self):
        return self.all_page_data.keys()

    def get_prev_url_data(self, url):
        return self.all_page_data[url]

    def get_unique_pages(self):
        return self.unique_pages

    def get_ics_subdomains(self):
        return self.ics_subdomains

    def get_ics_subdomain_count(self):
        return len(self.ics_subdomains)  # len(dict) returns the amount of keys, right?

    def get_word_count(self):
        return self.word_count

    def get_longest_page_count(self):
        return self.longest_page[1]

    def hasher(self, word):
        return self._hasher.get_hash(word)

    def get_longest_page_url(self):
        return self.longest_page[0]

    def get_all_words(self, content):
        """Returns a dictionary of all the words in the content and their frequency."""
        word_dict = {}
        for word in content:
            if word not in self.stopwords:
                if word in word_dict:
                    word_dict[word] += 1
                else:
                    word_dict[word] = 1
        return word_dict

    def compare_bits(self, bit_str: str, url) -> bool:
        """
        Compares the content of the current document to the content of the other documents via bits
        :param bit_str: string of bits for easy document storage
        :return: bool if the document is similar to another document
        """
        if len(self.documents) == 0:
            # inital case and add reversed bits
            self.documents[bit_str] = url
            return False
        else:
            for other_bit_str in self.documents.keys():
                count = 0
                print(f"comparing {bit_str} to {other_bit_str}")
                for bit1, bit2 in zip(bit_str, other_bit_str):
                    if bit1 == bit2:
                        # If bits are equivalent, increment count
                        count += 1
                similarity_ratio = count / 64
                print("SIMILARITY = ", similarity_ratio)
                # If the similarity ratio is greater than or equal to 0.9, return True
                if similarity_ratio >= 0.9:
                    print("\n\nSimilar to ", self.documents[other_bit_str])
                    return True
            self.documents[bit_str] = url
            print(f'\n\nTHIS IS THE BITS {self.documents}\n\n')
            return False

    def get_50_most_common_words(self):
        # Returns a sorted dict starting from the most common word
        self.remove_stopwords()
        return dict(sorted(self.word_count.items(), key=lambda item: item[1], reverse=True)[:50])
