# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from bson.json_util import dumps

from flask import abort, Blueprint, redirect, url_for, request, Response
from flask.ext.login import login_required, current_user

from ..models import Institute, Variant, Case
from ..extensions import store
from ..helpers import templated

core = Blueprint('core', __name__, template_folder='templates')

SAMPLES = [('123-1-1A', 'male', 'affected', 'Agilent_SureSelect.V5'),
           ('123-2-2A', 'female', 'unaffected', 'Agilent_SureSelect.V5'),
           ('123-2-1A', 'male', 'unaffected', 'Agilent_SureSelect.V5')]


@core.route('/institutes')
@templated('institutes.html')
@login_required
def institutes():
  """View all institutes that the current user belongs to."""
  if len(current_user.institutes) == 1:
    # there no choice of institutes to make, redirect to only institute
    institute = current_user.institutes[0]
    return redirect(url_for('.cases', institute_id=institute.id))

  else:
    return dict(institutes=current_user.institutes)


@core.route('/<institute_id>')
@templated('cases.html')
@login_required
def cases(institute_id):
  """View all cases.

  The purpose of this page is to display all cases related to an
  institute. It should also give an idea of which
  """
  institute = Institute.objects.get_or_404(id=institute_id)

  # fetch cases from the data store
  return dict(institute=institute, institute_id=institute_id)


@core.route('/api/v1/<institute_id>/cases')
@login_required
def api_cases(institute_id):
  institute = Institute.objects.get_or_404(id=institute_id)

  cases_json = dumps([case.to_mongo() for case in institute.cases])

  return Response(cases_json, mimetype='application/json; charset=utf-8')


@core.route('/<institute_id>/<case_id>')
@templated('case.html')
@login_required
def case(institute_id, case_id):
  """View one specific case."""
  institute = Institute.objects.get_or_404(id=institute_id)

  # abort with 404 error if the case doesn't exist
  cases = [case for case in institute.cases if case.display_name == case_id]
  if len(cases) == 0:
    return abort(404)

  case = cases[0]

  # fetch a single, specific case from the data store
  return dict(institute=institute, case=case, samples=SAMPLES)


@core.route('/<institute_id>/<case_id>/variants')
@templated('variants.html')
@login_required
def variants(institute_id, case_id):
  """View all variants for a single case."""
  # fetch all variants for a specific case
  skip = int(request.args.get('skip', 0))

  return dict(variants=store.variants('1'),  # case_id
              case_id=case_id,
              institute_id=institute_id,
              current_batch=(skip + 100))


@core.route('/<institute_id>/<case_id>/variants/<variant_id>')
@templated('variant.html')
@login_required
def variant(institute_id, case_id, variant_id):
  """View a single variant in a single case."""
  return dict(
    institute_id=institute_id,
    case_id=case_id,
    variant_id=variant_id,
    variant=Variant.objects.first()
  )
