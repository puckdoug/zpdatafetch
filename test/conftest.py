import pytest

from zpdatafetch import *


@pytest.fixture
def zp():
  return ZP()


@pytest.fixture
def cyclist():
  return Cyclist()


@pytest.fixture
def primes():
  return Primes()


@pytest.fixture
def result():
  return Result()


@pytest.fixture
def config():
  return Config()


@pytest.fixture
def signup():
  return Signup()


@pytest.fixture
def team():
  return Team()


@pytest.fixture
def login_page():
  return open('test/fixtures/login_page.html').read()


@pytest.fixture
def logged_in_page():
  return open('test/fixtures/logged_in_page.html').read()
