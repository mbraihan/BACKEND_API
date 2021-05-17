from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

import uuid
import os
import sys
from dotenv import load_dotenv
import urllib
import helper
import re
from urllib.request import urlopen
import json

load_dotenv()


uri = os.getenv("POSTGRES_URI")


app = Flask(__name__)
CORS(app, support_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


from backendapi import routes