# -*- coding: utf-8 -*-

from flask_frozen import Freezer
from app import app

if __name__ == '__main__':
    app.config['FREEZER_DESTINATION'] = 'docs'
    Freezer(app).freeze()
