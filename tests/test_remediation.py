from app.services.remediation_service import (
    AutoRemediationEngine,
    RemediationRule,
    RemediationAction,
)


def test_remediation_engine_initialization():
    """Test that the remediation engine initializes correctly."""
    engine = AutoRemediationEngine()

    assert engine.is_enabled == True
    assert engine.manual_override == False
    assert len(engine.rules) == 5  # Default rules
    assert len(engine.action_history) == 0


def test_remediation_engine_status():
    """Test getting remediation engine status."""
    engine = AutoRemediationEngine()

    status = engine.get_status()

    assert "enabled" in status
    assert "manual_override" in status
    assert "total_rules" in status
    assert "enabled_rules" in status
    assert "total_actions" in status
    assert "recent_actions" in status
    assert "rules" in status


def test_remediation_rule_creation():
    """Test creating a remediation rule."""
    rule = RemediationRule(
        name="Test Rule",
        conditions={"cpu_percent": {"threshold": 80}},
        actions=[RemediationAction.SEND_ALERT],
        priority=1,
        cooldown_minutes=5,
    )

    assert rule.name == "Test Rule"
    assert rule.enabled == True
    assert rule.priority == 1
    assert rule.cooldown_minutes == 5
    assert len(rule.actions) == 1
    assert rule.actions[0] == RemediationAction.SEND_ALERT
