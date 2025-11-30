# Nested Learning Module

## Overview
This module implements the Nested Learning paradigm, including the Continuum Memory System (CMS) and Self-Referential Optimization.

## Architecture
Follows Clean Architecture principles:
- `domain/`: Core entities and business rules (OptimizationCriteria, SuccessPattern).
- `services/`: Application logic (MetaOptimizer, ProviderSelector).
- `api/`: Interface adapters (not yet implemented).

## Components
- **MetaOptimizer**: Self-modifying optimizer that adjusts selection criteria based on historical patterns.
- **ProviderSelector**: Adaptive provider selector that uses CMS and MetaOptimizer to choose the best LLM provider.
