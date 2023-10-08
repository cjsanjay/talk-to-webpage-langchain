"""
Module for Generating the index
"""
import io

import PyPDF2
import requests
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.docstore.document import Document
from .data_loaders import load
from .util import encode_url, encode_url_scrapped

import os
import pinecone
import threading

import requests
from bs4 import BeautifulSoup
import validators
from urllib.parse import urlparse

GREQUEST_BATCH = 20


def pine_db_handler(docs, embedding, namespace):
    """

    :param docs:
    :param embedding:
    :param namespace:
    :return:
    """
    # inserting in pineconedb using url from webloader metadata.
    Pinecone.from_documents(docs, embedding, index_name=os.environ['PINECONE_INDEX_NAME'], namespace=namespace)


def check_namespace_exists(ns):
    """

    :param ns:
    :return:
    """
    # Initializing pinecone env / creds
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENVIRONMENT_REGION"],
    )
    index = pinecone.Index(os.environ['PINECONE_INDEX_NAME'])
    index_stats_response = index.describe_index_stats()
    if ns in index_stats_response['namespaces']:
        return True
    else:
        return False


def process_and_insert_to_pinecone(namespace, page_url, page_content=""):
    """

    :return:
    """
    if page_url.endswith(".pdf"):
        r = requests.get(page_url)
        f = io.BytesIO(r.content)

        reader = PyPDF2.PdfReader(f)
        plain_text = reader.pages[2].extract_text()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=20,
            length_function=len,
        )
        data = text_splitter.split_text(plain_text)
        docs = [Document(page_content=t) for t in data]
    elif page_content != "":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=20,
            length_function=len,
        )
        data = text_splitter.split_text(page_content)
        docs = [Document(page_content=t) for t in data]
    else:
        web_process = load.WebProcessor(page_url)
        web_process.load_data_source()
        web_process.pre_process_text()
        docs = web_process.docs

    # Initialized the embedding to use.
    # This also requires the OPEN_API_KEY SET if using OpenAIEmbeddings()
    embedding = OpenAIEmbeddings()

    # chroma_db_handler(docs=web_process.docs, embedding=embedding)
    pine_db_handler(docs=docs, embedding=embedding, namespace=namespace)


class NewThreadedTask(threading.Thread):
    page_url = ""
    logger = None

    def __init__(self, page_url, logger, page_content):
        self.page_url = page_url
        self.page_content = page_content
        self.logger = logger
        super(NewThreadedTask, self).__init__()

    def run(self):
        ns = encode_url(self.page_url)
        if check_namespace_exists(ns):
            self.logger.info(f"Namespace already existing in PineConeDb: {ns}")
            return
        process_and_insert_to_pinecone(ns, self.page_url, self.page_content)
        self.logger.info(f"Generated pinecone db index: {ns}")


class NewScrappingThreadedTask(threading.Thread):
    page_url = ""
    logger = None

    def __init__(self, page_url, logger):
        self.page_url = page_url
        self.logger = logger
        super(NewScrappingThreadedTask, self).__init__()

    def get_text_chunks_langchain(self, page_blob_txt):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=20,
            length_function=len,
        )
        data = text_splitter.split_text(page_blob_txt)
        docs = [Document(page_content=t) for t in data]
        return docs

    def run(self):
        ns = encode_url_scrapped(self.page_url)
        try:
            if check_namespace_exists(ns):
                self.logger.info(f"Namespace already existing in PineConeDb: {ns}")
                return
        except Exception as ex:
            self.logger.warn(f"failed to check for namespace existence: {os.environ['PINECONE_INDEX_NAME']}, error: {str(ex)}")
        page_blob_txt = self.scrap_page_and_return_txt_blob_content()
        docs = self.get_text_chunks_langchain(str(page_blob_txt))

        # Initialized the embedding to use.
        # This also requires the OPEN_API_KEY SET if using OpenAIEmbeddings()
        embedding = OpenAIEmbeddings()

        # chroma_db_handler(docs=web_process.docs, embedding=embedding)
        pine_db_handler(docs=docs, embedding=embedding, namespace=ns)
        self.logger.info(f"Generated pinecone db scrapped index: {ns}")

    def scrap_page_and_return_txt_blob_content(self):
        """

        :param page_url:
        :return:
        """
        hostname = urlparse(self.page_url).hostname
        page = requests.get(self.page_url, timeout=10)

        final_response = str(page.content)
        soup = BeautifulSoup(page.content, 'html.parser')

        target_links = [link.get('href') for link in soup.find_all('a')]

        final_target_link = []
        for link in target_links:
            if link is not None:
                if not validators.url(link):
                    final_target_link.append(f"https://{hostname}{link}")
                else:
                    final_target_link.append(link)

        self.logger.info(final_target_link)
        total = len(final_target_link)
        done = 0
        pages = (requests.get(url, timeout=10) for url in set(final_target_link))
        for res in pages:
            try:
                final_response += str(res.content)
                done += 1
            except AttributeError as ex:
                self.logger.warn(f"Failed to process one of the URLs: {ex}")
                continue
            self.logger.info(f"Done: {done}/{total}")
        return final_response


def generate_index_handler(logger, page_content, page_url):
    """
    Generate the index given a page URL

    :param page_content:
    :param page_url:
    :return:
    """
    new_thread = NewThreadedTask(page_url, logger, page_content)
    new_thread.start()
    logger.info(f"Triggered the indexing task for page: {page_url}")
    return {"response": True}


def generate_scrap_index_handler(logger, page_url):
    """

    :param logger:
    :param page_url:
    :param namespace:
    :return:
    """
    new_thread = NewScrappingThreadedTask(page_url, logger)
    new_thread.start()
    logger.info(f"Triggered the scrapping indexing task for page: {page_url}")
    return {"response": True}


def clean_up_index_handler(logger):
    """
    Clean up the indexes in Pinecone

    :param logger:
    :return:
    """
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENVIRONMENT_REGION"],
    )
    index = pinecone.Index(os.environ['PINECONE_INDEX_NAME'])
    index_stats_response = index.describe_index_stats()
    count = 0
    for namespace in index_stats_response["namespaces"]:
        logger.info(f"Deleting namespace: {namespace}")
        index.delete(delete_all=True, namespace=namespace)
        count += 1
    logger.info(f"Deleted {count} namespaces")
    return {"response": True}
