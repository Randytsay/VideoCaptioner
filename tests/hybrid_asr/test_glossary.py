from pathlib import Path

from app.core.hybrid_asr.glossary import Glossary, GlossaryEntry


def test_apply_and_review_modes() -> None:
    glossary = Glossary(
        [
            GlossaryEntry("見信成佛", "見性成佛"),
            GlossaryEntry("可疑詞", "", match_mode="review_only"),
        ]
    )
    result = glossary.apply("見信成佛與可疑詞")
    assert result.text == "見性成佛與可疑詞"
    assert result.review_hits == ("可疑詞",)


def test_version_hash_is_order_independent() -> None:
    first = Glossary([GlossaryEntry("甲", "乙"), GlossaryEntry("丙", "丁")])
    second = Glossary([GlossaryEntry("丙", "丁"), GlossaryEntry("甲", "乙")])
    assert first.version_hash == second.version_hash


def test_load_csv_with_utf8_content(tmp_path: Path) -> None:
    path = tmp_path / "詞庫.csv"
    path.write_text(
        "wrong_term,correct_term,note,match_mode,enabled\n錯,對,,exact,true\n",
        encoding="utf-8",
    )
    assert Glossary.from_csv(path).apply("錯").text == "對"
