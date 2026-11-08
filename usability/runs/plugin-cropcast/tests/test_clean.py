from cropcast.clean import flag_outliers


def test_flags_extreme_value():
    assert flag_outliers([10, 11, 10, 9, 10, 11, 10, 9, 10, 100])[-1]


def test_short_series_not_flagged():
    assert flag_outliers([1, 2]) == [False, False]
