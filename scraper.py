import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import variables
import similarity

#Report data: unique pages, longest page, word counts, subdomains
unique_pages = set()  #defragmented URLs
longest_page_url = ""  #URL of page with most words
longest_page_count = 0  #word count of longest page
word_counts = {}  #50 most common words
subdomains = {}  #subdomains with page counts

_page_count = 0  # track how many pages we've processed

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

    # Abubakr and Adan worked on this function together

    # Only handle successful responses with a real response body that isn't empty, None, or False
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

    # Current page URL that the crawler is on, it will turn short links into full URLs which is important
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

    # Decode the bytes and turn it into a string so that the crawler can parse HTML
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

    # Parse HTML with Beautiful Soup
    try:
        soup = BeautifulSoup(content, "lxml")
    except Exception:
        return []

    # Skip exact or near-duplicate pages (extra credit) to improve effiency
    text = soup.get_text(separator=" ", strip=True)
    if similarity.is_duplicate_page(text):
        return []

    # Record this page for the report (unique pages, longest page, subdomains)
    global _page_count
    _page_count += 1

    page_url_defrag, _ = urldefrag(base_url)
    unique_pages.add(page_url_defrag)
    
    # Get subdomain (netloc) for subdomain counts
    parsed = urlparse(page_url_defrag)
    subdomain = (parsed.netloc or "").lower()
    if subdomain:
        if subdomain not in subdomains:
            subdomains[subdomain] = set()
        subdomains[subdomain].add(page_url_defrag)

    # Count words (ignore stop words) for the report that will be made
    try:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        total_words = len(words)  # all words (for longest page)
        if total_words > longest_page_count:
            longest_page_url = page_url_defrag
            longest_page_count = total_words
        for w in words:
            if w and w not in variables.stop_words:
                word_counts[w] = word_counts.get(w, 0) + 1
    except Exception:
        pass

    # Print and save report progress every 10 pages
    print_and_save_report()

    out_list = []   # links we will return which is one per URL from this page
    seen_set = set()  # URLs we already added from this page, skipping duplicates within the same page to maximize efficiency
    
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href:
            continue

        # Skip non-page links (javascript, mailto, etc.)
        href_l = href.lower()
        if href_l.startswith(("javascript:", "mailto:", "tel:", "data:")) or href_l.startswith("#"):
            continue

        # Make it an absolute URL and remove the fragment
        try:
            absolute = urljoin(base_url, href)
        except Exception:
            continue
        absolute, _ = urldefrag(absolute)
        absolute = absolute.strip()

        # Make sure there are no empty or duplicate links
        if not absolute or absolute in seen_set:
            continue

        seen_set.add(absolute)
        out_list.append(absolute)

    return out_list

def print_and_save_report():
    '''Print and save the 4 report metrics to report.txt'''
    global _page_count

    # Only print/save every 10 pages to avoid too much output
    if _page_count % 10 != 0:
        return

    # 1. Unique pages count
    unique_count = len(unique_pages)

    # 2. Longest page
    longest_info = f"{longest_page_url} ({longest_page_count} words)" if longest_page_url else "None yet"

    # 3. Top 50 words (excluding stop words)
    top50 = sorted(word_counts.items(), key=lambda x: (-x[1], x[0]))[:50]
    top50_str = "\n   ".join([f"{i+1:2}. {word}: {count}" for i, (word, count) in enumerate(top50)])

    # 4. Subdomains (alphabetically) with counts
    subdomain_list = sorted([(k, len(v)) for k, v in subdomains.items()])
    subdomain_str = "\n   ".join([f"{subdomain}, {count}" for subdomain, count in subdomain_list])

    report_text = f"""
        CRAWLER REPORT (as of {_page_count} pages processed)
        {'='*60}

        1. Unique pages (by URL, fragment discarded): {unique_count}

        2. Longest page (by word count, HTML not counted):
        {longest_info}

        3. Top 50 most common words (excluding stop words), by frequency:
        {top50_str if top50_str else '   (none yet)'}

        4. Subdomains in uci.edu (alphabetically), with unique page count:
        {subdomain_str if subdomain_str else '   (none yet)'}

        {'='*60}
        """

    print(report_text)

    # Save to file
    try:
        with open("report.txt", "w", encoding="utf-8") as f:
            f.write(report_text)
    except Exception:
        pass

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

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
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", path)

    except TypeError:
        print ("TypeError for ", parsed)
        raise
