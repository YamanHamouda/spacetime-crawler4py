import re
from urllib.parse import urlparse

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
    return list()

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        hostname = (parsed.hostname or "").lower().strip(".") #gets hostname stuffix - Yaman and Majd
        if not hostname:
            return False

        allowed_suffixes = ( #allowed suffixes - Yaman and Majd
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
        )
        #simply checks if the hostname end with any of the allowed suffixes - Yaman and Majd
        if not any(hostname == s or hostname.endswith(f".{s}") for s in allowed_suffixes):
            return False

        if parsed.port not in (None, 80, 443): #makes sure we're using web ports - Yaman and Majd
            return False

        path = (parsed.path or "/").lower() #gets path like /a/b/c/... - Yaman and Majd
        query = (parsed.query or "").lower() #gets query like ?a=b&c=d... - Yaman and Majd

        year = r"\d{4}"
        month_or_day = r"\d{1,2}"
        sep = r"[-_/]"
        date_segment = r"(?:^|/)" + year + sep + month_or_day + r"(?:" + sep + month_or_day + r")?(?:/|$)"
        if re.search(date_segment, path): #checks if the path contains a date but written with the help of ChatGPT - Yaman and Majd
            return False

        if re.search(r"[?&](page|p)=\d{4,}", query): #checks for pagination traps - Yaman and Majd
            return False

        if re.search(r"(admin|wiki)", parsed.path): #checks for admin and wiki pages/traps - Yaman and Majd
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
