import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser as RobotParser
from bs4 import BeautifulSoup, SoupStrainer
import lxml



### robot parser
def can_parse(url) -> bool:
    '''
    Gets the url and checks its robot.txt to see if we are allowed to crawl :emoji_face:

    :param url -> namedTuple a url that is parsed through urlparse
    :return: bool of whether the crawler is allowed to search the url

    '''
    allowed_net_locs = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    robot_parse = RobotParser()
    robots_url = url.scheme + "://" + url.netloc + "/robots.txt"
    robot_parse.set_url(robots_url)
    robot_parse.read()
    return robot_parse.can_fetch("*", url) and url.netloc in allowed_net_locs



def scraper(url, resp):
    # TODO: Add a check to make sure that we are allowed to check the url
    links = extract_next_links(url, resp)
    links = [link for link in links if is_valid(link)]
    # TODO: Remove the fragment part of the URL (ie: the #bbb in http://www.ics.uci.edu#bbb)
    #  urllib.parse.urldefrag(url)¶
    return links

def extract_next_links(url, resp):
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
            for tag in soup.find_all():
                if 'href' in tag.attrs:
                    link = tag['href'].lower()
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
        if can_parse(url):
            return not re.match( # TODO: Change this to only allow *.ics.uci.edu/*, *.cs.uci.edu/*, *.informatics.uci.edu/*, *.stat.uci.edu/*
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                # specifc to ics
                # + r"|ics|cs|informatics|stat)\.uci\.edu"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
