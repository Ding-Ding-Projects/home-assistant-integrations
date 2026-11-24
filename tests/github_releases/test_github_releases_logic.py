import pytest

from conftest import load_logic

L = load_logic("github_releases")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("home-assistant/core", "home-assistant/core"),
        (
            "  Ding-Ding-Projects/home-assistant-integrations ",
            "Ding-Ding-Projects/home-assistant-integrations",
        ),
        ("https://github.com/owner/repo", "owner/repo"),
        ("https://github.com/owner/repo.git", "owner/repo"),
        ("github.com/owner/repo/", "owner/repo"),
    ],
)
def test_parse_repo_valid(text, expected):
    assert L.parse_repo(text) == expected


@pytest.mark.parametrize("text", ["", "owner", "owner/", "/repo", "a b/c", "-bad/repo", "o/r/extra"])
def test_parse_repo_invalid(text):
    with pytest.raises(ValueError):
        L.parse_repo(text)


def test_parse_release():
    tag, when = L.parse_release({"tag_name": "v1.2.3", "published_at": "2026-01-02T03:04:05Z"})
    assert tag == "v1.2.3"
    assert (when.year, when.month, when.hour) == (2026, 1, 3)
    assert when.utcoffset().total_seconds() == 0


def test_parse_release_without_date_or_tag():
    assert L.parse_release({"tag_name": "x"}) == ("x", None)
    with pytest.raises(ValueError):
        L.parse_release({})


def test_backoff_doubles_and_caps():
    assert [L.backoff_hours(n) for n in range(0, 5)] == [6, 12, 24, 24, 24]


def test_rate_limit_detection():
    assert L.is_rate_limited(429, None)
    assert L.is_rate_limited(403, "0")
    assert L.is_rate_limited(403, None)
    assert not L.is_rate_limited(403, "12")
    assert not L.is_rate_limited(200, "0")
