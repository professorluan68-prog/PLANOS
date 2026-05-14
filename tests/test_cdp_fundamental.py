from core.cdp import carregar_habilidades_cdp_fundamental, selecionar_item


def test_carrega_habilidades_cdp_fundamental_dos_docx():
    dados = carregar_habilidades_cdp_fundamental()

    assert "português" in dados
    assert "matematica" in dados
    assert dados["português"]
    assert dados["matematica"]
    assert dados["português"][0]["HABILIDADES"].startswith("EFCDP-LP")


def test_selecionar_item_cdp_fundamental_respeita_aula_inicial():
    item = selecionar_item("matematica", 0, aula_inicial=3, fundamental=True)

    assert item["AULA"] == "3"
    assert "multiplicação" in item["OBJETO DE CONHECIMENTO"].lower()
