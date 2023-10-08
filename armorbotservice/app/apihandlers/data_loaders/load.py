import requests
import langchain.text_splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import WebBaseLoader, UnstructuredHTMLLoader


class MultiTypeDataLoader:
    def load_data_source(self) -> dict:
        """Load in the file for extracting text."""
        pass

    def pre_process_text(self) -> str:
        """filter input text from the currently loaded file if required"""
        pass


class WebProcessor(MultiTypeDataLoader):
    """Extract text from a website"""

    def __init__(self, source):
        self.docs = []
        self.source = source

    def load_data_source(self) -> any:
        """Overrides MultiTypeDataLoader.load_data_source()"""
        loader = WebBaseLoader(web_path=self.source)
        self.docs = loader.load()


    def pre_process_text(self) -> str:
        """Overrides MultiTypeDataLoader.pre_process_text()"""
        splitter = RecursiveCharacterTextSplitter.from_language(language=langchain.text_splitter.Language.HTML,
                                                                chunk_size=700, chunk_overlap=20)
        self.docs = splitter.split_documents(self.docs)
        print("total number of chunks:", len(self.docs))


class RawHTMLProcessor(MultiTypeDataLoader):
    """Extract text from raw html bytes"""
    def __init__(self, source):
        self.docs = []
        self.source = source

    def load_data_source(self) -> any:
        """Overrides MultiTypeDataLoader.load_data_source()"""
        # url = "https://en.wikipedia.org/wiki/List_of_Marvel_Cinematic_Universe_television_series"
        try:
            response = requests.get(self.source)
            response.raise_for_status()  # Raise an exception for unsuccessful requests
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)
        html_body = response.content
        loader = UnstructuredHTMLLoader(html_body)
        self.docs = loader.load()

    def pre_process_text(self) -> str:
        """Overrides MultiTypeDataLoader.pre_process_text()"""
        # @TODO: Will think over the chunk logic here and remove extra newlines and chars
        splitter = RecursiveCharacterTextSplitter.from_language(language=langchain.text_splitter.Language.HTML,
                                                                chunk_size=700, chunk_overlap=20)
        self.docs = splitter.split_documents(self.docs)
        print("total number of chunks:", len(self.docs))
