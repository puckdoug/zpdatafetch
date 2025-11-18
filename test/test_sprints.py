import httpx



def test_sprints(sprints):
  assert sprints is not None


def test_sprints_initialization(sprints):
  assert sprints.raw == {}


def test_sprints_fetch_race_sprints(sprints, login_page, logged_in_page):
  test_data = {
    'data': [
      {'sprint_id': 1, 'name': 'Sprint 1', 'distance': 500},
      {'sprint_id': 2, 'name': 'Sprint 2', 'distance': 750},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'event_sprints' in str(request.url):
      return httpx.Response(200, json=test_data)
    return httpx.Response(404)

  from zpdatafetch.zp import ZP

  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self.init_client(
      httpx.Client(follow_redirects=True, transport=httpx.MockTransport(handler)),
    )

  ZP.__init__ = mock_init

  try:
    race_sprints = sprints.fetch(3590800)
    assert 3590800 in race_sprints
    assert race_sprints[3590800] == test_data
  finally:
    ZP.__init__ = original_init
