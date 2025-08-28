#!/usr/bin/env python3
"""
SmartCloudOps AI - Main Application Entry Point
==============================================

This file redirects to the secure main application.
For production use, use app/main_secure.py directly.
"""


import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))


def main():
    """Main entry point that redirects to the secure application."""
    print("🚀 SmartCloudOps AI - Starting Secure Application")
    print("=" * 50)

    # Check if we're in development mode
    if os.getenv("FLASK_ENV") == "development":
        print("⚠️  Development mode detected")
        print("🔒 For production, use app/main_secure.py directly")
        print()

    # Import and run the secure application
    try:
        from main_secure import app

        print("✅ Secure application loaded successfully")
        print("🌐 Starting Flask development server...")
        print("📊 Application will be available at: http://localhost:5000")
        print("🔑 API endpoints require proper authentication")
        print()

        # Run the application
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=os.getenv("FLASK_DEBUG", "False").lower() == "true",
        )

    except ImportError as e:
        print(f"❌ Error importing secure application: {e}")
        print("🔧 Please ensure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("🔧 Please check your configuration and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()


def create_app():
    """Create Flask application instance"""
    from app.main_secure import app

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
