import re
from urllib.parse import urlparse, urlunparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser as RobotParser
from urllib.error import URLError
from bs4 import BeautifulSoup, SoupStrainer
from ssl import SSLCertVerificationError
from difflib import SequenceMatcher
import lxml
import time


def bad_size(url): # TODO: Haven't implemented yet, but want to put it in can_parse() once we move that func
    # Returns True if the file is too big or empty, else False
    MAX_FILE_SIZE = 10 * 1024 * 1024 # == 10mb
    # TODO: Get content length of the page in mb
    # TODO: Find a way to check if the information is of low or high value
    content_length = len(url) # Placeholder for now
    if content_length > MAX_FILE_SIZE:
        return True

    # TODO: Check if the file is empty
    if content_length == 0 or len(url.title) == 0: # Placeholder for now
        return True
    return False


def save_page_data(url, soup, counter_object):
    # Count the words in the page
    # TODO: check if this saves correctly and save locally
    text = soup.get_text()
    words = re.findall(r"\b[\w\’\.\']+\b", text.lower())
    word_count = len(words) # Increment the word count
    counter_object.add_new_page(url, words)
    counter_object.increment_words(words)

    # Check if the page is the longest page
    if word_count > counter_object.get_longest_page_count():
        counter_object.set_longest_page(url, word_count)


def count_if_ics_subdomain(url, counter_object):
    # Count the number of pages that are in the ics subdomain
    # TODO: check if this saves correctly and save locally
    parsed = urlparse(url)
    if parsed.netloc.endswith(".ics.uci.edu"):
        counter_object.increment_ics_subdomains(parsed.netloc)


def can_parse(url) -> bool:
    """
    Gets the url and checks its robot.txt to see if we are allowed to crawl :emoji_face:

    :param url -> namedTuple a url that is parsed through urlparse
    :return: bool of whether the crawler is allowed to search the url

    """
    allowed_net_locs = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    try:
        robot_parse = RobotParser()
        parsed_url = urlparse(url)
        print(parsed_url)
        if (not any(net_loc in parsed_url.netloc for net_loc in allowed_net_locs)):
            return False
        robots_url = parsed_url.scheme + "://" + parsed_url.netloc + "/robots.txt"
        robot_parse.set_url(robots_url)
        robot_parse.read()
        return robot_parse.can_fetch("*", url)
    except URLError or SSLCertVerificationError:
        print("\n\ni errored\n\n")
        return False

def too_similar(soup, counter_object) -> bool:
    content = soup.get_text().strip().split()
    # then you wanna group some words together and make them tokens, let's do this word by word
    # group them by threes
    # tokenize with weights
    word_dict = counter_object.get_all_words(content)

    # hash all words
    hash_dict = {}
    # give them
    for words in word_dict.keys():
        hashed = hash(words)
        hashed = hashed & 0xFFFF
        hash_dict[words] = hashed

    summed_hashes = []
    # now count the hashes and form the vectors
    for i in range(16, -1, -1):
        # from every bit of every word
        hash = 0
        bitmask = 1 << i
        for word, hash_value in hash_dict.items():
            bit_value = (hash_value & bitmask) >> i
            if bit_value == 0:
                hash -= word_dict[word]
            else:
                hash += word_dict[word]
        summed_hashes.append(hash)

    bit_rep = []
    for nums in summed_hashes:
        if nums > 0:
            bit_rep.append(1)
        else:
            bit_rep.append(0)

    return counter_object.compare_bits(bit_rep)

def scraper(url, resp, counter_object):
    print(f'\n\nTIME TO SCRAPE!!\n\n')
    links = extract_next_links(url, resp, counter_object)
    if not links:
        return []
    links = list(set(urldefrag(link).url for link in links)) # defraged url!

#    for link in links[:]: TODO: This will be where we check bad_size() once we finish it
#        if bad_size(link):
#            links.remove(link)
#            print(f'\n\nLink is bad size: {link}\n\n')

    # TODO: check if this saves correctly and save locally
    counter_object.increment_unique_pages() # Word counting is done within extract_next_links()
    count_if_ics_subdomain(url, counter_object)
    # TODO MAYBE: Save the URL and webpage on the local disk
    return links


def extract_next_links(url, resp, counter_object):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = set()
    """ TODO: if the website is taking forever to load, we should just leave it
    -   thinking of just setting a timer and if it overlaps"""
    if resp.error is None: # Hard coding case where the url status is OK
        if 200 <= resp.status < 300:
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')

            if too_similar(soup, counter_object): # Check if the page is too similar to another page before reading it
                return links

            save_page_data(resp.url, soup, counter_object) # Count the words in the page, also checks if it's the longest page

            for tag in soup.find_all():
                if 'href' in tag.attrs:
                    link = tag['href'].lower()
                    link = urljoin(resp.url, link)
                    if is_valid(link): # checking for similarities
                        links.add(link)
                        print(f'Linked added successfully! {link}')
                    else:
                        print(f'\n\nLink not valid {link}\n\n')
        else:
            print(f'Error: Unexpected HTTP status code {resp.status} for URL {url}')
    else:
        print(f'Error: Request error for URL {url}: {resp.error}')

    return list(links)


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if 'embed' in parsed.path.lower():  # Check if 'embed?url' is present in the query string
            return False
        if 'wp-json' in parsed.path.lower(): # check for json websites
            return False
        if '\\' in parsed.path.lower(): # check for weird escape symbol urls
            return False
        if "php" in parsed.path.lower(): # php checking but re.match might already do this
            return False
            # louie deleted cus I already check it in can_parse
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|php|json)$", parsed.path.lower()):
            return False
        else:
            return can_parse(url)

    except TypeError or URLError:
        print ("TypeError for ", parsed)