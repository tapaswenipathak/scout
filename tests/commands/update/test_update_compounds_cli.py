# -*- coding: utf-8 -*-

from scout.commands import app_cli
from scout.server.extensions import store

def test_update_compounds(mock_app, case_obj):
    """Tests the CLI that updates all compounds for a case"""

    runner = mock_app.test_cli_runner()
    assert runner

    # Test CLI base, no arguments provided
    result =  runner.invoke(app_cli, ['update', 'compounds'])
    # it should return error message
    assert 'Missing argument "case_id"' in result.output

    # Provide case_id of a case not in database
    result =  runner.invoke(app_cli, ['update', 'compounds',
        'unknown_case_id'
    ])
    # it should return error message
    assert 'Case unknown_case_id could not be found' in result.output

    # Provide case_id of an existing case
    result =  runner.invoke(app_cli, ['update', 'compounds',
        case_obj['_id']
    ])
    # command should work
    assert result.exit_code == 0
    assert 'All compounds updated' in result.output