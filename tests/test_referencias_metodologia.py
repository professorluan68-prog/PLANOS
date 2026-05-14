from core.referencias_metodologia import (
    carregar_referencia_metodologica,
    listar_referencias_disponiveis,
)


def test_carrega_referencia_por_disciplina():
    referencia = carregar_referencia_metodologica("Língua Portuguesa", "7º ano A")

    assert "REGRAS FIXAS DO SISTEMA" in referencia
    assert "LÍNGUA PORTUGUESA" in referencia
    assert "Não invente técnicas" in referencia


def test_referencias_disponiveis_incluem_disciplinas_implantadas():
    referencias = listar_referencias_disponiveis()

    assert "historia" in referencias
    assert "arte" in referencias
    assert "projeto de vida" in referencias
    assert "ciencias" in referencias


def test_referencia_interdisciplinar_entra_como_complemento_seguro():
    referencia = carregar_referencia_metodologica("História", "8º ano A")

    assert "REFERÊNCIA INTERDISCIPLINAR COMPLEMENTAR" in referencia
    assert "não presentes nos slides" in referencia
    assert "Riscos de Confusão no Código Python" not in referencia
