from flask import Flask, render_template, url_for, request, redirect, flash, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from safety import is_safe_url
from forms import LoginForm, UserForm, EditUserForm, HospitalForm, RoleForm, EditDetailsForm, CSVUploadForm, DataEditForm
from functools import wraps
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime

import requests
from configparser import ConfigParser

import csv
import json
import io
import random