"""
Module for Generating the Summary
"""
from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import html2text
from sumy.nlp.stemmers import Stemmer
from sumy.parsers.plaintext import PlaintextParser
from sumy.utils import get_stop_words
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
import os
import re
import io
import openai
import PyPDF2
import requests
import urllib.request

LANGUAGE = "english"
SENTENCES_COUNT = 1000
openai.api_key = os.environ['OPENAI_API_KEY']


def get_completion_from_messages(trimmed_text="",
                                 model="gpt-3.5-turbo",
                                 temperature=0.0,
                                 max_tokens=1000):
    messages = [
        {'role': 'system',
         'content': """
         System output considerations:
         - We have ordered the sentences as per the importance they hold.
         - Please summarize the list and respond as an assistant who is summarizing a website content.
         - Never output the set delimiters in the output.
         - Do not use promotional texts for any particular items while summarizing.
         - Try to prioritize technical details like commands, code etc in the summary.
         - The user given sentences are delimited by ###.
         """},
        {'role': 'user',
         'content': "###" + trimmed_text + "###"},
    ]
    try:
        chat_completion_response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,  # this is the degree of randomness of the model's output
            max_tokens=max_tokens,  # the maximum number of tokens the model can ouptut
        )
        return chat_completion_response.choices[0].message["content"]
    except openai.error.InvalidRequestError as e:
        if e.code == 'context_length_exceeded':
            print("length exceeded.", len(trimmed_text))
            return get_completion_from_messages(trimmed_text[:-1500], temperature=temperature)


def generate_summary_handler(logger, page_content, page_url, is_regenerate):
    """
    Generate the summary for the given page content

    :param logger:
    :param page_content:
    :param page_url:
    :param is_regenerate: Flag to see if the regeneration is triggered or not
    :return:
    """
    # parser = HtmlParser.from_url(page_url, Tokenizer(LANGUAGE))
    # or for plain text files
    # parser = PlaintextParser.from_file("document.txt", Tokenizer(LANGUAGE))

    # logger.info(f"page_content:{page_content:[}")
    if page_url.endswith(".pdf"):
        logger.info(f"Seems to be a pdf file:{page_url}")

        r = requests.get(page_url)
        f = io.BytesIO(r.content)

        reader = PyPDF2.PdfReader(f)
        plain_text = reader.pages[2].extract_text().split('\n')
    else:
        plain_text = html2text.html2text(page_content)

    parser = PlaintextParser.from_string(plain_text, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)

    summarizer = Summarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    text = ""
    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        text += str(sentence)
    temperature = 0.0
    if is_regenerate:
        temperature = 0.5
    response = get_completion_from_messages(text[:10000], temperature=temperature)
    logger.debug(f"Generated summary for the URL: {page_url}, Summary: {str(response)}")
    return {"response": str(response)}
