"""Tests for zsdatafetch model dataclasses."""

from zsdatafetch.models import (
  ZSComponent,
  ZSIncident,
  ZSIncidentUpdate,
  ZSMaintenance,
  ZSMaintenanceUpdate,
  ZSPage,
  ZSStatus,
  ZSSummary,
)

# ---- ZSPage ----

def test_page_from_dict():
  data = {
    'id': 'abc123',
    'name': 'Zwift, Inc',
    'url': 'https://status.zwift.com',
    'time_zone': 'America/Los_Angeles',
    'updated_at': '2024-01-01T00:00:00.000Z',
  }
  page = ZSPage.from_dict(data)
  assert page.id == 'abc123'
  assert page.name == 'Zwift, Inc'
  assert page.url == 'https://status.zwift.com'
  assert page.time_zone == 'America/Los_Angeles'
  assert page.updated_at == '2024-01-01T00:00:00.000Z'


def test_page_from_dict_empty():
  page = ZSPage.from_dict({})
  assert page.id == ''
  assert page.name == ''


def test_page_extras():
  data = {'id': 'x', 'name': 'Y', 'unknown_field': 'val'}
  page = ZSPage.from_dict(data)
  assert page.extras() == {'unknown_field': 'val'}


def test_page_asdict():
  page = ZSPage(id='x', name='Y')
  d = page.asdict()
  assert d['id'] == 'x'
  assert '_extra' not in d
  assert '_excluded' not in d


def test_page_from_fixture(summary_data):
  page = ZSPage.from_dict(summary_data['page'])
  assert page.name == 'Zwift, Inc'
  assert page.id != ''


# ---- ZSStatus ----

def test_status_from_dict():
  data = {
    'indicator': 'none',
    'description': 'All Systems Operational',
  }
  status = ZSStatus.from_dict(data)
  assert status.indicator == 'none'
  assert status.description == 'All Systems Operational'


def test_status_from_dict_empty():
  status = ZSStatus.from_dict({})
  assert status.indicator == ''


def test_status_extras():
  data = {'indicator': 'none', 'description': 'OK', 'new': 1}
  status = ZSStatus.from_dict(data)
  assert status.extras() == {'new': 1}


def test_status_asdict():
  status = ZSStatus(indicator='none', description='OK')
  d = status.asdict()
  assert d['indicator'] == 'none'
  assert '_extra' not in d


# ---- ZSComponent ----

def test_component_from_dict():
  data = {
    'id': 'comp1',
    'name': 'Game',
    'status': 'operational',
    'description': None,
    'position': 1,
    'created_at': '2020-01-01T00:00:00.000Z',
    'updated_at': '2024-01-01T00:00:00.000Z',
    'group_id': None,
    'group': False,
    'only_show_if_degraded': False,
    'components': [],
    'showcase': True,
    'start_date': None,
    'page_id': 'page1',
  }
  comp = ZSComponent.from_dict(data)
  assert comp.id == 'comp1'
  assert comp.name == 'Game'
  assert comp.status == 'operational'
  assert comp.group is False
  assert comp.page_id == 'page1'


def test_component_group_from_dict():
  data = {
    'id': 'grp1',
    'name': 'Web Group',
    'status': 'operational',
    'group': True,
    'components': ['c1', 'c2', 'c3'],
  }
  comp = ZSComponent.from_dict(data)
  assert comp.group is True
  assert comp.components == ['c1', 'c2', 'c3']


def test_component_from_dict_empty():
  comp = ZSComponent.from_dict({})
  assert comp.id == ''
  assert comp.name == ''
  assert comp.components == []


def test_component_extras():
  data = {'id': 'x', 'new_field': 'abc'}
  comp = ZSComponent.from_dict(data)
  assert comp.extras() == {'new_field': 'abc'}


def test_component_asdict():
  comp = ZSComponent(id='x', name='Y')
  d = comp.asdict()
  assert d['id'] == 'x'
  assert '_extra' not in d


def test_component_from_fixture(summary_data):
  comps = summary_data.get('components', [])
  assert len(comps) > 0
  comp = ZSComponent.from_dict(comps[0])
  assert comp.id != ''
  assert comp.name != ''


# ---- ZSIncidentUpdate ----

def test_incident_update_from_dict():
  data = {
    'id': 'upd1',
    'status': 'resolved',
    'body': 'All fixed now.',
    'incident_id': 'inc1',
    'created_at': '2024-01-01T00:00:00.000Z',
    'updated_at': '2024-01-01T00:00:00.000Z',
    'display_at': '2024-01-01T00:00:00.000Z',
    'affected_components': [
      {'code': 'comp1', 'name': 'Game', 'old_status': 'major_outage', 'new_status': 'operational'},
    ],
    'deliver_notifications': True,
    'custom_tweet': None,
    'tweet_id': None,
  }
  upd = ZSIncidentUpdate.from_dict(data)
  assert upd.id == 'upd1'
  assert upd.status == 'resolved'
  assert upd.body == 'All fixed now.'
  assert upd.deliver_notifications is True
  assert len(upd.affected_components) == 1


def test_incident_update_from_dict_empty():
  upd = ZSIncidentUpdate.from_dict({})
  assert upd.id == ''
  assert upd.affected_components == []


def test_incident_update_extras():
  data = {'id': 'x', 'new_field': 123}
  upd = ZSIncidentUpdate.from_dict(data)
  assert upd.extras() == {'new_field': 123}


# ---- ZSIncident ----

def test_incident_from_dict():
  data = {
    'id': 'inc1',
    'name': 'Game Down',
    'status': 'resolved',
    'created_at': '2024-01-01T00:00:00.000Z',
    'updated_at': '2024-01-01T01:00:00.000Z',
    'monitoring_at': None,
    'resolved_at': '2024-01-01T01:00:00.000Z',
    'impact': 'major',
    'shortlink': 'https://stspg.io/abc',
    'started_at': '2024-01-01T00:00:00.000Z',
    'page_id': 'page1',
    'incident_updates': [
      {
        'id': 'upd1',
        'status': 'resolved',
        'body': 'Fixed.',
        'incident_id': 'inc1',
        'created_at': '2024-01-01T01:00:00.000Z',
        'updated_at': '2024-01-01T01:00:00.000Z',
        'display_at': '2024-01-01T01:00:00.000Z',
        'affected_components': [],
        'deliver_notifications': True,
        'custom_tweet': None,
        'tweet_id': None,
      },
    ],
    'components': [
      {'id': 'comp1', 'name': 'Game', 'status': 'operational'},
    ],
  }
  inc = ZSIncident.from_dict(data)
  assert inc.id == 'inc1'
  assert inc.name == 'Game Down'
  assert inc.impact == 'major'
  assert len(inc.incident_updates) == 1
  assert inc.incident_updates[0].status == 'resolved'
  assert len(inc.components) == 1
  assert inc.components[0].name == 'Game'


def test_incident_from_dict_empty():
  inc = ZSIncident.from_dict({})
  assert inc.id == ''
  assert inc.incident_updates == []
  assert inc.components == []


def test_incident_extras():
  data = {'id': 'x', 'reminder_intervals': None}
  inc = ZSIncident.from_dict(data)
  assert 'reminder_intervals' in inc.extras()


def test_incident_asdict():
  inc = ZSIncident(id='x', name='Y')
  d = inc.asdict()
  assert d['id'] == 'x'
  assert '_extra' not in d


def test_incident_from_fixture(incidents_data):
  incs = incidents_data.get('incidents', [])
  assert len(incs) > 0
  inc = ZSIncident.from_dict(incs[0])
  assert inc.id != ''
  assert inc.name != ''


# ---- ZSMaintenanceUpdate ----

def test_maintenance_update_from_dict():
  data = {
    'id': 'mupd1',
    'status': 'completed',
    'body': 'Maintenance done.',
    'created_at': '2024-01-01T00:00:00.000Z',
    'updated_at': '2024-01-01T00:00:00.000Z',
    'display_at': '2024-01-01T00:00:00.000Z',
    'affected_components': [],
    'deliver_notifications': False,
    'custom_tweet': None,
    'tweet_id': None,
    'scheduled_maintenance_id': 'maint1',
  }
  upd = ZSMaintenanceUpdate.from_dict(data)
  assert upd.id == 'mupd1'
  assert upd.status == 'completed'
  assert upd.scheduled_maintenance_id == 'maint1'


def test_maintenance_update_from_dict_empty():
  upd = ZSMaintenanceUpdate.from_dict({})
  assert upd.id == ''
  assert upd.scheduled_maintenance_id == ''


def test_maintenance_update_extras():
  data = {'id': 'x', 'new_field': True}
  upd = ZSMaintenanceUpdate.from_dict(data)
  assert upd.extras() == {'new_field': True}


# ---- ZSMaintenance ----

def test_maintenance_from_dict():
  data = {
    'id': 'maint1',
    'name': 'Server Update',
    'status': 'completed',
    'created_at': '2024-01-01T00:00:00.000Z',
    'updated_at': '2024-01-02T00:00:00.000Z',
    'monitoring_at': None,
    'resolved_at': '2024-01-02T00:00:00.000Z',
    'impact': 'maintenance',
    'shortlink': 'https://stspg.io/def',
    'started_at': '2024-01-01T06:00:00.000Z',
    'page_id': 'page1',
    'scheduled_for': '2024-01-01T06:00:00.000Z',
    'scheduled_until': '2024-01-01T08:00:00.000Z',
    'incident_updates': [
      {
        'id': 'mupd1',
        'status': 'completed',
        'body': 'Done.',
        'created_at': '2024-01-02T00:00:00.000Z',
        'updated_at': '2024-01-02T00:00:00.000Z',
        'display_at': '2024-01-02T00:00:00.000Z',
        'affected_components': [],
        'deliver_notifications': False,
        'custom_tweet': None,
        'tweet_id': None,
        'scheduled_maintenance_id': 'maint1',
      },
    ],
    'components': [
      {'id': 'comp1', 'name': 'Game', 'status': 'operational'},
    ],
  }
  m = ZSMaintenance.from_dict(data)
  assert m.id == 'maint1'
  assert m.name == 'Server Update'
  assert m.scheduled_for == '2024-01-01T06:00:00.000Z'
  assert m.scheduled_until == '2024-01-01T08:00:00.000Z'
  assert len(m.incident_updates) == 1
  assert len(m.components) == 1


def test_maintenance_from_dict_empty():
  m = ZSMaintenance.from_dict({})
  assert m.id == ''
  assert m.scheduled_for == ''
  assert m.incident_updates == []


def test_maintenance_extras():
  data = {'id': 'x', 'reminder_intervals': None}
  m = ZSMaintenance.from_dict(data)
  assert 'reminder_intervals' in m.extras()


def test_maintenance_asdict():
  m = ZSMaintenance(id='x', name='Y')
  d = m.asdict()
  assert d['id'] == 'x'
  assert '_extra' not in d


# ---- ZSSummary ----

def test_summary_from_dict(summary_data):
  summary = ZSSummary.from_dict(summary_data)
  assert summary.page.name == 'Zwift, Inc'
  assert summary.status.indicator == 'none'
  assert len(summary.components) > 0


def test_summary_from_dict_empty():
  summary = ZSSummary.from_dict({})
  assert summary.page.id == ''
  assert summary.status.indicator == ''
  assert summary.components == []
  assert summary.incidents == []


def test_summary_extras():
  data = {
    'page': {'id': 'x'},
    'status': {'indicator': 'none'},
    'unknown_top_level': 'value',
  }
  summary = ZSSummary.from_dict(data)
  assert summary.extras() == {'unknown_top_level': 'value'}


def test_summary_asdict(summary_data):
  summary = ZSSummary.from_dict(summary_data)
  d = summary.asdict()
  assert 'page' in d
  assert 'status' in d
  assert 'components' in d
  assert '_extra' not in d


def test_summary_none_values():
  data = {
    'page': None,
    'status': None,
    'components': None,
    'incidents': None,
    'scheduled_maintenances': None,
  }
  summary = ZSSummary.from_dict(data)
  assert summary.page.id == ''
  assert summary.components == []
