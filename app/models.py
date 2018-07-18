"""
Data model used by the app (SQLAlchemy is used as ORM)
"""

from app import DB


class FluModel(DB.Model):
    """
    ORM Model representing a Flu Model
    """

    __tablename__ = 'model'

    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String, unique=True, nullable=False)
    source_type = DB.Column(DB.Text, nullable=False)
    is_public = DB.Column(DB.Boolean, nullable=False)
    is_displayed = DB.Column(DB.Boolean, nullable=False)
    calculation_parameters = DB.Column(DB.Text, nullable=True)
    model_scores = DB.relationship('ModelScore')

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def delete(self):
        """ Convenience method to delete current instance """
        DB.session.delete(self)
        DB.session.commit()

    def get_model_parameters(self):
        """Parse this model's data attribute and return a dict"""
        if self.source_type in ['google', 'twitter']:
            matlab_function, average_window_size = self.calculation_parameters.split(',')
            return {
                'matlab_function': matlab_function,
                'average_window_size': int(average_window_size)
            }
        return None

    @staticmethod
    def get_all_public():
        """ Returns all public models """
        return FluModel.query.filter_by(is_public=True).all()

    @staticmethod
    def get_model_for_id(id):
        """ Searches a model by its id """
        return FluModel.query.filter_by(id=id).first()

    def __repr__(self):
        return '<Model %s>' % self.name


class ModelScore(DB.Model):
    """
    ORM Model representing a data point of a model score
    """

    calculation_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date, primary_key=True)
    region = DB.Column(DB.Text, primary_key=True)
    score_value = DB.Column(DB.Float, nullable=False)

    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'), primary_key=True)

    @staticmethod
    def get_scores_for_dates(model_id, start_date, end_date):
        """

        :param model_id:
        :param start_date:
        :param end_date:
        :return:
        """
        return ModelScore.query.filter(
            ModelScore.flu_model_id == model_id,
            ModelScore.score_date >= start_date,
            ModelScore.score_date <= end_date
        ).all()

    def __repr__(self):
        return '<ModelScore %s %s %f>' % (
            self.day.strftime('%Y-%m-%d'), self.region, self.value)


class GoogleScore(DB.Model):
    """
    ORM Model representing a data point of a score retrieved from Google Health Trends private API
    """

    retrieval_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date, primary_key=True)
    score_value = DB.Column(DB.Float, nullable=False)
    term_id = DB.Column(DB.Integer, DB.ForeignKey('google_term.id'), primary_key=True)

    def __repr__(self):
        return '<GoogleScore %s %f>' % (
            self.day.strftime('%Y-%m-%d'), self.value)


class GoogleTerm(DB.Model):
    """
    ORM Model representing a term used in querying Google Health Trends API
    """

    id = DB.Column(DB.Integer, primary_key=True)
    term = DB.Column(DB.Text, unique=True, index=True, nullable=False)

    def __repr__(self):
        return '<GoogleTerm %s>' % self.term
