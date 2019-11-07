# -*- coding: utf-8 -*-

from flask_frozen import Freezer
from app import app

if __name__ == '__main__':
    app.config['FREEZER_DESTINATION'] = '.'
    app.config['FREEZER_REMOVE_EXTRA_FILES'] = False
    app.config['FREEZER_RELATIVE_URLS'] = True
    Freezer(app).freeze()
