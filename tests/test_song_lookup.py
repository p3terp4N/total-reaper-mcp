# tests/test_song_lookup.py
"""Tests for song lookup / chord parsing (no network required)."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestChordParser:
    """Test chord chart text parsing."""

    def test_parse_simple_chart(self):
        from server.song_lookup import parse_chord_chart
        raw = """[Verse]
Am . G .
F . E .

[Chorus]
C G Am F
"""
        chart = parse_chord_chart(raw, title="Test Song", artist="Test Artist", bpm=120, key="Am")
        assert chart["title"] == "Test Song"
        assert chart["key"] == "Am"
        assert chart["bpm"] == 120
        assert len(chart["sections"]) == 2
        assert chart["sections"][0]["name"] == "verse"
        assert chart["sections"][0]["chords"] == ["Am", "Am", "G", "G", "F", "F", "E", "E"]
        assert chart["sections"][1]["name"] == "chorus"
        assert chart["sections"][1]["chords"] == ["C", "G", "Am", "F"]

    def test_parse_repeats_with_dots(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nAm . . .\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["Am", "Am", "Am", "Am"]

    def test_parse_section_names_normalized(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Intro]\nAm\n[VERSE 1]\nG\n[Pre-Chorus]\nC\n[Chorus]\nF\n[Bridge]\nDm\n[Outro]\nAm\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        names = [s["name"] for s in chart["sections"]]
        assert names == ["intro", "verse", "pre-chorus", "chorus", "bridge", "outro"]

    def test_parse_extended_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nCmaj7 Dm7b5 G13 Asus4\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["Cmaj7", "Dm7b5", "G13", "Asus4"]

    def test_parse_slash_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nC/E G/B Am\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["C/E", "G/B", "Am"]

    def test_parse_empty_chart_returns_empty_sections(self):
        from server.song_lookup import parse_chord_chart
        chart = parse_chord_chart("", title="T", artist="A")
        assert chart["sections"] == []

    def test_bars_calculated_from_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nAm G F E Am G F E\n"
        chart = parse_chord_chart(raw, title="T", artist="A", time_sig="4/4")
        # 8 chords at 1 chord per bar = 8 bars
        assert chart["sections"][0]["bars"] == 8


class TestChordSimplifier:
    """Test chord simplification for unknown types."""

    def test_simplify_known_chord(self):
        from server.song_lookup import simplify_chord
        assert simplify_chord("Am") == "Am"
        assert simplify_chord("C") == "C"

    def test_simplify_extended_chord(self):
        from server.song_lookup import simplify_chord
        assert simplify_chord("Cmaj7") == "Cmaj7"
        assert simplify_chord("Dm7") == "Dm7"

    def test_simplify_complex_to_triad(self):
        from server.song_lookup import simplify_chord
        # Unknown extensions fall back to root triad
        assert simplify_chord("Gadd9#11b13") == "G"

    def test_simplify_slash_extracts_bass(self):
        from server.song_lookup import simplify_chord, extract_bass_note
        assert extract_bass_note("C/E") == "E"
        assert extract_bass_note("Am") is None


class TestKeyDetection:
    """Test key detection from chord set."""

    def test_detect_key_from_chords(self):
        from server.song_lookup import detect_key
        assert detect_key(["Am", "G", "F", "E"]) == "Am"
        assert detect_key(["C", "G", "Am", "F"]) == "C"

    def test_detect_key_empty(self):
        from server.song_lookup import detect_key
        assert detect_key([]) == "C"  # default


class TestTempoEstimation:
    """Test genre-based tempo estimation."""

    def test_estimate_tempo_by_genre(self):
        from server.song_lookup import estimate_tempo
        assert estimate_tempo("rock") == 120
        assert estimate_tempo("ballad") == 72
        assert estimate_tempo("funk") == 100

    def test_estimate_tempo_unknown_genre(self):
        from server.song_lookup import estimate_tempo
        assert estimate_tempo("unknown") == 120  # default


class TestUGScraper:
    """Test Ultimate Guitar scraping with mocked network calls."""

    def _make_search_html(self, results: list) -> str:
        """Build a fake UG search page with a js-store div."""
        store_data = {"store": {"page": {"data": {"results": results}}}}
        escaped = json.dumps(store_data).replace('"', '&quot;')
        return f'<html><body><div class="js-store" data-content="{escaped}"></div></body></html>'

    def _make_chord_page_html(self, chord_text: str, meta: dict | None = None) -> str:
        """Build a fake UG chord page with wiki_tab content."""
        if meta is None:
            meta = {}
        store_data = {
            "store": {
                "page": {
                    "data": {
                        "tab_view": {
                            "wiki_tab": {"content": chord_text},
                            "meta": meta,
                        }
                    }
                }
            }
        }
        escaped = json.dumps(store_data).replace('"', '&quot;')
        return f'<html><body><div class="js-store" data-content="{escaped}"></div></body></html>'

    @patch("server.song_lookup.requests")
    def test_search_returns_url(self, mock_requests):
        from server.song_lookup import search_ultimate_guitar

        results = [
            {"url": "https://tabs.ultimate-guitar.com/tab/artist/song-chords-12345",
             "type": "Chords", "rating": 4.5, "votes": 100},
            {"url": "https://tabs.ultimate-guitar.com/tab/artist/song-tab-99999",
             "type": "Tab", "rating": 4.8, "votes": 200},
            {"url": "https://tabs.ultimate-guitar.com/tab/artist/song-chords-67890",
             "type": "Chords", "rating": 3.0, "votes": 50},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._make_search_html(results)
        mock_requests.get.return_value = mock_resp

        url = search_ultimate_guitar("Song", "Artist")
        assert url == "https://tabs.ultimate-guitar.com/tab/artist/song-chords-12345"

    @patch("server.song_lookup.requests")
    def test_search_no_results(self, mock_requests):
        from server.song_lookup import search_ultimate_guitar

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._make_search_html([])
        mock_requests.get.return_value = mock_resp

        url = search_ultimate_guitar("Nonexistent", "Nobody")
        assert url is None

    @patch("server.song_lookup.requests")
    def test_scrape_chord_page(self, mock_requests):
        from server.song_lookup import scrape_ug_chord_page

        chord_content = "[Verse]\\nAm  G  F  E\\n[Chorus]\\nC  G  Am  F"
        meta = {"tonality": "Am", "bpm": 120}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._make_chord_page_html(chord_content, meta)
        mock_requests.get.return_value = mock_resp

        text, meta_out = scrape_ug_chord_page("https://tabs.ultimate-guitar.com/tab/test")
        assert "[Verse]" in text
        assert "Am" in text
        assert meta_out["tonality"] == "Am"
        assert meta_out["bpm"] == 120

    @patch("server.song_lookup.requests")
    def test_full_lookup_pipeline(self, mock_requests):
        from server.song_lookup import lookup_song

        # First call: search page
        search_results = [
            {"url": "https://tabs.ultimate-guitar.com/tab/artist/song-chords-12345",
             "type": "Chords", "rating": 4.5, "votes": 100},
        ]
        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.text = self._make_search_html(search_results)

        # Second call: chord page
        chord_content = "[Verse]\\nAm  G  F  E\\n[Chorus]\\nC  G  Am  F"
        meta = {"tonality": "Am", "bpm": 95}
        chord_resp = MagicMock()
        chord_resp.status_code = 200
        chord_resp.text = self._make_chord_page_html(chord_content, meta)

        mock_requests.get.side_effect = [search_resp, chord_resp]

        chart = lookup_song("Song", "Artist", bpm=0, genre="rock")
        assert chart is not None
        assert chart["title"] == "Song"
        assert chart["artist"] == "Artist"
        assert len(chart["sections"]) == 2
        assert chart["sections"][0]["name"] == "verse"
        assert chart["sections"][1]["name"] == "chorus"
        # bpm should come from meta (95), not genre default
        assert chart["bpm"] == 95
