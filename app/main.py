#!/usr/bin/env python3
# Phase 2.2 Flask ChatOps App - Multi-AI Integration (OpenAI + Gemini)
# Enhanced implementation with Gemini 2.0 Flash support + ML Inference

from flask import Flask, request, jsonify
import os
import sys
import logging
from datetime import datetime, timezone
import json
import requests

# Add scripts directory to path for ML imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# AI Provider Imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ML Inference Imports  
try:
    from production_inference import get_inference_engine, initialize_models
    ML_AVAILABLE = True
    ML_ENGINE_TYPE = 'production'
except ImportError as e:
    try:
        # Fallback to real data inference engine
        from real_data_inference_engine import get_real_inference_engine
        ML_AVAILABLE = True
        ML_ENGINE_TYPE = 'real_data'
        logger.info("✅ Using real data inference engine")
    except ImportError as e2:
        print(f"⚠️ ML inference not available: {e}, {e2}")
        ML_AVAILABLE = False
        ML_ENGINE_TYPE = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Multi-AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'auto')  # auto, openai, gemini

# Initialize AI clients
openai_client = None
gemini_model = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("✅ OpenAI client initialized")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("✅ Gemini 2.0 Flash client initialized")

# Determine active AI provider
if AI_PROVIDER == 'auto':
    if gemini_model:
        AI_PROVIDER = 'gemini'
    elif openai_client:
        AI_PROVIDER = 'openai'
    else:
        AI_PROVIDER = 'fallback'

logger.info(f"🤖 Active AI Provider: {AI_PROVIDER.upper()}")

# Enhanced DevOps assistant prompt
DEVOPS_PROMPT = """You are an intelligent DevOps assistant for SmartCloudOps AI. 
You help with infrastructure monitoring, troubleshooting, and automation tasks.
Provide concise, actionable responses for DevOps operations."""

def process_with_ai(user_query):
    """Multi-AI processing with provider selection"""
    try:
        if AI_PROVIDER == 'gemini' and gemini_model:
            return process_with_gemini(user_query)
        elif AI_PROVIDER == 'openai' and openai_client:
            return process_with_openai(user_query)
        else:
            return f"DevOps Assistant (Basic): {user_query}"
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        return f"DevOps Assistant (Fallback): {user_query}"

def process_with_gemini(user_query):
    """Process query using Google Gemini 2.0 Flash"""
    try:
        response = gemini_model.generate_content(
            f"{DEVOPS_PROMPT}\n\nUser Query: {user_query}",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 200,
                "top_p": 0.8,
                "top_k": 40
            }
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {str(e)}")
        # Fallback to OpenAI if available
        if openai_client:
            return process_with_openai(user_query)
        return f"DevOps Assistant (Gemini Error): {user_query}"

def process_with_openai(user_query):
    """Process query using OpenAI GPT"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": DEVOPS_PROMPT},
                {"role": "user", "content": user_query}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        return f"DevOps Assistant (OpenAI Error): {user_query}"

# Enhanced endpoints with multi-AI support
@app.route('/status')
def status():
    """Enhanced status endpoint with ML information"""
    try:
        # Get ML health if available
        ml_status = None
        if ML_AVAILABLE:
            try:
                engine = get_inference_engine()
                ml_status = engine.health_check()
            except Exception as e:
                ml_status = {"status": "error", "error": str(e)}
        
        return jsonify({
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "2.2 - Multi-AI ChatOps + ML Integration",
            "version": "1.2.0",
            "ai_status": {
                "current_provider": AI_PROVIDER,
                "openai_available": OPENAI_AVAILABLE and bool(openai_client),
                "gemini_available": GEMINI_AVAILABLE and bool(gemini_model),
                "fallback_enabled": True
            },
            "ml_status": {
                "ml_available": ML_AVAILABLE,
                "model_health": ml_status
            },
            "endpoints": {
                "health": "/health",
                "query": "/query", 
                "logs": "/logs",
                "ai_switch": "/ai/switch",
                "ai_test": "/ai/test",
                "ml_health": "/ml/health",
                "ml_predict": "/ml/predict",
                "ml_metrics": "/ml/metrics",
                "ml_performance": "/ml/performance"
            }
        })
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/query', methods=['POST'])
def query():
    """Enhanced ChatOps query endpoint with multi-AI support"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
            
        # Enhanced input validation
        if len(user_query) > 500:
            return jsonify({"error": "Query too long (max 500 characters)"}), 400
            
        # Multi-AI processing
        ai_response = process_with_ai(user_query)
        
        response = {
            "query": user_query,
            "response": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "ai_provider": AI_PROVIDER,
            "phase": "2.2 - Multi-AI Integration"
        }
        
        logger.info(f"Query processed via {AI_PROVIDER}: {user_query[:50]}...")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/logs', methods=['GET'])
def logs():
    """Enhanced logs endpoint"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Enhanced log response
        sample_logs = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": f"Multi-AI ChatOps system active - Provider: {AI_PROVIDER}",
                "source": "smartcloudops_ai",
                "ai_provider": AI_PROVIDER
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO", 
                "message": "Enhanced ChatOps with Gemini 2.0 Flash + OpenAI support",
                "source": "ai_integration"
            }
        ]
        
        return jsonify({
            "logs": sample_logs[:limit],
            "total": len(sample_logs),
            "phase": "2.2 - Enhanced Multi-AI logs"
        })
        
    except Exception as e:
        logger.error(f"Logs error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/ai/switch', methods=['POST'])
def switch_ai_provider():
    """Switch AI provider dynamically"""
    global AI_PROVIDER
    try:
        data = request.get_json()
        new_provider = data.get('provider', '').lower()
        
        if new_provider not in ['auto', 'openai', 'gemini', 'fallback']:
            return jsonify({"error": "Invalid provider. Use: auto, openai, gemini, fallback"}), 400
        
        # Validate provider availability
        if new_provider == 'openai' and not openai_client:
            return jsonify({"error": "OpenAI not configured or available"}), 400
        if new_provider == 'gemini' and not gemini_model:
            return jsonify({"error": "Gemini not configured or available"}), 400
            
        old_provider = AI_PROVIDER
        AI_PROVIDER = new_provider
        
        logger.info(f"AI provider switched: {old_provider} → {AI_PROVIDER}")
        
        return jsonify({
            "status": "success",
            "previous_provider": old_provider,
            "current_provider": AI_PROVIDER,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Provider switch error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/ai/test', methods=['POST'])
def test_ai_providers():
    """Test all available AI providers"""
    try:
        test_query = "Hello, test connection"
        results = {}
        
        # Test OpenAI if available
        if openai_client:
            try:
                openai_response = process_with_openai(test_query)
                results['openai'] = {
                    "status": "success",
                    "response": openai_response[:100] + "..." if len(openai_response) > 100 else openai_response
                }
            except Exception as e:
                results['openai'] = {"status": "error", "error": str(e)}
        else:
            results['openai'] = {"status": "unavailable", "reason": "Not configured"}
            
        # Test Gemini if available
        if gemini_model:
            try:
                gemini_response = process_with_gemini(test_query)
                results['gemini'] = {
                    "status": "success", 
                    "response": gemini_response[:100] + "..." if len(gemini_response) > 100 else gemini_response
                }
            except Exception as e:
                results['gemini'] = {"status": "error", "error": str(e)}
        else:
            results['gemini'] = {"status": "unavailable", "reason": "Not configured"}
            
        return jsonify({
            "test_results": results,
            "current_provider": AI_PROVIDER,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI test error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# =============================================================================
# ML ANOMALY DETECTION ENDPOINTS (Phase 3)
# =============================================================================

@app.route('/ml/health', methods=['GET'])
def ml_health():
    """ML model health check endpoint."""
    try:
        if not ML_AVAILABLE:
            return jsonify({
                "status": "unavailable",
                "message": "ML inference not available",
                "ml_available": False
            }), 503
        
        # Get the appropriate engine based on type
        if ML_ENGINE_TYPE == 'real_data':
            engine = get_real_inference_engine()
        else:
            engine = get_inference_engine()
            
        health = engine.health_check()
        
        return jsonify({
            "status": health['status'],
            "ml_available": ML_AVAILABLE,
            "engine_type": ML_ENGINE_TYPE,
            "health": health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"ML health check error: {str(e)}")
        return jsonify({"error": "ML health check failed"}), 500

@app.route('/ml/predict', methods=['POST'])
def predict_anomaly():
    """Real-time anomaly prediction endpoint using real infrastructure data."""
    try:
        if not ML_AVAILABLE:
            return jsonify({
                "error": "ML inference not available",
                "anomaly": False,
                "confidence": 0.0
            }), 503
        
        # Get custom metrics from request body (optional)
        data = request.get_json() if request.is_json else {}
        custom_metrics = data.get('metrics') if data else None
        
        # Get the appropriate engine based on type
        if ML_ENGINE_TYPE == 'real_data':
            engine = get_real_inference_engine()
        else:
            engine = get_inference_engine()
            
        result = engine.predict_anomaly(custom_metrics)
        
        # Add engine type to response
        result['engine_type'] = ML_ENGINE_TYPE
        result['data_source'] = 'real_infrastructure_data' if ML_ENGINE_TYPE == 'real_data' else 'prometheus_api'
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Anomaly prediction error: {str(e)}")
        return jsonify({
            "error": str(e),
            "anomaly": False,
            "confidence": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/ml/metrics', methods=['GET'])
def get_current_metrics():
    """Get current system metrics from real infrastructure data."""
    try:
        if not ML_AVAILABLE:
            return jsonify({"error": "ML inference not available"}), 503
        
        # Get the appropriate engine based on type
        if ML_ENGINE_TYPE == 'real_data':
            engine = get_real_inference_engine()
        else:
            engine = get_inference_engine()
            
        metrics = engine.collect_live_metrics() if hasattr(engine, 'collect_live_metrics') else engine.collect_current_metrics()
        
        return jsonify({
            "metrics": metrics,
            "engine_type": ML_ENGINE_TYPE,
            "data_source": "real_infrastructure_data" if ML_ENGINE_TYPE == 'real_data' else "prometheus_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Metrics collection error: {str(e)}")
        return jsonify({"error": "Failed to collect metrics"}), 500

@app.route('/ml/performance', methods=['GET'])
def get_ml_performance():
    """Get ML model performance metrics."""
    try:
        if not ML_AVAILABLE:
            return jsonify({"error": "ML inference not available"}), 503
        
        engine = get_inference_engine()
        performance = engine.monitor.get_performance_metrics()
        
        return jsonify({
            "performance": performance,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        return jsonify({"error": "Failed to get performance metrics"}), 500

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    # Initialize ML models if available
    if ML_AVAILABLE:
        try:
            logger.info("🚀 Initializing ML models...")
            initialize_models()
            logger.info("✅ ML models initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ML models: {e}")
            ML_AVAILABLE = False
    
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SmartCloudOps AI ChatOps - Phase 2.2 + ML Integration")
    logger.info(f"ML Available: {ML_AVAILABLE}")
    app.run(host='0.0.0.0', port=port, debug=debug)