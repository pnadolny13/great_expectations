from typing import Set

import pytest

import great_expectations.exceptions.exceptions as ge_exceptions
from great_expectations.data_context import DataContext
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.parameter_builder import (
    RegexPatternStringParameterBuilder,
    regex_pattern_string_parameter_builder,
)
from great_expectations.rule_based_profiler.types import (
    Domain,
    ParameterContainer,
    get_parameter_value_by_fully_qualified_parameter_name,
)
from tests.integration.profiling.rule_based_profilers.conftest import (
    alice_columnar_table_single_batch,
    alice_columnar_table_single_batch_context,
    bobby_columnar_table_multi_batch_deterministic_data_context,
)


def test_regex_pattern_string_parameter_builder_instantiation():
    candidate_regexes: Set[str] = {
        r"^\d{1}$",
        r"^\d{2}$",
        r"^\S{8}-\S{4}-\S{4}-\S{4}-\S{12}$",
    }

    regex_pattern_string_parameter: RegexPatternStringParameterBuilder = (
        RegexPatternStringParameterBuilder(
            name="my_simple_regex_string_parameter_builder",
        )
    )

    assert regex_pattern_string_parameter._threshold == 1.0
    assert regex_pattern_string_parameter._candidate_strings == candidate_regexes
    assert regex_pattern_string_parameter.CANDIDATE_STRINGS == candidate_regexes


def test_regex_pattern_string_parameter_builder_zero_batch_id_error():
    regex_pattern_string_parameter: RegexPatternStringParameterBuilder = (
        RegexPatternStringParameterBuilder(
            name="my_simple_regex_string_parameter_builder",
        )
    )
    parameter_container: ParameterContainer = ParameterContainer(parameter_nodes=None)
    domain: Domain = Domain(domain_type=MetricDomainTypes.COLUMN)

    with pytest.raises(ge_exceptions.ProfilerExecutionError) as e:
        regex_pattern_string_parameter.build_parameters(
            parameter_container=parameter_container, domain=domain
        )

    assert (
        str(e.value)
        == "Utilizing a RegexPatternStringParameterBuilder requires a non-empty list of batch identifiers."
    )


def test_regex_pattern_string_parameter_builder_alice(
    alice_columnar_table_single_batch_context,
):
    data_context: DataContext = alice_columnar_table_single_batch_context
    batch_request = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    candidate_strings: Set[str] = {
        r"^\d{1}$",
        r"^\d{2}$",
        r"^\S{8}-\S{4}-\S{4}-\S{4}-\S{12}$",
    }
    metric_domain_kwargs = {"column": "id"}

    regex_pattern_string_parameter: RegexPatternStringParameterBuilder = (
        RegexPatternStringParameterBuilder(
            name="my_regex",
            metric_domain_kwargs=metric_domain_kwargs,
            data_context=data_context,
            batch_request=batch_request,
        )
    )

    assert regex_pattern_string_parameter._candidate_strings == candidate_strings
    assert regex_pattern_string_parameter._threshold == 1.0

    parameter_container: ParameterContainer = ParameterContainer(parameter_nodes=None)
    domain: Domain = Domain(
        domain_type=MetricDomainTypes.COLUMN, domain_kwargs=metric_domain_kwargs
    )
    assert parameter_container.parameter_nodes is None

    regex_pattern_string_parameter._build_parameters(
        parameter_container=parameter_container, domain=domain
    )

    assert len(parameter_container.parameter_nodes) == 1

    fully_qualified_parameter_name_for_value: str = "$parameter.my_regex"
    expected_value: dict = {
        "value": r"^\S{8}-\S{4}-\S{4}-\S{4}-\S{12}$",
        "details": {"success_ratio": 1.0},
    }
    assert (
        get_parameter_value_by_fully_qualified_parameter_name(
            fully_qualified_parameter_name=fully_qualified_parameter_name_for_value,
            domain=domain,
            parameters={domain.id: parameter_container},
        )
        == expected_value
    )


def test_regex_pattern_string_parameter_builder_bobby(
    bobby_columnar_table_multi_batch_deterministic_data_context,
):
    data_context: DataContext = (
        bobby_columnar_table_multi_batch_deterministic_data_context
    )
    metric_domain_kwargs: dict = {"column": "VendorID"}
    candidate_strings: Set[str] = {
        r"^\d{1}$",
        r"^\d{3}$",  # won't match
        r"^\d{4}$",  # won't match
    }
    threshold: float = 0.9
    batch_request: dict = {
        "datasource_name": "taxi_pandas",
        "data_connector_name": "monthly",
        "data_asset_name": "my_reports",
        "data_connector_query": {"index": -1},
    }

    regex_parameter: RegexPatternStringParameterBuilder = (
        RegexPatternStringParameterBuilder(
            name="my_regex_pattern_string_parameter_builder",
            metric_domain_kwargs=metric_domain_kwargs,
            candidate_strings=candidate_strings,
            threshold=threshold,
            data_context=data_context,
            batch_request=batch_request,
        )
    )

    assert regex_parameter.CANDIDATE_STRINGS != candidate_strings
    assert regex_parameter._candidate_strings == candidate_strings
    assert regex_parameter._threshold == 0.9

    parameter_container: ParameterContainer = ParameterContainer(parameter_nodes=None)
    domain: Domain = Domain(
        domain_type=MetricDomainTypes.COLUMN, domain_kwargs=metric_domain_kwargs
    )

    assert parameter_container.parameter_nodes is None

    regex_parameter._build_parameters(
        parameter_container=parameter_container, domain=domain
    )

    assert len(parameter_container.parameter_nodes) == 1

    fully_qualified_parameter_name_for_value: str = (
        "$parameter.my_regex_pattern_string_parameter_builder"
    )
    expected_value: dict = {
        "value": r"^\d{1}$",
        "details": {"success_ratio": 1.0},
    }

    assert (
        get_parameter_value_by_fully_qualified_parameter_name(
            fully_qualified_parameter_name=fully_qualified_parameter_name_for_value,
            domain=domain,
            parameters={domain.id: parameter_container},
        )
        == expected_value
    )


def test_regex_pattern_string_parameter_builder_bobby_no_match(
    bobby_columnar_table_multi_batch_deterministic_data_context,
):
    data_context: DataContext = (
        bobby_columnar_table_multi_batch_deterministic_data_context
    )
    metric_domain_kwargs: dict = {"column": "VendorID"}
    candidate_strings: Set[str] = {
        r"^\d{3}$",  # won't match
    }
    threshold: float = 0.9
    batch_request: dict = {
        "datasource_name": "taxi_pandas",
        "data_connector_name": "monthly",
        "data_asset_name": "my_reports",
        "data_connector_query": {"index": -1},
    }

    regex_parameter: RegexPatternStringParameterBuilder = (
        RegexPatternStringParameterBuilder(
            name="my_regex_pattern_string_parameter_builder",
            metric_domain_kwargs=metric_domain_kwargs,
            candidate_strings=candidate_strings,
            threshold=threshold,
            data_context=data_context,
            batch_request=batch_request,
        )
    )
    parameter_container: ParameterContainer = ParameterContainer(parameter_nodes=None)
    domain: Domain = Domain(
        domain_type=MetricDomainTypes.COLUMN, domain_kwargs=metric_domain_kwargs
    )

    assert parameter_container.parameter_nodes is None

    regex_parameter._build_parameters(
        parameter_container=parameter_container, domain=domain
    )
    assert len(parameter_container.parameter_nodes) == 1

    fully_qualified_parameter_name_for_value: str = (
        "$parameter.my_regex_pattern_string_parameter_builder"
    )
    expected_value: dict = {
        "details": {"success_ratio": 0},
    }

    assert (
        get_parameter_value_by_fully_qualified_parameter_name(
            fully_qualified_parameter_name=fully_qualified_parameter_name_for_value,
            domain=domain,
            parameters={domain.id: parameter_container},
        )
        == expected_value
    )