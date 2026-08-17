from flask import Flask, render_template, jsonify, request, send_from_directory
from database import NewsDatabase
from datetime import datetime, timedelta
import os
import logging
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

logger = logging.getLogger(__name__)
db = NewsDatabase()

# Get the absolute path to the recipients.json file
RECIPIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recipients.json')


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/statistics')
def get_statistics():
    """Get database statistics."""
    stats = db.get_statistics()
    return jsonify(stats)


@app.route('/api/articles')
def get_articles():
    """Get recent articles with optional filters."""
    limit = request.args.get('limit', 50, type=int)
    days = request.args.get('days', type=int)

    articles = db.get_recent_articles(limit=limit, days=days)
    return jsonify(articles)


@app.route('/api/articles/search')
def search_articles():
    """Search articles by query."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)

    if not query:
        return jsonify([])

    articles = db.search_articles(query, limit=limit)
    return jsonify(articles)


@app.route('/api/articles/range')
def get_articles_by_range():
    """Get articles within a date range."""
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        return jsonify({'error': 'Start and end dates required'}), 400

    articles = db.get_articles_by_date_range(start, end)
    return jsonify(articles)


@app.route('/api/email-logs')
def get_email_logs():
    """Get email sending history."""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_email_logs(limit=limit)
    return jsonify(logs)


@app.route('/api/agent-logs')
def get_agent_logs():
    """Get agent activity logs."""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_agent_logs(limit=limit)
    return jsonify(logs)


@app.route('/api/agent/run-now', methods=['POST'])
def run_agent_now():
    """Trigger agent to run immediately."""
    try:
        from ai_news_agent import run_news_digest
        success = run_news_digest()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'News digest sent successfully' if success else 'Failed to send digest'
        })
    except Exception as e:
        logger.error(f'Error running agent: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_data():
    """Manually trigger cleanup of old articles."""
    months = request.json.get('months', 3)
    deleted = db.cleanup_old_articles(months=months)
    return jsonify({
        'status': 'success',
        'deleted_count': deleted
    })


@app.route('/api/recipients')
def get_recipients():
    """Get list of recipient emails."""
    try:
        with open(RECIPIENTS_FILE, 'r') as f:
            data = json.load(f)
            return jsonify(data.get('recipients', []))
    except FileNotFoundError:
        return jsonify([os.getenv('RECIPIENT_EMAIL')])
    except Exception as e:
        logger.error(f'Error loading recipients: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/recipients/add', methods=['POST'])
def add_recipient():
    """Add a new recipient email."""
    try:
        email = request.json.get('email')
        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400

        try:
            with open(RECIPIENTS_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {'recipients': []}

        if email not in data['recipients']:
            data['recipients'].append(email)
            with open(RECIPIENTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f'Added recipient: {email}')
            return jsonify({'status': 'success', 'recipients': data['recipients']})
        else:
            return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        logger.error(f'Error adding recipient: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/recipients/remove', methods=['POST'])
def remove_recipient():
    """Remove a recipient email."""
    try:
        email = request.json.get('email')

        try:
            with open(RECIPIENTS_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': 'No recipients file found'}), 404

        if email in data['recipients']:
            data['recipients'].remove(email)
            with open(RECIPIENTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f'Removed recipient: {email}')
            return jsonify({'status': 'success', 'recipients': data['recipients']})
        else:
            return jsonify({'error': 'Email not found'}), 404
    except Exception as e:
        logger.error(f'Error removing recipient: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
def get_config():
    """Get current agent configuration."""
    config = {
        'recipient_email': os.getenv('RECIPIENT_EMAIL'),
        'sender_email': os.getenv('GMAIL_USER') or os.getenv('EMAIL_USER'),
        'has_newsapi_key': bool(os.getenv('NEWSAPI_KEY')),
        'schedule_time': '8:03 AM daily'
    }
    return jsonify(config)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))

    print('=' * 60)
    print('AI News Agent Portfolio')
    print('=' * 60)
    print(f'Dashboard running at: http://0.0.0.0:{port}')
    print('Press CTRL+C to stop')
    print('=' * 60)

    # Use debug=False in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
