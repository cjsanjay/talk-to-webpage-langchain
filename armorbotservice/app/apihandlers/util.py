import base64


def encode_url(page_url):
    """

    :param page_url:
    :return:
    """
    return base64.b64encode(page_url.encode("utf-8")).decode("utf-8")


def encode_url_scrapped(page_url):
    """

    :param page_url:
    :return:
    """
    return f"{base64.b64encode(page_url.encode('utf-8')).decode('utf-8')}-scrap"
