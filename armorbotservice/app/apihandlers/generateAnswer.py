"""
Module for Generating the Answer for the question text
"""
import os
from .generateIndex import check_namespace_exists, process_and_insert_to_pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import Pinecone
import pinecone
from .util import encode_url, encode_url_scrapped

pinecone_key = str(os.getenv('PINECONE_API_KEY'))
pinecone_region = str(os.getenv('PINECONE_ENVIRONMENT_REGION'))


def generate_answer_handler(logger, question_text, page_url, chat_history, is_scrapped=False):
    """
    Generate the answer for the given question text

    :param question_text:
    :param page_url:
    :param chat_history: array of arrays with format: [[prompt, answer], [prompt, answer]]
    :return:
    """
    # pinecone.init(
    #     api_key=pinecone_key,
    #     environment=pinecone_region
    # )
    # Convert the chat_history into chat_history_tuples
    # Store only 5 tuples in chat_history_tuples
    chat_history_tuples = []
    count = 0
    for history in reversed(chat_history):
        if len(history) >= 2:
            chat_history_tuples.append((history[0], history[1]))
            count = count + 1
        if count == 5:
            break

    # Sample output of chat_history_tuples
    # chat_history_tuples: [('What is the state of patna?', 'Patna is the capital city of the state of Bihar in India.')
    # ,('What is the population of patna?', 'The estimated population of Patna in 2011 was 1.68 million.'),
    # ('What is the River in patna?', 'The city of Patna is bounded by four interlinked rivers.')]
    logger.info(f"chat_history_tuples: {chat_history_tuples}")
    namespace = encode_url(page_url)
    if is_scrapped:
        namespace_scrapped = encode_url_scrapped(page_url)
        if check_namespace_exists(ns=namespace_scrapped):
            namespace = namespace_scrapped

    embeddings = OpenAIEmbeddings()

    if not check_namespace_exists(ns=namespace):
        process_and_insert_to_pinecone(namespace=namespace, page_url=page_url)

    doc_search = Pinecone.from_existing_index(os.environ['PINECONE_INDEX_NAME'], embedding=embeddings,
                                              namespace=namespace)
    chat = ChatOpenAI(verbose=True, temperature=0)

    qa = ConversationalRetrievalChain.from_llm(llm=chat, retriever=doc_search.as_retriever())
    response = qa({"question": question_text, "chat_history": chat_history_tuples})["answer"]
    logger.info(f"Generated answer for page: {page_url}, answer length: {response}")
    return {"response": response}
