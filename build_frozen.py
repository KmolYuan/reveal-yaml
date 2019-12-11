# -*- coding: utf-8 -*-

from flask_frozen import Freezer
from app import app

if __name__ == '__main__':
    app.config['FREEZER_DESTINATION'] = 'build'
    app.config['FREEZER_RELATIVE_URLS'] = True
    Freezer(app).freeze()
