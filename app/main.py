#!/usr/bin/env python3
# Phase 2.1 Flask ChatOps App - Basic Implementation (Per PDF Plan)
# Simple endpoints as specified in Phase Wise Plan

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Phase 2.1 Basic Endpoints (as per PDF)
@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "phase": "2.1 - Basic Flask App (PDF Compliant)"
    })

@app.route('/query', methods=['POST'])
def query():
    """Basic ChatOps query endpoint - Phase 2.1 (Simple version per PDF)"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
            
        # Phase 2.1 - Basic response (GPT integration comes in Phase 2.2 + 5)
        response = {
            "query": user_query,
            "response": f"Basic ChatOps response to: {user_query}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "phase": "2.1 - Basic Implementation"
        }
        
        logger.info(f"Query processed: {user_query}")
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
    
    logger.info(f"Starting SmartCloudOps AI ChatOps - Phase 2.1 Basic Implementation")
    app.run(host='0.0.0.0', port=port, debug=debug)