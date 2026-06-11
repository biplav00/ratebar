from ratebar.gauge import sweep_degrees


def test_sweep_degrees():
    assert sweep_degrees(0) == 0.0
    assert sweep_degrees(50) == 180.0
    assert sweep_degrees(100) == 360.0
    assert sweep_degrees(150) == 360.0   # clamped
    assert sweep_degrees(-10) == 0.0
