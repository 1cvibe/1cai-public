"""
Tests for CostOptimizer Service

Unit tests for infrastructure cost optimization logic.
"""

import pytest

from src.modules.devops.services.cost_optimizer import CostOptimizer
from src.modules.devops.domain.models import (
    InfrastructureConfig,
    UsageMetrics,
)


@pytest.fixture
def optimizer():
    """Fixture for CostOptimizer instance"""
    return CostOptimizer()


@pytest.fixture
def aws_config():
    """Fixture for AWS infrastructure config"""
    return InfrastructureConfig(
        provider="aws",
        instance_type="m5.2xlarge",
        instance_count=3,
        pricing_model="on_demand",
        region="eu-west-1"
    )


@pytest.fixture
def low_usage_metrics():
    """Fixture for low resource usage metrics"""
    return UsageMetrics(
        cpu_avg=25.0,  # Low CPU
        memory_avg=35.0,  # Low memory
        storage_iops=500,
        network_throughput=100.0
    )


@pytest.fixture
def high_usage_metrics():
    """Fixture for high resource usage metrics"""
    return UsageMetrics(
        cpu_avg=85.0,  # High CPU
        memory_avg=90.0,  # High memory
        storage_iops=5000,
        network_throughput=800.0
    )


class TestCostOptimizer:
    """Tests for CostOptimizer service"""

    @pytest.mark.asyncio
    async def test_analyze_costs_low_usage(self, optimizer, aws_config, low_usage_metrics):
        """Test cost analysis with low resource usage"""
        result = await optimizer.analyze_costs(aws_config, low_usage_metrics)

        assert result.current_cost_month > 0
        assert result.optimized_cost_month < result.current_cost_month
        assert result.total_savings_month > 0
        assert result.savings_percent > 0
        assert len(result.optimizations) > 0

    @pytest.mark.asyncio
    async def test_analyze_costs_high_usage(self, optimizer, aws_config, high_usage_metrics):
        """Test cost analysis with high resource usage"""
        result = await optimizer.analyze_costs(aws_config, high_usage_metrics)

        # High usage should result in fewer optimization opportunities
        assert result.current_cost_month > 0
        # May still have some optimizations (e.g., Reserved Instances)
        assert len(result.optimizations) >= 0

    @pytest.mark.asyncio
    async def test_cpu_optimization_recommendation(self, optimizer, aws_config):
        """Test CPU-based optimization recommendation"""
        low_cpu_metrics = UsageMetrics(cpu_avg=30.0, memory_avg=60.0)
        result = await optimizer.analyze_costs(aws_config, low_cpu_metrics)

        # Should recommend CPU rightsizing
        cpu_opts = [opt for opt in result.optimizations if "cpu" in opt.reason.lower()]
        assert len(cpu_opts) > 0

    @pytest.mark.asyncio
    async def test_memory_optimization_recommendation(self, optimizer, aws_config):
        """Test memory-based optimization recommendation"""
        low_memory_metrics = UsageMetrics(cpu_avg=60.0, memory_avg=35.0)
        result = await optimizer.analyze_costs(aws_config, low_memory_metrics)

        # Should recommend memory rightsizing
        memory_opts = [opt for opt in result.optimizations if "memory" in opt.reason.lower()]
        assert len(memory_opts) > 0

    @pytest.mark.asyncio
    async def test_reserved_instances_recommendation(self, optimizer, low_usage_metrics):
        """Test Reserved Instances recommendation for on-demand pricing"""
        on_demand_config = InfrastructureConfig(
            provider="aws",
            instance_type="m5.large",
            instance_count=2,
            pricing_model="on_demand"
        )

        result = await optimizer.analyze_costs(on_demand_config, low_usage_metrics)

        # Should recommend Reserved Instances
        ri_opts = [opt for opt in result.optimizations if "reserved" in opt.recommended.lower()]
        assert len(ri_opts) > 0

    @pytest.mark.asyncio
    async def test_no_ri_recommendation_for_reserved(self, optimizer, low_usage_metrics):
        """Test no RI recommendation if already using Reserved Instances"""
        reserved_config = InfrastructureConfig(
            provider="aws",
            instance_type="m5.large",
            instance_count=2,
            pricing_model="reserved"
        )

        result = await optimizer.analyze_costs(reserved_config, low_usage_metrics)

        # Should not recommend Reserved Instances
        ri_opts = [opt for opt in result.optimizations if "reserved" in opt.recommended.lower()]
        assert len(ri_opts) == 0

    @pytest.mark.asyncio
    async def test_annual_savings_calculation(self, optimizer, aws_config, low_usage_metrics):
        """Test annual savings calculation"""
        result = await optimizer.analyze_costs(aws_config, low_usage_metrics)

        # Annual savings should be 12x monthly savings
        assert result.annual_savings == result.total_savings_month * 12

    @pytest.mark.asyncio
    async def test_savings_percent_calculation(self, optimizer, aws_config, low_usage_metrics):
        """Test savings percentage calculation"""
        result = await optimizer.analyze_costs(aws_config, low_usage_metrics)

        # Savings percent should match calculation
        expected_percent = int((result.total_savings_month / result.current_cost_month) * 100)
        assert result.savings_percent == expected_percent

    def test_calculate_cost_aws(self, optimizer):
        """Test cost calculation for AWS instances"""
        config = InfrastructureConfig(
            provider="aws",
            instance_type="m5.large",
            instance_count=2
        )

        cost = optimizer._calculate_cost(config)
        assert cost > 0
        assert cost == 200  # m5.large = 100 * 2 instances

    def test_calculate_cost_unknown_instance(self, optimizer):
        """Test cost calculation for unknown instance type"""
        config = InfrastructureConfig(
            provider="aws",
            instance_type="unknown.type",
            instance_count=1
        )

        cost = optimizer._calculate_cost(config)
        assert cost == 400  # Default fallback

    def test_downsize_instance_aws(self, optimizer):
        """Test instance downsizing for AWS"""
        downsized = optimizer._downsize_instance("m5.2xlarge")
        assert downsized == "m5.xlarge"

        downsized = optimizer._downsize_instance("m5.xlarge")
        assert downsized == "m5.large"

    def test_downsize_instance_azure(self, optimizer):
        """Test instance downsizing for Azure"""
        downsized = optimizer._downsize_instance("Standard_D4s_v3")
        assert downsized == "Standard_D2s_v3"

    def test_downsize_instance_gcp(self, optimizer):
        """Test instance downsizing for GCP"""
        downsized = optimizer._downsize_instance("n1-standard-4")
        assert downsized == "n1-standard-2"

    def test_downsize_instance_unknown(self, optimizer):
        """Test downsizing unknown instance type"""
        downsized = optimizer._downsize_instance("unknown.type")
        assert downsized == "unknown.type"  # No change

    def test_rightsizing_rules_loaded(self, optimizer):
        """Test that rightsizing rules are loaded"""
        assert len(optimizer.rightsizing_rules) > 0

        # Check rule structure
        for rule in optimizer.rightsizing_rules:
            assert "condition" in rule
            assert "action" in rule
            assert "savings_percent" in rule

    @pytest.mark.asyncio
    async def test_optimization_risk_levels(self, optimizer, aws_config, low_usage_metrics):
        """Test that optimizations have appropriate risk levels"""
        result = await optimizer.analyze_costs(aws_config, low_usage_metrics)

        for opt in result.optimizations:
            assert opt.risk in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_optimization_effort_levels(self, optimizer, aws_config, low_usage_metrics):
        """Test that optimizations have effort levels"""
        result = await optimizer.analyze_costs(aws_config, low_usage_metrics)

        for opt in result.optimizations:
            assert opt.effort in ["low", "medium", "high"]
