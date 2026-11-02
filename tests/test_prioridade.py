from discovery.collectors.prioridade import PRIORITY_KEYWORDS, pontuar


def test_portuguese_terms_are_kept():
    assert {"sobre", "serviço", "contato", "lgpd"} <= set(PRIORITY_KEYWORDS)


def test_english_terms_score_like_portuguese():
    assert pontuar("https://x.com.br/about") == pontuar("https://x.com.br/sobre")
    assert pontuar("https://x.com.br/services") == pontuar("https://x.com.br/servicos")
    assert pontuar("https://x.com/pt/contact", "Contact us") == pontuar("https://x.com/pt/contato")


def test_anchor_counts_towards_score():
    assert pontuar("https://x.com.br/p", "Quem somos") > pontuar("https://x.com.br/p", "l1")


def test_unrelated_page_scores_zero():
    assert pontuar("https://x.com.br/blog/post-1") == 0
