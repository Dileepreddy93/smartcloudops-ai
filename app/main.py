#!/usr/bin/env python3
# Phase 2.2 Flask ChatOps App - Basic GPT Integration (Per PDF Plan)
# Simple implementation as specified in phase plan

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
import json
try:
    from openai import OpenAI
    GPT_AVAILABLE = True
except ImportError:
    GPT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Phase 2.2 Basic GPT Configuration (per plan)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if GPT_AVAILABLE and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

# Basic prompt template (Phase 2.2 spec)
BASIC_PROMPT = "You are a DevOps assistant."

def process_with_gpt(user_query):
    """Basic GPT processing - Phase 2.2 implementation"""
    if not GPT_AVAILABLE or not openai_client:
        return f"Basic response to: {user_query}"
    
    try:
        # Basic OpenAI integration as per Phase 2.2 plan
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": BASIC_PROMPT},
                {"role": "user", "content": user_query}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT error: {str(e)}")
        return f"Basic response to: {user_query}"

# Phase 2.1 Basic Endpoints (per PDF plan)
@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.2.0",
        "phase": "2.2 - Basic GPT Integration (PDF Compliant)",
        "gpt_available": GPT_AVAILABLE,
        "openai_configured": bool(openai_client)
    })

@app.route('/query', methods=['POST'])
def query():
    """Basic ChatOps query endpoint - Phase 2.2 (Basic GPT)"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
            
        # Basic input sanitization (Phase 2.2 requirement)
        if len(user_query) > 200:
            return jsonify({"error": "Query too long"}), 400
            
        # Phase 2.2 - Basic GPT response
        gpt_response = process_with_gpt(user_query)
        
        response = {
            "query": user_query,
            "response": gpt_response,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "phase": "2.2 - Basic GPT Integration"
        }
        
        logger.info(f"Query processed: {user_query}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/logs', methods=['GET'])
def logs():
    """Logs endpoint - Basic implementation"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Basic log response
        sample_logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Basic log entry - Phase 2.1 implementation",
                "source": "flask_app"
            }
        ]
        
        return jsonify({
            "logs": sample_logs[:limit],
            "total": len(sample_logs),
            "phase": "2.1 - Basic logs endpoint"
        })
        
    except Exception as e:
        logger.error(f"Logs error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SmartCloudOps AI ChatOps - Phase 2.2 Basic GPT Integration")
    app.run(host='0.0.0.0', port=port, debug=debug)