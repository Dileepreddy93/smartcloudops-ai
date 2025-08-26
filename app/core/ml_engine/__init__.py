"""
SmartCloudOps AI - ML Engine Package
===================================

Machine Learning inference engines for SmartCloudOps AI.
Provides secure, production-hardened ML prediction capabilities.
"""

# Safe import with fallback for missing dependencies
try:
    from .secure_inference import SecureMLInferenceEngine

    SECURE_ENGINE_AVAILABLE = True
except ImportError:
    SecureMLInferenceEngine = None  # type: ignore
    SECURE_ENGINE_AVAILABLE = False

try:
    from .production_inference import ProductionInferenceEngine

    PRODUCTION_ENGINE_AVAILABLE = True
except ImportError:
    ProductionInferenceEngine = None  # type: ignore
    PRODUCTION_ENGINE_AVAILABLE = False

# Export what's available
__all__ = []
if SECURE_ENGINE_AVAILABLE:
    __all__.append("SecureMLInferenceEngine")
if PRODUCTION_ENGINE_AVAILABLE:
    __all__.append("ProductionInferenceEngine")
