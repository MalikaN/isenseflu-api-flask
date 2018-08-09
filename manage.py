"""
Commandline options for database management and testing
"""

import os
import unittest
from datetime import datetime
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import create_app, DB
from scheduler import Scheduler

MIGRATE = Migrate()

CONFIG_NAME = os.getenv('APP_CONFIG', 'development')
APP = create_app(CONFIG_NAME)
MIGRATE.init_app(APP, DB)

MANAGER = Manager(APP)
MANAGER.add_command('db', MigrateCommand)


@MANAGER.command
def test():
    """ Runs the unit tests without test coverage. """
    tests = unittest.TestLoader().discover('./tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


@MANAGER.command
def run_model_sched():
    """ Runs a scheduler to calculate model scores. """
    scheduler = Scheduler(APP)
    scheduler.run_model(1, "* * * * *")


@MANAGER.command
def init_model(model_id, start_date, end_date):
    """ Calculates the first batch of scores """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    scheduler = Scheduler(APP)
    scheduler.init_model(model_id, start, end)


if __name__ == '__main__':
    MANAGER.run()
