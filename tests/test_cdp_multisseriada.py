from core.cdp import (
    carregar_planilha_cdp_multisseriada,
    listar_componentes_cdp_multisseriada,
    listar_habilidades_cdp_multisseriada,
    limpar_texto_cdp,
    montar_acessibilidade_cdp,
    montar_acompanhamento_cdp,
    montar_metodologia_cdp,
    selecionar_item,
    titulo_item_cdp,
)


def test_lista_componentes_cdp_multisseriada():
    componentes = listar_componentes_cdp_multisseriada()

    assert "Ciências" in componentes
    assert "História" in componentes
    assert "Matemática" in componentes


def test_lista_habilidades_cdp_multisseriada_por_componente_turma_e_bimestre():
    habilidades = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 1º, 2º e 3º ano",
        bimestre="2ºBIMESTRE",
    )

    assert habilidades
    assert "Habilidade" not in habilidades[0]["codigo"]
    assert "(EF0" in habilidades[0]["codigo"]


def test_selecionar_item_cdp_multisseriada_respeita_componente_turma_e_bimestre():
    item = selecionar_item(
        "História",
        0,
        turma="MULTISSERIADO 4º e 5º ano",
        bimestre="2ºBIMESTRE",
        multisseriada=True,
        componente_cdp="História",
    )

    assert item
    assert item.get("ANO", "").startswith(("4", "5"))
    assert item.get("BIMESTRE", "").startswith("2")


def test_multisseriada_usa_colunas_reais_para_titulo_e_metodologia():
    dados = carregar_planilha_cdp_multisseriada()
    item = dados["Língua Portuguesa"][0]

    assert titulo_item_cdp(item)
    assert "conteúdo proposto" not in montar_metodologia_cdp("português", item).lower()


def test_limpa_percentuais_da_planilha_multisseriada():
    assert limpar_texto_cdp("Quatro operações (90%) Números fracionários (60%)") == "Quatro operações Números fracionários"
    assert limpar_texto_cdp("Normativo (86,3% corrigem fala)") == "Normativo"


def test_metodologia_multisseriada_usa_estilo_eja_contextualizado():
    dados = carregar_planilha_cdp_multisseriada()
    item = dados["Matemática"][0]

    metodologia = montar_metodologia_cdp("matematica", item)
    acompanhamento = montar_acompanhamento_cdp("matematica", item)
    acessibilidade = montar_acessibilidade_cdp("matematica", item)

    assert "situação do cotidiano" in metodologia
    assert "conteúdo proposto" not in metodologia.lower()
    assert "cálculos" in acompanhamento[1]
    assert "explicação passo a passo" in acessibilidade[0].lower()

    texto_cdp = " ".join([metodologia, *acompanhamento, *acessibilidade]).lower()
    termos_bloqueados = ["lemov", "virem", "todo mundo", "tecnologia", "digital", "software", "aplicativo"]
    assert not any(termo in texto_cdp for termo in termos_bloqueados)


def test_multisseriada_separa_turmas_123_e_45():
    habilidades_123 = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 1º, 2º e 3º ano",
    )
    habilidades_45 = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 4º e 5º ano",
    )

    assert habilidades_123
    assert habilidades_45
    assert habilidades_123[0]["descricao"] != habilidades_45[0]["descricao"]
