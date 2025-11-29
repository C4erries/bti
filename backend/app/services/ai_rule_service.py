"""Сервис для работы с правилами AI"""
from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.ai_rule import AIRule, RiskType
from app.schemas.ai_rule import AIRuleCreate, AIRuleUpdate
from fastapi import HTTPException


def list_rules(
    db: Session,
    risk_type: RiskType | None = None,
    is_enabled: bool | None = None,
    tags: list[str] | None = None,
    search: str | None = None,
) -> list[AIRule]:
    """Получить список правил с фильтрами"""
    query = select(AIRule)
    
    conditions = []
    
    if risk_type:
        conditions.append(AIRule.risk_type == risk_type)
    
    if is_enabled is not None:
        conditions.append(AIRule.is_enabled == is_enabled)
    
    if tags:
        # Фильтр по тегам: правило должно содержать хотя бы один из указанных тегов
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(AIRule.tags.contains([tag]))
        if tag_conditions:
            conditions.append(or_(*tag_conditions))
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                AIRule.name.ilike(search_pattern),
                AIRule.description.ilike(search_pattern),
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(AIRule.priority.desc(), AIRule.created_at.desc())
    
    return list(db.scalars(query).all())


def get_rule(db: Session, rule_id: uuid.UUID) -> AIRule | None:
    """Получить правило по ID"""
    return db.get(AIRule, rule_id)


def create_rule(db: Session, data: AIRuleCreate) -> AIRule:
    """Создать новое правило"""
    rule = AIRule(
        name=data.name,
        trigger_condition=data.trigger_condition,
        risk_type=data.risk_type,
        description=data.description,
        severity=data.severity,
        risk_zone=data.risk_zone,
        is_enabled=data.is_enabled,
        priority=data.priority,
        tags=data.tags or [],
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: AIRule, data: AIRuleUpdate) -> AIRule:
    """Обновить правило"""
    if data.name is not None:
        rule.name = data.name
    if data.trigger_condition is not None:
        rule.trigger_condition = data.trigger_condition
    if data.risk_type is not None:
        rule.risk_type = data.risk_type
    if data.description is not None:
        rule.description = data.description
    if data.severity is not None:
        rule.severity = data.severity
    if data.risk_zone is not None:
        rule.risk_zone = data.risk_zone
    if data.is_enabled is not None:
        rule.is_enabled = data.is_enabled
    if data.priority is not None:
        rule.priority = data.priority
    if data.tags is not None:
        rule.tags = data.tags
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule: AIRule) -> None:
    """Удалить правило"""
    db.delete(rule)
    db.commit()


def batch_update_rules(
    db: Session,
    rule_ids: list[uuid.UUID],
    action: str,
    tags: list[str] | None = None,
) -> int:
    """Массовое обновление правил"""
    rules = db.scalars(select(AIRule).where(AIRule.id.in_(rule_ids))).all()
    
    updated_count = 0
    for rule in rules:
        if action == "enable":
            rule.is_enabled = True
            updated_count += 1
        elif action == "disable":
            rule.is_enabled = False
            updated_count += 1
        elif action == "add_tags" and tags:
            existing_tags = rule.tags or []
            for tag in tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            rule.tags = existing_tags
            updated_count += 1
        elif action == "remove_tags" and tags:
            existing_tags = rule.tags or []
            rule.tags = [t for t in existing_tags if t not in tags]
            updated_count += 1
    
    if updated_count > 0:
        db.commit()
    
    return updated_count


def preview_rule_response(rule: AIRule, test_scenario: dict) -> dict:
    """Предпросмотр ответа AI на основе правила (заглушка)"""
    # В реальной реализации здесь должна быть логика проверки условия правила
    # и формирования ответа AI. Пока возвращаем заглушку.
    would_trigger = True  # Упрощенная логика
    
    preview = {
        "ruleId": str(rule.id),
        "ruleName": rule.name,
        "risk": {
            "type": rule.risk_type.value,
            "description": rule.description,
            "severity": rule.severity,
            "zone": rule.risk_zone,
        },
        "wouldTrigger": would_trigger,
        "testScenario": test_scenario,
    }
    
    return preview

