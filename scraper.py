import re
from urllib.parse import urlparse, urlunparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser as RobotParser
from urllib.error import URLError
from bs4 import BeautifulSoup, SoupStrainer
from ssl import SSLCertVerificationError
from difflib import SequenceMatcher
import lxml
import time


def bad_size(soup): # TODO: Haven't implemented yet, but want to put it in can_parse() once we move that func
    # Returns True if the file is too big or empty, else False
    MAX_FILE_SIZE = 10 * 1024 * 1024 # == 10mb
    # TODO: Get content length of the page in mb
    # TODO: Find a way to check if the information is of low or high value
    content_length = len(soup.body) # NOT SURE IF THIS WORKS TBH
    if content_length > MAX_FILE_SIZE:
        return True

    # TODO: Check if the file is empty
    if content_length == 0 or len(soup.title) == 0:
        return True
    return False


# def similarity_score(a, b): # A similarity checker I found online that might work
#     from difflib import SequenceMatcher
#     return SequenceMatcher(None, a, b).ratio()

#
# def too_similar(soup, visited_contents): # Return True if the page is too similar to any prev. page
#     # TODO: Find a way to feed this function all the previously visited page contents.
#
#     if any(similarity_score(soup, visited_content) > 0.9 for visited_content in visited_contents): # 0.9 is 90% similar
#         return True
#     return False


def count_page_words(url, soup, counter_object):
    # Count the words in the page
    text = soup.get_text()
    words = re.findall(r'\w+', text.lower())
    word_count = len(words) # Increment the word count
    counter_object.increment_words(words)

    # Check if the page is the longest page
    if word_count > counter_object.get_longest_page_count():
        counter_object.set_longest_page(url, word_count)


def count_if_ics_subdomain(url, counter_object):
    # Count the number of pages that are in the ics subdomain
    parsed = urlparse(url)
    if parsed.netloc.endswith(".ics.uci.edu"):
        counter_object.increment_ics_subdomains(parsed.netloc)


### robot parser
def can_parse(url) -> bool:
    '''
    Gets the url and checks its robot.txt to see if we are allowed to crawl :emoji_face:

    :param url -> namedTuple a url that is parsed through urlparse
    :return: bool of whether the crawler is allowed to search the url

    '''
    allowed_net_locs = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    # print("\t this is the url: ", url)
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

def url_similarity(url1, url2):
    # Parse the URLs
    parsed_url1 = urlparse(url1)
    parsed_url2 = urlparse(url2)

    # Calculate similarity for each component of the URLs
    domain_similarity = SequenceMatcher(None, parsed_url1.netloc, parsed_url2.netloc).ratio()
    path_similarity = SequenceMatcher(None, parsed_url1.path, parsed_url2.path).ratio()
    query_similarity = SequenceMatcher(None, parsed_url1.query, parsed_url2.query).ratio()

    # Calculate overall similarity as an average of component similarities
    overall_similarity = (domain_similarity + path_similarity + query_similarity) / 3

    return overall_similarity

def get_rid_of_similars(links: list):
    n = len(links)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if (url_similarity(links[i], links[j])) > 0.9:
                print(f"\n\ni'm deleting one of the urls: {links[j]}\n\n")
                del links[j]
                n -= 1
            else:
                j += 1
        i += 1


def scraper(url, resp, counter_object):
    print(f'\n\nTIME TO SCRAPE!!\n\n')
    # TODO: I think we should use can_parse() here instead of inside is_valid()
    links = extract_next_links(url, resp, counter_object)
    # got rid of extra is valid check since we call it in extract_next_links
    print("\n\nTIME TO GET RID OF SIMILAR LINKS!\n\n")
    get_rid_of_similars(links)
    links = list(set(urldefrag(link).url for link in links)) # defraged url!
    counter_object.increment_unique_pages() # Word counting is done within extract_next_links()
    count_if_ics_subdomain(url, counter_object)
    # TODO MAYBE: Save the URL and webpage on the local disk
    # no
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
            count_page_words(resp.url, soup, counter_object) # Count the words in the page, also checks if it's the longest page
            for tag in soup.find_all():
                if 'href' in tag.attrs:
                    link = tag['href'].lower()
                    link = urljoin(resp.url, link)
                    if is_valid(link):
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
        if parsed.scheme not in set(["http", "https"]):
            return False
        if 'embed' in parsed.path:  # Check if 'embed?url' is present in the query string
            return False
        if 'json' in parsed.path: # check for json websites
            return False
        if '\\' in parsed.path: # check for weird escape symbol urls
            return False
        if can_parse(url): # TODO: can_parse() def should go AFTER this following check to make sure it's a webpage
            # louie deleted cus I already check it in can_parse
            return not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz|php|xml|json)$", parsed.path.lower())
        else:
            print("\n\nit failed i am the worst coder.\n\n")

    except TypeError or URLError:
        print ("TypeError for ", parsed)