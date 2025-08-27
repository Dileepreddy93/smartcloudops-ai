#!/usr/bin/env python3
"""
SmartCloudOps AI - Base Service
================================

Base service class providing common functionality for all services.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base service class providing common functionality."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the base service."""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the service. Returns True if successful."""
        try:
            self._initialize_service()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            return False

    @abstractmethod
    def _initialize_service(self) -> None:
        """Initialize the specific service. Override in subclasses."""
        pass

    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the service."""
        return {
            "service": self.__class__.__name__,
            "status": "healthy" if self._initialized else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "initialized": self._initialized,
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an operation for audit purposes."""
        log_data = {
            "operation": operation,
            "service": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        self.logger.info(f"Operation: {operation}", extra=log_data)


class ServiceRegistry:
    """Registry for managing service instances."""

    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    def register(self, name: str, service: BaseService) -> None:
        """Register a service with the registry."""
        self._services[name] = service
        logger.info(f"Registered service: {name}")

    def get(self, name: str) -> Optional[BaseService]:
        """Get a service by name."""
        return self._services.get(name)

    def get_all(self) -> Dict[str, BaseService]:
        """Get all registered services."""
        return self._services.copy()

    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered services."""
        results = {}
        for name, service in self._services.items():
            results[name] = service.initialize()
        return results

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on all services."""
        return {name: service.health_check() for name, service in self._services.items()}


# Global service registry
service_registry = ServiceRegistry()
