import re
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser as RobotParser
from urllib.error import URLError
from bs4 import BeautifulSoup
from ssl import SSLCertVerificationError

TEN_MB = 10 * 1024 * 1024
WORD_REGEX = re.compile(r"\b[a-zA-Z\’'.0-9]+\b")


def get_text(resp) -> list:
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    for script in soup(["script", "style"]):
        script.decompose()
    text = ' '.join(soup.stripped_strings)
    all_words = [match.group() for match in WORD_REGEX.finditer(text.lower()) if match.group() != '.']
    return all_words


def save_page_data(resp, counter_object) -> None:
    # Save data for server statistics
    words = get_text(resp)
    word_count = len(words)  # Increment the word count
    counter_object.add_new_page(resp.url)
    counter_object.increment_words(words)

    # Check if the page is the longest page
    if word_count > counter_object.get_longest_page_count():
        counter_object.set_longest_page(resp.url, word_count)


def count_if_ics_subdomain(resp, counter_object) -> None:
    # Count the number of pages that are in the ics subdomain
    parsed = urlparse(resp.url)
    if parsed.netloc.endswith("ics.uci.edu"):
        counter_object.increment_ics_subdomains(parsed.netloc)


def can_parse(url) -> tuple[bool, list | None]:
    """
    Gets the url and checks its robot.txt to see if we are allowed to crawl :emoji_face:

    :param url -> namedTuple a url that is parsed through urlparse
    :return: bool of whether the crawler is allowed to search the url

    """
    allowed_net_locs = ["ics.uci.edu", ".cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    try:
        parsed_url = urlparse(url)
        if not any(net_loc in parsed_url.netloc for net_loc in allowed_net_locs):
            if not parsed_url.netloc.startswith("cs.uci.edu"):  # special case for eecs, cecs, etc.
                return False, None
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        robot_parse = RobotParser()
        robot_parse.set_url(robots_url)
        robot_parse.read()
        return robot_parse.can_fetch("*", url), robot_parse.site_maps()
    except (URLError, SSLCertVerificationError) as e:
        print(f"\n\ni errored {e}\n\n")
        return False, None


def too_similar(resp, counter_object) -> bool:
    """
    Checks if the page is too similar to another page
    :param resp:
    :param counter_object:
    :return: bool
    """
    # takes out the script and style tags
    if resp.error is not None:
        return False
    else:
        if resp.status >= 300 or resp.status < 200:
            return False
    words = get_text(resp)
    word_dict = counter_object.get_all_words(words)
    # hash all words
    hash_dict = {word: counter_object.hasher(word) for word in word_dict.keys()}
    summed_hashes = []
    # now count the hashes and form the vectors
    for i in range(63, -1, -1):
        # from every bit of every word
        the_hash = 0
        bitmask = 1 << i
        for word, hash_value in hash_dict.items():
            bit_value = (hash_value & bitmask) >> i
            if bit_value == 0:
                the_hash -= word_dict[word]  # if the bit is 0, subtract the word count
            else:
                the_hash += word_dict[word]  # if the bit is 1, add the word count
        summed_hashes.append(the_hash)

    bit_rep = [1 if nums > 0 else 0 for nums in summed_hashes]
    bit_str = ''.join(map(str, bit_rep))

    return counter_object.compare_bits(bit_str)


def scraper(url, resp) -> list:
    links = extract_next_links(url, resp)
    if not links:
        return []
    return links


def extract_next_links(url, resp) -> list:
    links = set()
    if resp.error is None:  # Hard coding case where the url status is OK
        if 200 <= resp.status < 300:
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')

            total_words = get_text(resp)
            unique_words = set(total_words)

            if len(total_words) > TEN_MB:  # Check if the page is too big
                print("\n\nit's too big tbh\n\n")
                return []

            if len(unique_words) < 100:  # low textual information
                print("\n\nnot enough text\n\n")
                return []

            # Extract the links from the page
            for tag in soup.find_all('a'):
                if 'href' in tag.attrs:
                    link = tag['href'].lower()
                    link = urldefrag(urljoin(resp.url, link)).url
                    # check if valid link
                    if link in links or not link:
                        continue
                    valid, sitemap = can_parse(link)  # robots.txt check
                    if valid and is_valid(link):
                        if sitemap is not None and sitemap not in links:
                            links.add(sitemap)
                        links.add(link)
        else:
            print(f'Error: Unexpected HTTP status code {resp.status} for URL {url}')
    else:
        print(f'Error: Request error for URL {url}: {resp.error}')

    return list(links)


def is_valid(url) -> bool:
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if 'embed' in parsed.path.lower():  # Check if 'embed?url' is present in the query string
            return False
        if 'wp-json' in parsed.path.lower():  # check for json websites
            return False
        if '\\' in parsed.path.lower():  # check for weird escape symbol urls
            return False
        if "php" in parsed.path.lower():  # php checking but re.match might already do this
            return False
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
            return True
    except TypeError or URLError:
        print("TypeError for ", parsed)
