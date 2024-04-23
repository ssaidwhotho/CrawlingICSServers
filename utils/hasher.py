class Hash:
    """Hashes a word and returns the hash value. If the word has already been hashed, it returns the hash value."""
    def __init__(self):
        self.hash_dict = {}

    def get_hash(self, word):
        if word in self.hash_dict:
            return self.hash_dict[word]
        else:
            self.hash_dict[word] = hash(word) & 0xFFFF
            return self.hash_dict[word]

    def get_all_hashes(self):
        return self.hash_dict

