"""
SmartCloudOps AI - Phase 5: NLP Enhanced ChatOps Service
=======================================================

Advanced natural language processing for DevOps ChatOps commands.
Supports intent recognition and entity extraction for AWS operations.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import boto3
import nltk
import spacy

# Set environment variables to limit resource usage
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)


class NLPEnhancedChatOps:
    """
    Advanced NLP-powered ChatOps service for DevOps operations.
    Optimized for CPU usage and test environments.
    """

    def __init__(self, use_lightweight_model=True):
        """Initialize the NLP ChatOps service."""
        # Use lightweight spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic text processing")
            self.nlp = None

        # Use lightweight approach instead of heavy transformer
        self.use_lightweight_model = use_lightweight_model
        if not use_lightweight_model:
            try:
                from transformers import pipeline

                self.intent_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1,  # CPU only
                )
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                self.use_lightweight_model = True

        # Define DevOps intents and their patterns
        self.devops_intents = {
            "deploy": {
                "patterns": [
                    r"deploy\s+(?:the\s+)?(?:\w+\s+)?(?:app|application|service)(?:\s+to\s+\w+)?",
                    r"push\s+(?:to\s+)?(?:production|staging)",
                    r"release\s+(?:the\s+)?(?:app|application)",
                ],
                "entities": ["app_name", "environment", "version"],
            },
            "scale": {
                "patterns": [
                    r"scale\s+(?:servers?|instances?|resources?)\s+(?:to\s+)?(\d+)",
                    r"increase\s+(?:capacity|instances?)\s+(?:to\s+)?(\d+)",
                    r"decrease\s+(?:capacity|instances?)\s+(?:to\s+)?(\d+)",
                ],
                "entities": ["count", "resource_type", "direction"],
            },
            "monitor": {
                "patterns": [
                    r"show\s+(?:logs?|metrics?|status)\s+(?:of\s+)?(\w+)",
                    r"check\s+(?:health|status)\s+(?:of\s+)?(\w+)",
                    r"get\s+(?:logs?|metrics?)\s+(?:for\s+)?(\w+)",
                ],
                "entities": ["service_name", "metric_type", "time_range"],
            },
            "restart": {
                "patterns": [
                    r"restart\s+(?:the\s+)?(?:service|app|application|server)",
                    r"reboot\s+(?:the\s+)?(?:instance|server)",
                    r"stop\s+(?:and\s+)?start\s+(?:the\s+)?(?:service)",
                ],
                "entities": ["service_name", "instance_id"],
            },
            "backup": {
                "patterns": [
                    r"create\s+(?:a\s+)?backup\s+(?:of\s+)?(\w+)",
                    r"backup\s+(?:the\s+)?(?:database|data)",
                    r"save\s+(?:a\s+)?backup",
                ],
                "entities": ["resource_name", "backup_type"],
            },
            "security": {
                "patterns": [
                    r"check\s+(?:security|vulnerabilities)",
                    r"scan\s+(?:for\s+)?(?:threats|vulnerabilities)",
                    r"audit\s+(?:security|compliance)",
                ],
                "entities": ["scan_type", "target"],
            },
            "cost": {
                "patterns": [
                    r"show\s+(?:cost|billing|expenses)",
                    r"check\s+(?:cost|billing)\s+(?:for\s+)?(\w+)",
                    r"get\s+(?:cost|billing)\s+(?:report)",
                ],
                "entities": ["service_name", "time_period"],
            },
            "compliance": {
                "patterns": [
                    r"check\s+(?:compliance|audit)",
                    r"run\s+(?:compliance|audit)\s+(?:check)",
                    r"verify\s+(?:compliance|standards)",
                ],
                "entities": ["compliance_type", "framework"],
            },
            "alert": {
                "patterns": [
                    r"set\s+(?:up\s+)?(?:alert|notification)",
                    r"configure\s+(?:alert|notification)",
                    r"create\s+(?:alert|notification)",
                ],
                "entities": ["alert_type", "threshold", "channel"],
            },
            "rollback": {
                "patterns": [
                    r"rollback\s+(?:to\s+)?(?:version|deployment|previous\s+version)",
                    r"revert\s+(?:to\s+)?(?:previous|last)\s+(?:version)",
                    r"undo\s+(?:deployment|changes)",
                ],
                "entities": ["version", "reason"],
            },
        }

        # Initialize AWS clients (mock for testing)
        try:
            self.ec2_client = boto3.client("ec2", region_name="us-east-1")
            self.cloudwatch_client = boto3.client("cloudwatch", region_name="us-east-1")
            self.s3_client = boto3.client("s3", region_name="us-east-1")
        except Exception as e:
            logger.warning(f"AWS clients not configured: {e}")
            self.ec2_client = None
            self.cloudwatch_client = None
            self.s3_client = None

        # Command execution history
        self.command_history = []

    def process_command(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language command and return structured response.

        Args:
            user_input: Natural language command from user

        Returns:
            Dict containing intent, entities, and action plan
        """
        try:
            # Clean and normalize input
            cleaned_input = self._preprocess_input(user_input)

            # Detect intent
            intent = self._detect_intent(cleaned_input)

            # Extract entities
            entities = self._extract_entities(cleaned_input, intent)

            # Generate action plan
            action_plan = self._generate_action_plan(intent, entities)

            # Log command
            self._log_command(user_input, intent, entities, action_plan)

            return {
                "status": "success",
                "original_input": user_input,
                "cleaned_input": cleaned_input,
                "intent": intent,
                "entities": entities,
                "action_plan": action_plan,
                "confidence": self._calculate_confidence(intent, entities),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "status": "error",
                "error": str(e),
                "original_input": user_input,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _preprocess_input(self, text: str) -> str:
        """Preprocess and normalize input text."""
        # Convert to lowercase
        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep important ones
        text = re.sub(r"[^\w\s\-\.]", "", text)

        return text

    def _detect_intent(self, text: str) -> str:
        """Detect the intent of the command using pattern matching and NLP."""
        # First, try pattern matching for exact matches
        for intent, config in self.devops_intents.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent

        # If no pattern match and transformer is available, use it
        if not self.use_lightweight_model and hasattr(self, "intent_classifier"):
            try:
                # Prepare candidate labels for classification
                candidate_labels = list(self.devops_intents.keys())

                # Use zero-shot classification with correct API
                result = self.intent_classifier(text, candidate_labels)

                if result and len(result) > 0:
                    return result["labels"][0]  # Correct API usage
            except Exception as e:
                logger.warning(f"Transformer classification failed: {e}")

        # Default to general query if no intent detected
        return "query"

    def _extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract entities from the text using spaCy and regex."""
        entities = {}

        # Use spaCy for general entity extraction if available
        if self.nlp:
            doc = self.nlp(text)

            # Extract numbers
            numbers = [token.text for token in doc if token.like_num]
            if numbers:
                entities["numbers"] = numbers

            # Extract named entities
            for ent in doc.ents:
                entities[ent.label_.lower()] = ent.text
        else:
            # Fallback to regex for numbers
            numbers = re.findall(r"\d+", text)
            if numbers:
                entities["numbers"] = numbers

        # Intent-specific entity extraction
        if intent in self.devops_intents:
            intent_config = self.devops_intents[intent]

            # Extract entities based on intent patterns
            for pattern in intent_config["patterns"]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for i, match in enumerate(matches):
                        if isinstance(match, tuple):
                            for j, group in enumerate(match):
                                if group:
                                    entity_name = (
                                        intent_config["entities"][j] if j < len(intent_config["entities"]) else f"entity_{j}"
                                    )
                                    entities[entity_name] = group
                        else:
                            entity_name = intent_config["entities"][i] if i < len(intent_config["entities"]) else f"entity_{i}"
                            entities[entity_name] = match

        return entities

    def _generate_action_plan(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate action plan based on intent and entities."""
        action_plan = {
            "action": intent,
            "parameters": entities,
            "aws_operations": [],
            "safety_checks": [],
            "estimated_time": "30s",
        }

        if intent == "deploy":
            action_plan["aws_operations"] = [
                "codebuild:start_build",
                "codedeploy:create_deployment",
            ]
            action_plan["safety_checks"] = [
                "check_deployment_approval",
                "validate_environment",
            ]
            action_plan["estimated_time"] = "5m"

        elif intent == "scale":
            count = entities.get(
                "count",
                entities.get("numbers", [1])[0] if entities.get("numbers") else 1,
            )
            action_plan["aws_operations"] = [
                f"autoscaling:set_desired_capacity (count={count})",
                "ec2:describe_auto_scaling_groups",
            ]
            action_plan["safety_checks"] = [
                "validate_scale_limits",
                "check_cost_impact",
            ]
            action_plan["estimated_time"] = "2m"

        elif intent == "monitor":
            service = entities.get("service_name", "all")
            action_plan["aws_operations"] = [
                f"cloudwatch:get_metric_data (service={service})",
                "logs:describe_log_groups",
            ]
            action_plan["safety_checks"] = ["check_monitoring_permissions"]
            action_plan["estimated_time"] = "30s"

        elif intent == "restart":
            service = entities.get("service_name", "default")
            action_plan["aws_operations"] = [
                f"ec2:reboot_instances (service={service})",
                "ecs:update_service",
            ]
            action_plan["safety_checks"] = [
                "check_service_health",
                "validate_restart_approval",
            ]
            action_plan["estimated_time"] = "3m"

        elif intent == "backup":
            resource = entities.get("resource_name", "database")
            action_plan["aws_operations"] = [
                f"rds:create_db_snapshot (resource={resource})",
                "s3:put_object (backup)",
            ]
            action_plan["safety_checks"] = [
                "check_backup_space",
                "validate_backup_permissions",
            ]
            action_plan["estimated_time"] = "10m"

        elif intent == "security":
            action_plan["aws_operations"] = [
                "guardduty:list_findings",
                "securityhub:get_findings",
            ]
            action_plan["safety_checks"] = ["check_security_permissions"]
            action_plan["estimated_time"] = "2m"

        elif intent == "cost":
            action_plan["aws_operations"] = [
                "ce:get_cost_and_usage",
                "budgets:describe_budgets",
            ]
            action_plan["safety_checks"] = ["check_billing_permissions"]
            action_plan["estimated_time"] = "1m"

        elif intent == "compliance":
            action_plan["aws_operations"] = [
                "config:get_compliance_details_by_config_rule",
                "securityhub:get_findings",
            ]
            action_plan["safety_checks"] = ["check_compliance_permissions"]
            action_plan["estimated_time"] = "3m"

        elif intent == "alert":
            action_plan["aws_operations"] = [
                "cloudwatch:put_metric_alarm",
                "sns:create_topic",
            ]
            action_plan["safety_checks"] = ["validate_alert_configuration"]
            action_plan["estimated_time"] = "2m"

        elif intent == "rollback":
            action_plan["aws_operations"] = [
                "codedeploy:create_deployment (rollback)",
                "ecs:update_service (previous_version)",
            ]
            action_plan["safety_checks"] = [
                "check_rollback_approval",
                "validate_previous_version",
            ]
            action_plan["estimated_time"] = "5m"

        return action_plan

    def _calculate_confidence(self, intent: str, entities: Dict[str, Any]) -> float:
        """Calculate confidence score for the intent detection."""
        confidence = 0.5  # Base confidence

        # Increase confidence based on entity extraction
        if entities:
            confidence += 0.2

        # Increase confidence for specific intents with good entity coverage
        if intent in self.devops_intents:
            intent_config = self.devops_intents[intent]
            expected_entities = intent_config.get("entities", [])
            found_entities = len([k for k in entities.keys() if k in expected_entities])

            if found_entities > 0:
                confidence += (found_entities / len(expected_entities)) * 0.3

        return min(confidence, 1.0)

    def _log_command(
        self,
        original_input: str,
        intent: str,
        entities: Dict[str, Any],
        action_plan: Dict[str, Any],
    ):
        """Log the processed command for audit and analytics."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "original_input": original_input,
            "intent": intent,
            "entities": entities,
            "action_plan": action_plan,
            "confidence": self._calculate_confidence(intent, entities),
        }

        self.command_history.append(log_entry)

        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]

        logger.info(f"NLP ChatOps Command: {log_entry}")

    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history."""
        return self.command_history[-limit:] if self.command_history else []

    def get_intent_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected intents."""
        if not self.command_history:
            return {"total_commands": 0, "intents": {}}

        intent_counts: dict = {}
        total_commands = len(self.command_history)

        for entry in self.command_history:
            intent = entry.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        return {
            "total_commands": total_commands,
            "intents": intent_counts,
            "success_rate": len([e for e in self.command_history if e.get("confidence", 0) > 0.7]) / total_commands,
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the NLP service."""
        try:
            # Test spaCy
            self.nlp("test")

            # Test transformer with correct syntax
            self.intent_classifier("test")

            return {
                "status": "healthy",
                "spacy_loaded": True,
                "transformer_loaded": True,
                "total_commands_processed": len(self.command_history),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global instance for the service
nlp_chatops_service = NLPEnhancedChatOps()
