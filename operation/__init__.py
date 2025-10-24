"""
Operation Evaluation Module
운영평가 모듈 - snowball link7 기반
"""
from flask import Blueprint

bp_operation = Blueprint('operation', __name__, url_prefix='/operation')

from operation import routes
