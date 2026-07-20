from app.core.hybrid_asr.glossary import Glossary, GlossaryRule


def test_glossary_only_applies_explicit_safe_rules():
    glossary = Glossary([
        GlossaryRule("設立佛", "舍利弗", match_mode="exact"),
        GlossaryRule("美安", "Market America", match_mode="contains"),
    ])

    assert glossary.apply_deterministic("設立佛") == "舍利弗"
    assert glossary.apply_deterministic("我使用美安產品") == "我使用美安產品"
    assert "舍利弗" in glossary.prompt()
    assert len(glossary.version_hash) == 12
