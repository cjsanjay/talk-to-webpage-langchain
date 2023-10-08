import logging
from flask import Flask, request, jsonify, abort
from functools import wraps
import os
import time
from .apihandlers.generateIndex import generate_index_handler, clean_up_index_handler, generate_scrap_index_handler
from .apihandlers.genenerateSummary import generate_summary_handler
from .apihandlers.generateAnswer import generate_answer_handler

import nltk
def download_nltk():
    time.sleep(3)
    nltk.download('punkt')

app = Flask(__name__)

api_key = str(os.getenv('API_KEY'))
open_ai_key = str(os.getenv('OPENAI_API_KEY'))
pinecone_key = str(os.getenv('PINECONE_API_KEY'))
pinecone_region = str(os.getenv('PINECONE_ENVIRONMENT_REGION'))

# The actual decorator function
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == os.getenv('API_KEY'):
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


def require_appSuperkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == os.getenv('API_SUPER_KEY'):
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function

@app.route('/api/v1/cleanUpIndex', methods=["POST"])
@require_appSuperkey
def cleanup_index():
    app.logger.info(f"Cleaning up all pinecone indexes")
    return clean_up_index_handler(app.logger)


@app.route('/api/v1/generateIndex', methods=["POST"])
@require_appkey
def generate_index():
    if 'page_content' not in request.json or 'page_url' not in request.json:
        abort(400)
    page_content = request.json['page_content']
    page_url = request.json['page_url']
    app.logger.info(f"Generating index for the URL: {page_url}")
    resp = generate_index_handler(app.logger, page_content, page_url)
    try:
        generate_scrap_index_handler(app.logger, page_url)
    except Exception as ex:
        app.logger.warn(f"Failed to generate the scrape index error: {str(ex)}")

    return resp


@app.route('/api/v1/generateScrapIndex', methods=["POST"])
@require_appkey
def generate_scrap_index():
    if 'page_url' not in request.json:
        abort(400)
    page_url = request.json['page_url']
    app.logger.info(f"Generating scrap index for the URL: {page_url}")
    return generate_scrap_index_handler(app.logger, page_url)


@app.route('/api/v1/generateSummary', methods=["POST"])
@require_appkey
def generate_summary():
    if 'page_content' not in request.json or 'page_url' not in request.json:
        abort(400)
    is_regenerate = False
    if 'is_regenerate' in request.json:
        is_regenerate = request.json["is_regenerate"]
    page_content = request.json['page_content']
    page_url = request.json['page_url']
    app.logger.info(f"Generating summary for the URL: {page_url}")
    return generate_summary_handler(app.logger, page_content, page_url, is_regenerate)


@app.route('/api/v1/generateScrappedAnswer', methods=["POST"])
@require_appkey
def generate_scrapped_answer():
    if 'question_text' not in request.json or 'page_url' not in request.json:
        abort(400)
    if 'chat_history' not in request.json:
        chat_history = []
    else:
        chat_history = request.json['chat_history']
    question_text = request.json['question_text']
    page_url = request.json['page_url']
    app.logger.info(f"Generating scrapped answer for the URL: {page_url}")
    return generate_answer_handler(app.logger, question_text, page_url, chat_history, is_scrapped=True)

@app.route('/api/v1/generateAnswer', methods=["POST"])
@require_appkey
def generate_answer():
    if 'question_text' not in request.json or 'page_url' not in request.json:
        abort(400)
    if 'chat_history' not in request.json:
        chat_history = []
    else:
        chat_history = request.json['chat_history']
    question_text = request.json['question_text']
    page_url = request.json['page_url']
    app.logger.info(f"Generating answer for the URL: {page_url}")
    return generate_answer_handler(app.logger, question_text, page_url, chat_history, is_scrapped=True)


# Setup gunicorn logger as the app logger
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    download_nltk()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8001))
    app.run(debug=True, host='0.0.0.0', port=port)
