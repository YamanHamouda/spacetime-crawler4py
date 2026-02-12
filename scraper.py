# scraper.py

import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import variables
import similarity

# Accumulates the word counts other than stop words for the report
word_counts = {}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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

    if not resp or not resp.raw_response:
        return []

    if resp.status != 200:
        return []

    raw = resp.raw_response
    try:
        content = raw.content
    except AttributeError:
        return []

    if not content:
        return []

    base_url = url
    try:
        if resp.url:
            base_url = resp.url

        if raw.url:
            base_url = raw.url
    except AttributeError:
        pass

    if not base_url:
        return []

    if isinstance(content, bytes):
        encoding = "utf-8"
        try:
            if raw.encoding:
                encoding = raw.encoding
        except AttributeError:
            pass

        try:
            content = content.decode(encoding, errors="replace")
        except Exception:
            content = content.decode("utf-8", errors="replace")

    if not isinstance(content, str):
        return []

    try:
        soup = BeautifulSoup(content, "lxml")
    except Exception:
        return []

    text = soup.get_text(separator=" ", strip=True)
    if similarity.is_duplicate_page(text):
        return []

    try:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        for w in words:
            if w and w not in variables.stop_words:
                word_counts[w] = word_counts.get(w, 0) + 1
    except Exception:
        pass

    out_list = []
    seen_set = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href:
            continue
        href_l = href.lower()
        if href_l.startswith(("javascript:", "mailto:", "tel:", "data:")) or href_l.startswith("#"):
            continue

        try:
            absolute = urljoin(base_url, href)
        except Exception:
            continue

        if "#" in absolute:
            absolute = absolute.split("#", 1)[0]
            
        absolute = absolute.strip()

        if not absolute or absolute in seen_set:
            continue

        seen_set.add(absolute)
        out_list.append(absolute)

    return out_list

# Only crawl: *.ics.uci.edu, *.cs.uci.edu, *.informatics.uci.edu, *.stat.uci.edu
ALLOWED_SUBLINK = (".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu")
ALLOWED_LINK = ("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu")

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        host = (parsed.netloc or "").lower()
        if not host:
            return False

        if host not in ALLOWED_LINK and not any(host.endswith(d) for d in ALLOWED_SUBLINK):
            return False

        path = (parsed.path or "/").lower()
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", path)

    except TypeError:
        print ("TypeError for ", parsed)
        raise
