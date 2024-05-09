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
