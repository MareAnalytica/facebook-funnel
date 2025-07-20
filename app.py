from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from dotenv import load_dotenv
import json
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create database connection"""
    try:
        # Use connection string directly from DATABASE_URL
        connection_string = os.getenv('DATABASE_URL')
        if not connection_string:
            logger.error("DATABASE_URL environment variable not set")
            return None
        
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def init_db():
    """Initialize database table"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_responses (
                    id SERIAL PRIMARY KEY,
                    facebook_id VARCHAR(255),
                    facebook_name VARCHAR(255),
                    facebook_email VARCHAR(255),
                    facebook_likes JSONB,
                    scoreapp_data JSONB,
                    scoreapp_quiz_id VARCHAR(255),
                    scoreapp_result_url TEXT,
                    scoreapp_finished_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Database table initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/api/facebook-data', methods=['POST'])
def save_facebook_data():
    """Save Facebook profile and likes data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract Facebook data
        facebook_id = data.get('id')
        facebook_name = data.get('name')
        facebook_email = data.get('email')
        facebook_likes = data.get('likes', [])
        
        # Store in database
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO user_responses (facebook_id, facebook_name, facebook_email, facebook_likes)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (facebook_id, facebook_name, facebook_email, json.dumps(facebook_likes)))
            
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Facebook data saved for user {facebook_id}")
            return jsonify({'success': True, 'user_id': user_id}), 200
        else:
            logger.error("Failed to connect to database")
            return jsonify({'error': 'Database connection failed'}), 500
            
    except Exception as e:
        logger.error(f"Error saving Facebook data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/webhooks/scoreapp', methods=['POST'])
def scoreapp_webhook():
    """Handle ScoreApp completion webhook"""
    try:
        data = request.get_json()
        
        if not data:
            logger.error("No data received in ScoreApp webhook")
            return jsonify({'error': 'No data provided'}), 400
        
        # Log the received data for debugging
        logger.info(f"ScoreApp webhook received: {json.dumps(data, indent=2)}")
        
        # Extract event type and data
        event_name = data.get('event_name')
        webhook_data = data.get('data', {})
        
        # We only care about QUIZ_FINISHED and LEAD_SIGNED_UP events
        if event_name not in ['QUIZ_FINISHED', 'LEAD_SIGNED_UP']:
            logger.info(f"Ignoring event: {event_name}")
            return jsonify({'success': True, 'message': f'Event {event_name} ignored'}), 200
        
        # Extract Facebook ID from lead form questions
        facebook_id = None
        lead_form_questions = webhook_data.get('lead_form_questions', [])
        for question in lead_form_questions:
            if question.get('question', '').lower() == 'facebook id':
                answers = question.get('answers', [])
                if answers:
                    facebook_id = answers[0].get('answer')
                    break
        
        if not facebook_id:
            logger.error("No Facebook ID found in ScoreApp data")
            return jsonify({'error': 'No Facebook ID found'}), 400
        
        # Extract structured data from ScoreApp
        result_url = None
        finished_at = None
        
        if event_name == 'QUIZ_FINISHED':
            result_url = webhook_data.get('result_url')
            finished_at = webhook_data.get('finished_at')
        
        # Check if a record with this Facebook ID already exists
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Check if Facebook ID already exists
            cur.execute('SELECT id FROM user_responses WHERE facebook_id = %s LIMIT 1', (facebook_id,))
            existing_record = cur.fetchone()
            
            if existing_record:
                # Update existing record with ScoreApp data
                cur.execute('''
                    UPDATE user_responses 
                    SET scoreapp_data = %s, scoreapp_quiz_id = %s, scoreapp_result_url = %s, scoreapp_finished_at = %s
                    WHERE facebook_id = %s
                ''', (json.dumps(data), webhook_data.get('id'), result_url, finished_at, facebook_id))
                
                logger.info(f"ScoreApp data updated for existing user {facebook_id} (Event: {event_name})")
            else:
                # Create new record with ScoreApp data
                cur.execute('''
                    INSERT INTO user_responses (
                        facebook_id, scoreapp_data, scoreapp_quiz_id,
                        scoreapp_result_url, scoreapp_finished_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    facebook_id, 
                    json.dumps(data), 
                    webhook_data.get('id'),
                    result_url,
                    finished_at
                ))
                
                logger.info(f"ScoreApp data stored in new record for user {facebook_id} (Event: {event_name})")
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({'success': True}), 200
        else:
            logger.error("Failed to connect to database for ScoreApp webhook")
            return jsonify({'error': 'Database connection failed'}), 500
            
    except Exception as e:
        logger.error(f"Error processing ScoreApp webhook: {e}")
        logger.error(f"Received data: {request.get_data()}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 