# -*- coding: utf-8 -*-
import pytest
from pprint import pprint as pp
from scout.exceptions import (PedigreeError, ConfigError, IntegrityError)

from scout.build import build_case


def test_build_case(parsed_case, panel_database):
    adapter = panel_database

    # GIVEN a parsed case
    # WHEN bulding a case model
    case_obj = build_case(parsed_case, adapter)

    # THEN make sure it is built in the proper way
    assert case_obj['_id'] == parsed_case['case_id']
    assert case_obj['display_name'] == parsed_case['display_name']
    assert case_obj['owner'] == parsed_case['owner']
    assert case_obj['collaborators'] == parsed_case['collaborators']
    assert len(case_obj['individuals']) == len(parsed_case['individuals'])
    assert case_obj['synopsis'] == ''

    assert case_obj['status'] == 'inactive'
    assert case_obj['is_research'] == False
    assert case_obj['research_requested'] == False
    assert case_obj['rerun_requested'] == False

    assert case_obj['analysis_date'] == parsed_case['analysis_date']

    assert len(case_obj['dynamic_gene_list']) == 0

    assert case_obj['genome_build'] == parsed_case['genome_build']

    assert case_obj['rank_model_version'] == parsed_case['rank_model_version']
    assert case_obj['rank_score_threshold'] == parsed_case['rank_score_threshold']
    assert case_obj['sv_rank_model_version'] == parsed_case['sv_rank_model_version']

    assert case_obj['madeline_info'] == parsed_case['madeline_info']

    assert case_obj['delivery_report'] == parsed_case['delivery_report']

    for vcf in case_obj['vcf_files']:
        assert vcf in parsed_case['vcf_files']

    # assert case_obj['diagnosis_phenotypes'] == []
    # assert case_obj['diagnosis_genes'] == []

    if (parsed_case['vcf_files'].get('vcf_sv') or parsed_case['vcf_files'].get('vcf_sv_research')):
        assert case_obj['has_svvariants'] == True
    else:
        assert case_obj['has_svvariants'] == False


def test_build_minimal_case(institute_database):
    # GIVEN a case without case id
    case_info = {
        'case_id': 'test-case',
        'owner': 'cust000'
    }
    # WHEN case is built
    case_obj = build_case(case_info, institute_database)
    # THEN assert that it worked
    assert case_obj['_id'] == case_info['case_id']


def test_build_case_no_case_id(adapter):
    # GIVEN a case without case id
    case_info = {}

    # WHEN case is built
    # THEN a PedigreeError should be raised
    with pytest.raises(Exception):
        build_case(case_info, adapter)


def test_build_case_no_display_name(institute_database):
    # GIVEN a case without case id
    case_info = {
        'case_id': 'test-case',
        'owner': 'cust000'
    }
    # WHEN case is built
    case_obj = build_case(case_info, institute_database)
    # THEN assert that display_name was set to case_id
    assert case_obj['display_name'] == case_info['case_id']


def test_build_case_no_owner(institute_database):
    # GIVEN a case where owner does not exist in the database
    case_info = {
        'case_id': 'test-case',
        'owner': 'cust001'
    }
    # WHEN case is built
    # THEN a IntegrityError should be raised since the owner has to exist in the database
    with pytest.raises(IntegrityError):
        case_obj = build_case(case_info, institute_database)


def test_build_case_non_existing_owner(institute_database):
    # GIVEN a case without owner
    # GIVEN a case where owner does not exist in the database
    case_info = {
        'case_id': 'test-case',
    }
    # WHEN case is built
    # THEN a ConfigError should be raised since a case has to have a owner
    with pytest.raises(ConfigError):
        case_obj = build_case(case_info, institute_database)

# def test_build_case_config(parsed_case):
#     case_obj = build_case(parsed_case)
#     print(case_obj.to_json())
#     assert False
