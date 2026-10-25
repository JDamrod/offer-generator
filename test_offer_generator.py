from offer_generator import geo_flag, _conditions, build_offer_text


# Tests for geo_flag()

def test_geo_flag_poland():
    assert geo_flag("PL") == "🇵🇱"


def test_geo_flag_uk():
    assert geo_flag("UK") == "🇬🇧"
    assert geo_flag("GB") == "🇬🇧"


def test_geo_flag_lowercase():
    assert geo_flag("pl") == "🇵🇱"
    assert geo_flag("gb") == "🇬🇧"


def test_geo_flag_unknown():
    assert geo_flag("123") == "🌍"
    assert geo_flag("poland") == "🌍"
    assert geo_flag("") == "🌍"


# Tests for _conditions()

def test_conditions_only_mindep():
    assert _conditions("20 EUR", "", "") == "mindep 20 EUR"


def test_conditions_mindep_and_baseline():
    assert _conditions(
        "20 EUR",
        "20 EUR",
        ""
    ) == "mindep = <b>baseline 20 EUR</b>"


def test_conditions_mindep_and_wager():
    assert _conditions(
        "20 EUR",
        "",
        "20 EUR"
    ) == "mindep = <b>wager 20 EUR</b>"


def test_conditions_all_equal():
    assert _conditions(
        "20 EUR",
        "20 EUR",
        "20 EUR"
    ) == "mindep = <b>baseline = wager 20 EUR</b>"


def test_conditions_all_different():
    assert _conditions(
        "10 EUR",
        "20 EUR",
        "30 EUR"
    ) == "mindep 10 EUR + <b>baseline 20 EUR + wager 30 EUR</b>"


# Tests for build_offer_text()

def test_build_offer_contains_basic_data():
    result = build_offer_text(
        "Stake",
        "PL",
        "100",
        "20",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Slot",
        ""
    )

    assert "Stake" in result
    assert "PL" in result
    assert "CPA 100" in result


def test_build_offer_multiple_names():
    result = build_offer_text(
        "Stake,Roobet",
        "GB",
        "200",
        "50",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Casino",
        ""
    )

    assert "Stake" in result
    assert "Roobet" in result
    assert result.count("CPA 200") == 2


def test_build_offer_with_comment_and_kpi():
    result = build_offer_text(
        "Casino",
        "DE",
        "150",
        "30",
        "",
        "",
        "",
        "High quality traffic",
        "",
        "",
        "Web",
        "Slot",
        "Exclusive offer"
    )

    assert "Exclusive offer" in result
    assert "KPI: High quality traffic" in result
    assert "Web platform" in result