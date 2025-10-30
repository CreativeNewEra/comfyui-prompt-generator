"""
Main Application Route

Serves the main single-page application HTML.
"""

from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """
    Serve the main application page.

    Returns the single-page application HTML which includes embedded
    CSS and JavaScript for the full user interface.

    Returns:
        str: Rendered HTML template (templates/index.html)
    """
    return render_template('index.html')
