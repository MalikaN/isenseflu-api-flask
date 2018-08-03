"""
Data model used by the app (SQLAlchemy is used as ORM)
"""

from datetime import date

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
    def get_model_for_id(model_id):
        """ Searches a model by its id """
        return FluModel.query.filter_by(id=model_id).first()

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

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    @staticmethod
    def get_scores_for_dates(model_id, start_date, end_date):
        """ Returns a list of model scores for a model id, start and end date """
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
    term_id = DB.Column(DB.Integer, DB.ForeignKey('google_term.id'), primary_key=True)
    score_value = DB.Column(DB.Float, nullable=False)

    def __init__(self, term_id: int, score_date: date, score_value: float):
        self.term_id = term_id
        self.score_date = score_date
        self.score_value = score_value

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleScore term_id=%d %f>' % (self.term_id, self.value)


class GoogleTerm(DB.Model):
    """
    ORM Model representing a term used in querying Google Health Trends API
    """

    id = DB.Column(DB.Integer, primary_key=True)
    term = DB.Column(DB.Text, unique=True, index=True, nullable=False)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleTerm %s>' % self.term


class GoogleDate(DB.Model):
    """
    ORM Model representing the date for which a complete set of Google terms for a particular model
    ID was retrieved. The date here stored assumes the scores for a set of Google terms as a
    transaction and should always be added to the session together with the set of GoogleScores.
    """

    id = DB.Column(DB.Integer, primary_key=True)
    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'))
    transaction_timestamp = DB.Column(DB.DateTime, default=DB.func.current_timestamp())
    score_date = DB.Column(DB.Date)

    def __init__(self, model_id: int, score_date: date):
        self.flu_model_id = model_id
        self.score_date = score_date

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()

    def __repr__(self):
        return '<GoogleDate model_id=%d %s>' % (
            self.flu_model_id, self.score_date.strftime('%Y-%m-%d')
        )


class FluModelGoogleTerm(DB.Model):
    """
    ORM Model representing a link table between FluModel and GoogleTerm
    """

    flu_model_id = DB.Column(DB.Integer, DB.ForeignKey('model.id'), primary_key=True)
    google_term_id = DB.Column(DB.Integer, DB.ForeignKey('google_term.id'), primary_key=True)

    def save(self):
        """ Convenience method to save current instance """
        DB.session.add(self)
        DB.session.commit()
