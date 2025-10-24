"""
Design Evaluation Module
설계평가 모듈 - snowball link6 기반
"""
from flask import Blueprint

bp_design = Blueprint('design', __name__, url_prefix='/design')

from design import routes
