#!/usr/bin/env python3
# Phase 2.2 Flask ChatOps App - GPT Integration (Per PDF Plan)
# Enhanced with intelligent query processing

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
import json
try:
    import openai
    from litellm import completion
    GPT_AVAILABLE = True
except ImportError:
    GPT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Phase 2.2 GPT Configuration
GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-3.5-turbo')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# DevOps Prompt Templates
SYSTEM_PROMPT = """You are a DevOps AI assistant for SmartCloudOps AI platform. 
Provide concise, actionable responses for infrastructure monitoring, troubleshooting, and automation queries.
Focus on AWS, Docker, Kubernetes, monitoring, and CI/CD topics.
Keep responses under 200 words and include specific commands when helpful."""

def process_with_gpt(user_query):
    """Process user query with GPT integration"""
    if not GPT_AVAILABLE or not OPENAI_API_KEY:
        return f"GPT integration available but not configured. Basic response to: {user_query}"
    
    try:
        response = completion(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT processing error: {str(e)}")
        return f"GPT processing unavailable. Basic response to: {user_query}"

# Phase 2.1 Basic Endpoints (as per PDF)
@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.2.0",
        "phase": "2.2 - GPT Integration (PDF Compliant)",
        "gpt_available": GPT_AVAILABLE,
        "openai_configured": bool(OPENAI_API_KEY),
        "model": GPT_MODEL
    })

@app.route('/query', methods=['POST'])
def query():
    """Enhanced ChatOps query endpoint - Phase 2.2 (GPT Integration)"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
            
        # Input validation and sanitization
        if len(user_query) > 500:
            return jsonify({"error": "Query too long (max 500 characters)"}), 400
            
        # Phase 2.2 - GPT-powered intelligent response
        gpt_response = process_with_gpt(user_query)
        
        response = {
            "query": user_query,
            "response": gpt_response,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "phase": "2.2 - GPT Integration",
            "gpt_available": GPT_AVAILABLE,
            "model": GPT_MODEL if GPT_AVAILABLE else "N/A"
        }
        
        logger.info(f"GPT Query processed: {user_query[:50]}...")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
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
        logger.error(f"Logs retrieval error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SmartCloudOps AI ChatOps - Phase 2.2 GPT Integration Complete")
    app.run(host='0.0.0.0', port=port, debug=debug)