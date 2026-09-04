from ai_act_validator.official_ui import bilingual_html, link_article_references


def test_links_ai_act_article_in_english_and_spanish():
    english = link_article_references("See Article 6 (3) AI Act")
    spanish = link_article_references("Véase el artículo 50 del Reglamento de IA")

    assert "/en/ai-act/article-6" in english
    assert ">6</a> (3)" in english
    assert "/en/ai-act/article-50" in spanish


def test_links_every_article_in_a_plural_reference():
    linked = link_article_references("Articles 16, 17 and 18 apply")

    assert linked.count("<a href=") == 3
    assert "/article-16" in linked
    assert "/article-17" in linked
    assert "/article-18" in linked


def test_links_directive_articles_to_eur_lex_instead_of_ai_act():
    linked = link_article_references("Article 3-(4) of Directive (EU) 2016/680 applies")

    assert "eur-lex.europa.eu/eli/dir/2016/680" in linked
    assert "/en/ai-act/article-3" not in linked


def test_bilingual_html_places_translation_in_parentheses():
    rendered = bilingual_html("Official question", "Pregunta traducida", "question-text")

    assert 'class="translation">(Pregunta traducida)</div>' in rendered
    assert 'class="question-text">Official question</div>' in rendered
