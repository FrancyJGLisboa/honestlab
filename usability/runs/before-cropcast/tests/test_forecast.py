from cropcast.forecast import predict_yield


def test_returns_float():
    hist = [{"year": y, "yield": 150.0, "rain_mm": 500, "gdd": 2800} for y in range(2010, 2015)]
    assert isinstance(predict_yield(hist, {"year": 2015, "rain_mm": 500, "gdd": 2800}), float)
