"""
SQL Optimizer API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from src.modules.auth.api.dependencies import get_current_user
from src.modules.sql_optimizer.domain.models import (
    OptimizedQuery,
    QueryAnalysis,
    SQLQuery,
)
from src.modules.sql_optimizer.services.query_analyzer import QueryAnalyzer
from src.modules.sql_optimizer.services.query_rewriter import QueryRewriter
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/sql_optimizer", tags=["SQL Optimizer"])


def get_query_analyzer():
    return QueryAnalyzer()


def get_query_rewriter():
    return QueryRewriter()


@router.post(
    "/analyze",
    response_model=QueryAnalysis,
    summary="Analyze SQL query",
    description="Analyze SQL query for complexity, anti-patterns, and missing indexes",
)
async def analyze_query(
    query: SQLQuery,
    current_user=Depends(get_current_user),
    analyzer: QueryAnalyzer = Depends(get_query_analyzer),
):
    """
    Analyze SQL query
    """
    try:
        logger.info(
            "Analyzing SQL query",
            user_id=current_user.id,
            query_type=query.query_type,
        )
        return await analyzer.analyze_query(query)
    except Exception as e:
        logger.error("Failed to analyze query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/rewrite",
    response_model=OptimizedQuery,
    summary="Rewrite and optimize SQL query",
    description="Rewrite SQL query to fix anti-patterns and improve performance",
)
async def rewrite_query(
    query: SQLQuery,
    current_user=Depends(get_current_user),
    analyzer: QueryAnalyzer = Depends(get_query_analyzer),
    rewriter: QueryRewriter = Depends(get_query_rewriter),
):
    """
    Rewrite and optimize SQL query
    """
    try:
        logger.info(
            "Rewriting SQL query",
            user_id=current_user.id,
            query_type=query.query_type,
        )
        # First analyze
        analysis = await analyzer.analyze_query(query)
        
        # Then rewrite
        return await rewriter.rewrite_query(query, analysis)
    except Exception as e:
        logger.error("Failed to rewrite query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
