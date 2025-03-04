import httpx
import pytest

from zpdatafetch.zp import ZP


def test_fetch_login_page(
  zp,
  login_page,
  logged_in_page,
):
  def handler(request):
    match request.method:
      case 'GET':
        return httpx.Response(200, text=login_page)
      case 'POST':
        return httpx.Response(200, text=logged_in_page)

  zp.init_client(
    httpx.Client(follow_redirects=True, transport=httpx.MockTransport(handler)),
  )
  zp.login()
  assert zp.login.status_code == 200


def test_pen(zp):
  assert zp.set_pen(0) == 'E'
  assert zp.set_pen(1) == 'A'
  assert zp.set_pen(2) == 'B'
  assert zp.set_pen(3) == 'C'
  assert zp.set_pen(4) == 'D'
  assert zp.set_pen(5) == 'E'
  assert zp.set_pen(6) == '6'


def test_rider_category(zp):
  assert zp.set_rider_category(0) == ''
  assert zp.set_rider_category(10) == 'A'
  assert zp.set_rider_category(20) == 'B'
  assert zp.set_rider_category(30) == 'C'
  assert zp.set_rider_category(40) == 'D'
  assert zp.set_rider_category(50) == '50'


def test_category(zp):
  assert zp.set_category(0) == 'E'
  assert zp.set_category(10) == 'A'
  assert zp.set_category(20) == 'B'
  assert zp.set_category(30) == 'C'
  assert zp.set_category(40) == 'D'
  assert zp.set_category(50) == '50'
