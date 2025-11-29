"""API endpoints для управления правилами AI"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.ai_rule import AIRule, RiskType
from app.schemas.ai_rule import (
    AIRuleCreate,
    AIRuleRead,
    AIRuleUpdate,
    AIRulePreviewRequest,
    AIRulePreviewResponse,
    AIRuleBatchActionRequest,
)
from app.services import ai_rule_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/ai/rules", response_model=list[AIRuleRead], summary="Список правил AI")
def list_rules(
    riskType: RiskType | None = Query(default=None, alias="riskType", description="Фильтр по типу риска"),
    isEnabled: bool | None = Query(default=None, alias="isEnabled", description="Фильтр по статусу (включено/выключено)"),
    tags: str | None = Query(default=None, description="Фильтр по тегам (через запятую)"),
    search: str | None = Query(default=None, description="Поиск по названию или описанию"),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[AIRuleRead]:
    """Получить список правил AI с фильтрами"""
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    rules = ai_rule_service.list_rules(
        db,
        risk_type=riskType,
        is_enabled=isEnabled,
        tags=tags_list,
        search=search,
    )
    return [AIRuleRead.model_validate(rule) for rule in rules]


@router.get("/ai/rules/{rule_id}", response_model=AIRuleRead, summary="Детали правила")
def get_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> AIRuleRead:
    """Получить правило по ID"""
    rule = ai_rule_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return AIRuleRead.model_validate(rule)


@router.post("/ai/rules", response_model=AIRuleRead, status_code=201, summary="Создать правило")
def create_rule(
    data: AIRuleCreate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> AIRuleRead:
    """Создать новое правило AI"""
    rule = ai_rule_service.create_rule(db, data)
    return AIRuleRead.model_validate(rule)


@router.patch("/ai/rules/{rule_id}", response_model=AIRuleRead, summary="Обновить правило")
def update_rule(
    rule_id: uuid.UUID,
    data: AIRuleUpdate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> AIRuleRead:
    """Обновить правило AI"""
    rule = ai_rule_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule = ai_rule_service.update_rule(db, rule, data)
    return AIRuleRead.model_validate(rule)


@router.delete("/ai/rules/{rule_id}", status_code=204, summary="Удалить правило")
def delete_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    """Удалить правило AI"""
    rule = ai_rule_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    ai_rule_service.delete_rule(db, rule)
    return None


@router.post("/ai/rules/{rule_id}/preview", response_model=AIRulePreviewResponse, summary="Предпросмотр ответа AI")
def preview_rule(
    rule_id: uuid.UUID,
    payload: AIRulePreviewRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> AIRulePreviewResponse:
    """Предпросмотр ответа AI на основе правила"""
    rule = ai_rule_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    preview = ai_rule_service.preview_rule_response(rule, payload.test_scenario)
    
    return AIRulePreviewResponse(
        ruleId=rule.id,
        ruleName=rule.name,
        wouldTrigger=preview.get("wouldTrigger", False),
        previewResponse=preview,
    )


@router.post("/ai/rules/batch", summary="Массовые действия над правилами")
def batch_action(
    payload: AIRuleBatchActionRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> dict:
    """Массовые действия над правилами (включение/отключение, теги)"""
    if payload.action not in ["enable", "disable", "add_tags", "remove_tags"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if payload.action in ["add_tags", "remove_tags"] and not payload.tags:
        raise HTTPException(status_code=400, detail="Tags required for this action")
    
    updated_count = ai_rule_service.batch_update_rules(
        db,
        rule_ids=payload.rule_ids,
        action=payload.action,
        tags=payload.tags,
    )
    
    return {"updated": updated_count}

