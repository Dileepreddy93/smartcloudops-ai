#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Flask Application
==============================================

Security-hardened multi-AI ChatOps application with real data ML integration.
"""

from flask import Flask, request, jsonify
import os
import sys
import logging
import traceback
from datetime import datetime, timezone
import json
from pathlib import Path

# Secure path handling for ML imports
app_dir = Path(__file__).parent
scripts_dir = app_dir.parent / 'scripts'
if scripts_dir.exists():
    sys.path.insert(0, str(scripts_dir))

# Import configuration manager
try:
    from config import config, logger
except ImportError:
    # Fallback logging if config import fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    config = None
    logger.warning("Config module not available, using fallback configuration")

# AI Provider Imports with error handling
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI module available")
except ImportError as e:
    logger.warning(f"❌ OpenAI not available: {e}")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini module available")
except ImportError as e:
    logger.warning(f"❌ Gemini not available: {e}")

# ML Engine Imports with error handling
ML_ENGINE_AVAILABLE = False
RealDataInferenceEngine = None
MLModel = None

try:
    from real_data_inference_engine import RealDataInferenceEngine
    ML_ENGINE_AVAILABLE = True
    logger.info("✅ Real Data ML Engine available")
except ImportError as e:
    logger.warning(f"❌ Real Data ML Engine not available: {e}")
    try:
        # Fallback to Phase 3 ML
        from phase3_anomaly_detection import MLModel
        ML_ENGINE_AVAILABLE = True
        logger.info("✅ Phase 3 ML Engine available as fallback")
    except ImportError as e2:
        logger.error(f"❌ No ML Engine available: {e2}")

# Initialize Flask app with security settings
app = Flask(__name__)
if config:
    app.config['SECRET_KEY'] = config.secret_key
    app.config['DEBUG'] = config.debug
else:
    app.config['SECRET_KEY'] = os.urandom(32)
    app.config['DEBUG'] = False

# AI Configuration with environment support
if config:
    OPENAI_API_KEY = config.ai.openai_api_key
    GEMINI_API_KEY = config.ai.gemini_api_key
    AI_PROVIDER = config.ai.provider
else:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'auto')

# Initialize AI clients with error handling
openai_client = None
gemini_model = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized")
    except Exception as e:
        logger.error(f"❌ OpenAI client initialization failed: {e}")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini 2.0 Flash client initialized")
    except Exception as e:
        logger.error(f"❌ Gemini client initialization failed: {e}")

# Determine active AI provider
if AI_PROVIDER == 'auto':
    if gemini_model:
        AI_PROVIDER = 'gemini'
    elif openai_client:
        AI_PROVIDER = 'openai'
    else:
        AI_PROVIDER = 'fallback'

logger.info(f"🤖 Active AI Provider: {AI_PROVIDER.upper()}")

# ML Engine Configuration with improved error handling
ML_ENGINE_TYPE = "none"
ml_engine_instance = None

# Get ML engine setting from environment
ml_engine_preference = os.getenv('ML_ENGINE', 'auto')

if ML_ENGINE_AVAILABLE:
    try:
        if ml_engine_preference == 'real_data' and RealDataInferenceEngine:
            ml_engine_instance = RealDataInferenceEngine()
            ML_ENGINE_TYPE = "real_data"
            logger.info("✅ Real Data ML Engine initialized")
        elif ml_engine_preference == 'phase3' and MLModel:
            ml_engine_instance = MLModel()
            ML_ENGINE_TYPE = "phase3"
            logger.info("✅ Phase 3 ML Engine initialized")
        elif ml_engine_preference == 'auto':
            # Auto-detection: prefer real_data over phase3
            if RealDataInferenceEngine:
                ml_engine_instance = RealDataInferenceEngine()
                ML_ENGINE_TYPE = "real_data"
                logger.info("✅ Real Data ML Engine auto-selected")
            elif MLModel:
                ml_engine_instance = MLModel()
                ML_ENGINE_TYPE = "phase3"
                logger.info("✅ Phase 3 ML Engine auto-selected")
        else:
            logger.warning(f"⚠️ Requested ML engine '{ml_engine_preference}' not available")
    except Exception as e:
        logger.error(f"❌ ML Engine initialization failed: {e}")
        ML_ENGINE_TYPE = "none"
else:
    logger.warning("⚠️ No ML engines available")

def get_inference_engine():
    """Get the available inference engine."""
    if ML_ENGINE_TYPE == "real_data" and ml_engine_instance:
        return ml_engine_instance
    elif ML_ENGINE_TYPE == "phase3" and ml_engine_instance:
        return ml_engine_instance
    else:
        return None

def get_real_inference_engine():
    """Get real data inference engine if available."""
    if ML_ENGINE_TYPE == "real_data" and ml_engine_instance:
        return ml_engine_instance
    return None

# Enhanced DevOps assistant prompt
DEVOPS_PROMPT = """You are an intelligent DevOps assistant for SmartCloudOps AI. 
You help with infrastructure monitoring, troubleshooting, and automation tasks.
Provide concise, actionable responses for DevOps operations."""

def process_with_ai(user_query):
    """Multi-AI processing with provider selection and error handling"""
    try:
        if AI_PROVIDER == 'gemini' and gemini_model:
            return process_with_gemini(user_query)
        elif AI_PROVIDER == 'openai' and openai_client:
            return process_with_openai(user_query)
        else:
            return process_fallback(user_query)
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return f"AI processing temporarily unavailable. Error: {str(e)}"

def process_with_gemini(user_query):
    """Process query with Gemini"""
    try:
        response = gemini_model.generate_content(f"{DEVOPS_PROMPT}\n\nUser: {user_query}")
        return response.text
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        return f"Gemini AI temporarily unavailable: {str(e)}"

def process_with_openai(user_query):
    """Process query with OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": DEVOPS_PROMPT},
                {"role": "user", "content": user_query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI processing error: {e}")
        return f"OpenAI temporarily unavailable: {str(e)}"

def process_fallback(user_query):
    """Fallback processing when AI is unavailable"""
    logger.info("Using fallback AI processing")
    
    # Simple keyword-based responses
    query_lower = user_query.lower()
    
    if any(word in query_lower for word in ['status', 'health', 'check']):
        return "System status: Monitoring active. Use /status endpoint for detailed health information."
    elif any(word in query_lower for word in ['cpu', 'memory', 'disk']):
        return "Resource monitoring: Check /ml/metrics endpoint for current infrastructure metrics."
    elif any(word in query_lower for word in ['anomaly', 'alert', 'error']):
        return "Anomaly detection: Use /ml/predict endpoint for real-time anomaly detection."
    else:
        return f"DevOps Assistant: Received '{user_query}'. Available endpoints: /status, /ml/health, /ml/predict, /ml/metrics"

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': ['/status', '/chat', '/ml/health', '/ml/predict', '/ml/metrics']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Application Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 500

# Routes
@app.route('/status')
def status():
    """Application health status"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '3.0.0',
        'environment': config.environment if config else 'unknown',
        'ai_provider': AI_PROVIDER,
        'ml_engine': ML_ENGINE_TYPE,
        'features': {
            'openai': OPENAI_AVAILABLE and bool(openai_client),
            'gemini': GEMINI_AVAILABLE and bool(gemini_model),
            'ml_inference': ML_ENGINE_AVAILABLE and bool(ml_engine_instance)
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Multi-AI chat endpoint with error handling"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message in request'}), 400
        
        user_message = data['message']
        if not user_message.strip():
            return jsonify({'error': 'Empty message not allowed'}), 400
        
        # Process with AI
        ai_response = process_with_ai(user_message)
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'provider': AI_PROVIDER,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({
            'error': 'Chat processing failed',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/ml/health')
def ml_health():
    """ML inference engine health check"""
    try:
        engine = get_inference_engine()
        if not engine:
            return jsonify({
                'status': 'unavailable',
                'message': 'No ML engine available',
                'engine_type': ML_ENGINE_TYPE,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 503
        
        # Try to get health status from engine
        if hasattr(engine, 'health_check'):
            health_status = engine.health_check()
        else:
            health_status = {'status': 'unknown', 'message': 'Health check not implemented'}
        
        return jsonify({
            'status': 'healthy',
            'engine_type': ML_ENGINE_TYPE,
            'health_details': health_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"ML health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'engine_type': ML_ENGINE_TYPE,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/ml/predict', methods=['POST'])
def ml_predict():
    """ML anomaly prediction endpoint"""
    try:
        engine = get_inference_engine()
        if not engine:
            return jsonify({
                'error': 'ML engine unavailable',
                'message': 'No ML inference engine available',
                'engine_type': ML_ENGINE_TYPE
            }), 503
        
        # Get prediction from engine
        if hasattr(engine, 'predict_anomaly'):
            result = engine.predict_anomaly()
        elif hasattr(engine, 'predict'):
            result = engine.predict()
        else:
            return jsonify({
                'error': 'Prediction method not available',
                'engine_type': ML_ENGINE_TYPE
            }), 501
        
        # Enhance result with metadata
        result['engine_type'] = ML_ENGINE_TYPE
        result['data_source'] = 'real_infrastructure_data' if ML_ENGINE_TYPE == 'real_data' else 'prometheus_api'
        result['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e),
            'engine_type': ML_ENGINE_TYPE,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/ml/metrics')
def ml_metrics():
    """Current infrastructure metrics"""
    try:
        engine = get_inference_engine()
        if not engine:
            return jsonify({
                'error': 'ML engine unavailable',
                'message': 'No ML inference engine available'
            }), 503
        
        # Get current metrics
        if hasattr(engine, 'get_current_metrics'):
            metrics = engine.get_current_metrics()
        else:
            metrics = {'error': 'Metrics collection not available'}
        
        return jsonify({
            'metrics': metrics,
            'engine_type': ML_ENGINE_TYPE,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Metrics collection error: {e}")
        return jsonify({
            'error': 'Metrics collection failed',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = config.debug if config else False
    
    logger.info(f"🚀 Starting SmartCloudOps AI on port {port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🤖 AI Provider: {AI_PROVIDER}")
    logger.info(f"🧠 ML Engine: {ML_ENGINE_TYPE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
