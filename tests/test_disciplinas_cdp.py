from core.disciplinas import (
    BIMESTRES,
    TURMAS_CDP,
    eh_cdp,
    eh_cdp_fundamental,
    nomes_disciplinas,
    obter_config,
)


def test_cdp_nao_exige_pdf():
    config = obter_config("CDP- Multisseriada")

    assert eh_cdp("CDP- Multisseriada")
    assert config.exige_pdf is False


def test_cdp_fundamental_nao_exige_pdf():
    config = obter_config("CDP-ENSINO FUNDAMENTAL")

    assert eh_cdp("CDP-ENSINO FUNDAMENTAL")
    assert eh_cdp_fundamental("CDP-ENSINO FUNDAMENTAL")
    assert config.exige_pdf is False


def test_lista_disciplinas_tem_opcoes_principais():
    nomes = nomes_disciplinas()

    assert "Língua Portuguesa" in nomes
    assert "Ciências" in nomes
    assert "Projeto de Vida" in nomes
    assert "Educação Financeira" in nomes
    assert "Redação e Leitura" in nomes
    assert "Biologia" in nomes
    assert "CDP- Multisseriada" in nomes
    assert "CDP-ENSINO FUNDAMENTAL" in nomes
    assert "Outra" in nomes


def test_opcoes_cabecalho_e_cdp():
    assert BIMESTRES == ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"]
    assert TURMAS_CDP == [
        "MULTISSERIADO 1º, 2º e 3º ano",
        "MULTISSERIADO 4º e 5º ano",
    ]
