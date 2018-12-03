"""
 Run calculation of Model Scores
"""

from datetime import date
from flask_api import FlaskAPI
from logging import INFO, log, basicConfig
from os import getenv

from .google_api_client import GoogleApiClient
from .matlab_client import build_matlab_client
from .message_client import build_message_client
from .score_query_registry import get_date_ranges_google_score,\
    get_google_batch,\
    set_and_verify_google_dates,\
    set_google_scores,\
    get_dates_missing_model_score,\
    set_and_get_model_score, \
    get_matlab_function_attr,\
    get_moving_averages_or_scores

basicConfig(format='%(asctime)s %(levelname)s : %(message)s', level=INFO)


def run(model_id: int, start: date, end: date):
    """ Calculate the model score for the date range specified """
    missing_google_range, missing_google_list = get_date_ranges_google_score(model_id, start, end)
    if missing_google_range and missing_google_list:
        batch = get_google_batch(model_id, missing_google_range)
        api_client = GoogleApiClient()
        for terms, start_date, end_date in batch:
            batch_scores = api_client.fetch_google_scores(terms, start_date, end_date)
            set_google_scores(batch_scores)
        set_and_verify_google_dates(model_id, missing_google_list)  # Raise an error if missing data
    else:
        log(INFO, 'Google scores have already been collected for this time period')
    missing_model_dates = get_dates_missing_model_score(model_id, start, end)
    if missing_model_dates:
        model_function = get_matlab_function_attr(model_id)
        msg_score = None
        msg_date = None
        matlab_client = build_matlab_client()
        for missing_model_date in missing_model_dates:
            scores_or_averages = get_moving_averages_or_scores(model_id, model_function['average_window_size'],
                                                               missing_model_date)
            msg_score = set_and_get_model_score(
                model_id,
                matlab_client,
                (model_function['matlab_function'], model_function['has_confidence_interval']),
                scores_or_averages,
                missing_model_date
            )
            msg_date = missing_model_date
        if getenv('TWITTER_ENABLED'):
            mq_client = build_message_client()
            mq_client.publish_model_score(msg_date, msg_score)
            log(INFO, 'Latest ModelScore value sent to message queue')
    else:
        log(INFO, 'Model scores have already been collected for this time period')


def runsched(model_id: int, start: date, end: date, app: FlaskAPI):
    """ Calculate the model score for the date range specified inside the scheduler """
    with app.app_context():
        run(model_id, start, end)
