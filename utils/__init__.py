import os
import logging
from hashlib import sha256
from urllib.parse import urlparse

def get_logger(name, filename=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    fh = logging.FileHandler(f"Logs/{filename if filename else name}.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
       "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def get_urlhash(url):
    parsed = urlparse(url)
    # everything other than scheme.
    return sha256(
        f"{parsed.netloc}/{parsed.path}/{parsed.params}/"
        f"{parsed.query}/{parsed.fragment}".encode("utf-8")).hexdigest()

def normalize(url):
    if url.endswith("/"):
        return url.rstrip("/")
    return url


# Levenshtein Distance via wikipedia pseudocode https://en.wikipedia.org/wiki/Levenshtein_distance
def levenstein_distance(url1, url2) -> int:
    """
    Calculate the Levenshtein distance between two urls.
    :param url1:
    :param url2:
    :return: int
    """
    matrix = [[0 for _ in range(len(url2) + 1)] for _ in range(len(url1) + 1)]
    for i in range(len(url1) + 1):
        matrix[i][0] = i
    for j in range(len(url2) + 1):
        matrix[0][j] = j
    for i in range(1, len(url1) + 1):
        for j in range(1, len(url2) + 1):
            if url1[i - 1] == url2[j - 1]:
                cost = 0
            else:
                cost = 1
            matrix[i][j] = min(matrix[i - 1][j] + 1,
                               matrix[i][j - 1] + 1,
                               matrix[i - 1][j - 1] + cost)

    return matrix[len(url1)][len(url2)]


def similarity_score(url1, url2) -> float:
    """Calculate the similarity score between two URLs. via Levenshtein distance"""
    url1 = urlparse(url1)
    url2 = urlparse(url2)

    if url1.netloc != url2.netloc:
        return 0

    path_score = levenstein_distance(url1.path, url2.path)
    query_score = levenstein_distance(url1.query, url2.query)

    max_path_length = max(len(url1.path), len(url2.path))
    max_query_length = max(len(url1.query), len(url2.query))
    max_distance = max(max_path_length, max_query_length)
    if max_distance == 0:
        return 1

    return 1 - ((path_score + query_score) / 2) / max_distance
