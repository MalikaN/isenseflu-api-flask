"""
Flask app entry point
"""

from datetime import date, timedelta, datetime
from numbers import Number
from flask import request
from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

DB = SQLAlchemy()


def create_app(config_name):
    """ Creates an instance of Flask based on the config name as found in instance/config.py """

    from app.models_query_registry import get_flu_model_for_id, get_public_flu_models, \
        get_model_scores_for_dates, get_model_function, get_default_flu_model

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.ini', silent=True)
    DB.init_app(app)

    @app.route('/', methods=['GET'])
    def root_route():
        """ Default route (/). Returns model scores for the default flu model """
        default_model = get_default_flu_model()
        if not default_model:
            return '', status.HTTP_204_NO_CONTENT
        model_parameters = get_model_function(default_model.id)
        datapoints = []
        for score in default_model.model_scores:
            child = {
                'score_date': score.score_date.strftime('%Y-%m-%d'),
                'score_value': score.score_value
            }
            if model_parameters.has_confidence_interval:
                confidence_interval = {
                    'confidence_interval_upper': score.confidence_interval_upper,
                    'confidence_interval_lower': score.confidence_interval_lower
                }
                child.update(confidence_interval)
            datapoints.append(child)
        result = {
            'id': default_model.id,
            'name': default_model.name,
            'hasConfidenceInterval': model_parameters.has_confidence_interval,
            'datapoints': datapoints
        }
        return result, status.HTTP_200_OK

    @app.route('/models', methods=['GET'])
    def models_route():
        """ Returns a catalogue of public models """
        flu_models = get_public_flu_models()
        if not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        results = []
        for flu_model in flu_models:
            obj = {
                'id': flu_model.id,
                'name': flu_model.name
            }
            results.append(obj)
        return results, status.HTTP_200_OK

    @app.route('/scores/<int:id>', methods=['GET'])
    def scores_route(id):
        """ Returns a list of model scores for a model id, start and end date """
        def_end_date = date.today() - timedelta(days=2)
        end_date = str(request.args.get('endDate', def_end_date.strftime('%Y-%m-%d')))
        def_start_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        start_date = str(request.args.get('startDate', def_start_date.strftime('%Y-%m-%d')))
        if start_date > end_date:
            return '', status.HTTP_400_BAD_REQUEST
        flu_model = get_flu_model_for_id(id)
        scores = None
        if flu_model is not None:
            scores = get_model_scores_for_dates(
                id,
                datetime.strptime(start_date, '%Y-%m-%d').date(),
                datetime.strptime(end_date, '%Y-%m-%d').date()
            )
        if scores is None:
            return '', status.HTTP_204_NO_CONTENT
        datapoints = []
        for score in scores:
            child = {
                'score_date': score.score_date.strftime('%Y-%m-%d'),
                'score_value': score.score_value
            }
            if isinstance(score.confidence_interval_upper, Number) and \
                    isinstance(score.confidence_interval_upper, Number):
                confidence_interval = {
                    'confidence_interval_upper': score.confidence_interval_upper,
                    'confidence_interval_lower': score.confidence_interval_lower
                }
                child.update(confidence_interval)
            datapoints.append(child)
        model_parameters = get_model_function(flu_model.id)
        result = {
            'name': flu_model.name,
            'sourceType': flu_model.source_type,
            'displayModel': flu_model.is_displayed,
            'parameters': {
                'georegion': 'e',
                'smoothing': model_parameters.average_window_size
            },
            'datapoints': datapoints
        }
        return result, status.HTTP_200_OK

    return app
