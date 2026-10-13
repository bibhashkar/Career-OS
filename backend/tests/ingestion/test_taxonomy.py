"""
Tests for LocationNormalizer and VisaSponsorshipParser taxonomy engines.
"""

from app.ingestion.taxonomy import LocationNormalizer, VisaSponsorshipParser


def test_location_normalizer_city_state_us():
    norm = LocationNormalizer()
    res = norm.normalize("New York, NY")
    assert res.city == "New York"
    assert res.state_province_code == "NY"
    assert res.country_code == "US"
    assert res.primary_region == "north_america"
    assert res.workplace_type == "on_site"


def test_location_normalizer_remote_modality_and_scope():
    norm = LocationNormalizer()
    res = norm.normalize("Remote - Worldwide")
    assert res.workplace_type == "remote"
    assert res.remote_scope == "worldwide_global"


def test_location_normalizer_hybrid_uk():
    norm = LocationNormalizer()
    res = norm.normalize("Hybrid - London, UK")
    assert res.city == "London"
    assert res.country_code == "GB"
    assert res.primary_region == "europe"
    assert res.workplace_type == "hybrid"


def test_location_normalizer_canada():
    norm = LocationNormalizer()
    res = norm.normalize("Toronto, Ontario, Canada")
    assert res.city == "Toronto"
    assert res.state_province_code == "ON"
    assert res.country_code == "CA"
    assert res.primary_region == "canada"


def test_location_normalizer_australia():
    norm = LocationNormalizer()
    res = norm.normalize("Sydney, NSW, Australia")
    assert res.city == "Sydney"
    assert res.state_province_code == "NSW"
    assert res.country_code == "AU"
    assert res.primary_region == "oceania"


def test_visa_sponsorship_parser_affirmative():
    parser = VisaSponsorshipParser()
    desc = "We provide full visa sponsorship and relocation support for qualified H-1B holders."
    policy = parser.parse(desc)
    assert policy.status == "yes"
    assert "us_h1b" in policy.visa_types


def test_visa_sponsorship_parser_negative():
    parser = VisaSponsorshipParser()
    desc = "Must be legally authorized to work in the US without requiring visa sponsorship now or in the future."
    policy = parser.parse(desc)
    assert policy.status == "no"
    assert policy.notes is not None


def test_visa_sponsorship_parser_opt_cpt():
    parser = VisaSponsorshipParser()
    desc = "We welcome candidates on F-1 OPT / STEM OPT extensions."
    policy = parser.parse(desc)
    assert policy.status == "opt_cpt_accepted"
    assert "us_opt_cpt" in policy.visa_types


def test_visa_sponsorship_parser_unspecified_returns_null():
    parser = VisaSponsorshipParser()
    desc = "We are seeking a talented Python developer with 5 years experience."
    policy = parser.parse(desc)
    assert policy.status is None
    assert policy.visa_types == []
