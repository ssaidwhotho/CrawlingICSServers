class Hash:
    """Hash class that hashes words and stores them in a dictionary."""
    def __init__(self):
        self.hash_dict = {}

    def get_hash(self, word):
        if word in self.hash_dict:
            return self.hash_dict[word]
        else:
            self.hash_dict[word] = hash(word) & 0xFF
            return self.hash_dict[word]

    def get_all_hashes(self):
        return self.hash_dict

