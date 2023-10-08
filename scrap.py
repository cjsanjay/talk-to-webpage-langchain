import requests
from bs4 import BeautifulSoup
import validators
from urllib.parse import urlparse


def scrap_page_and_return_txt_blob_content(page_url):
    """

    :param page_url:
    :return:
    """
    hostname = urlparse(page_url).hostname
    page = requests.get(page_url)

    final_response = page.content
    soup = BeautifulSoup(page.content, 'html.parser')

    target_links = [link.get('href') for link in soup.find_all('a')]

    final_target_link = []
    for link in target_links:
        if link is not None:
            if not validators.url(link):
                final_target_link.append(f"https://{hostname}{link}")
            else:
                final_target_link.append(link)

    print(final_target_link)
    total = len(final_target_link)
    done = 0
    pages = (requests.get(url) for url in set(final_target_link))
    for res in pages:
        try:
            final_response += res.content
            done += 1
        except AttributeError as ex:
            print(f"Failed to process one of the URLs: {ex}")
            continue
        print(final_response)
        print(f"Done: {done}/{total}")

scrap_page_and_return_txt_blob_content("https://www.cisco.com/c/en/us/tech/ip/ip-addressing-services/tsd-technology-support-troubleshooting-technotes-list.html")