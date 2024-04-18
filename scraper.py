import re
from urllib.parse import urlparse, urlunparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser as RobotParser
from bs4 import BeautifulSoup, SoupStrainer
import lxml
import time


def count_page_words(url, soup, counter_object):
    # Count the words in the page
    text = soup.get_text()
    words = re.findall(r'\w+', text.lower())
    word_count = len(words) # Increment the word count
    counter_object.increment_words(words)

    # Check if the page is the longest page
    if word_count > counter_object.get_longest_page_count():
        counter_object.set_longest_page(url, word_count)
    return


def count_if_ics_subdomain(url, counter_object):
    # Count the number of pages that are in the ics subdomain
    parsed = urlparse(url)
    if parsed.netloc.endswith(".ics.uci.edu"):
        counter_object.increment_ics_subdomains(parsed.netloc)
    return


### robot parser
def can_parse(url) -> bool:
    '''
    Gets the url and checks its robot.txt to see if we are allowed to crawl :emoji_face:

    :param url -> namedTuple a url that is parsed through urlparse
    :return: bool of whether the crawler is allowed to search the url

    '''
    allowed_net_locs = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    print("/t this is the url: ", url)
    try:
        robot_parse = RobotParser()
        parsed_url = urlparse(url)
        print(parsed_url)
        robots_url = parsed_url.scheme + "://" + parsed_url.netloc + "/robots.txt"
        robot_parse.set_url(robots_url)
        robot_parse.read()
        return robot_parse.can_fetch("*", url) and any(net_loc in parsed_url.netloc for net_loc in allowed_net_locs)
    except ValueError:
        return False



def scraper(url, resp, counter_object):
    # TODO: I think we should use can_parse() here instead of inside is_valid()
    links = extract_next_links(url, resp, counter_object)
    links = [link for link in links if is_valid(link)]
    links = list(set(urldefrag(link).url for link in links))
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
    if resp.error is None: # Hard coding case where the url status is OK
        if 200 <= resp.status < 300:
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')
            count_page_words(url, soup, counter_object) # Count the words in the page, also checks if it's the longest page
            for tag in soup.find_all():
                if 'href' in tag.attrs:
                    link = tag['href'].lower()
                    link = urljoin(url, link)
                    if is_valid(link):
                        links.add(link)
                        print(f'Linked added successfully! {link}')
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
        if can_parse(url): # TODO: can_parse() def should go AFTER this following check to make sure it's a webpage
            if not any(domain in parsed.netloc for domain in
                       [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]):
                return False
            return not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise