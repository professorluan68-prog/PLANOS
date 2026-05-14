from core.lote import _detectar_tipo_aula, _montar_etapas_metodologia
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada


def test_educacao_financeira_classifica_tipos_especificos():
    assert (
        _detectar_tipo_aula(
            "Organize receita, despesa, renda e gastos em um orcamento mensal.",
            "Orcamento pessoal",
            "Educacao Financeira",
        )
        == "orcamento_planejamento"
    )
    assert (
        _detectar_tipo_aula(
            "Compare compra parcelada, credito, juros, parcelas e custo total.",
            "Credito e juros",
            "Educacao Financeira",
        )
        == "credito_endividamento"
    )
    assert (
        _detectar_tipo_aula(
            "Analise poupanca, reserva de emergencia, rendimento e metas.",
            "Por que poupamos?",
            "Educacao Financeira",
        )
        == "investimento_poupanca"
    )


def test_educacao_financeira_metodologia_usa_regras_da_analise():
    etapas = _montar_etapas_metodologia(
        texto=(
            "Compra parcelada com juros. Compare valor a vista, parcelas, credito e custo total. "
            "Na pratica, resolva as situacoes-problema e justifique a decisao."
        ),
        disciplina="Educacao Financeira",
        turma="7 ano A",
        tema="Juros e credito",
    )

    titulos = [etapa["titulo"] for etapa in etapas]
    texto = " ".join(etapa["texto"] for etapa in etapas)

    assert "Analise de caso" in titulos
    assert "Calculos financeiros" in titulos
    assert "sem exigir relatos pessoais" in texto
    assert "valor a vista" in texto or "custo total" in texto
    assert "REGISTREM" not in texto


def test_educacao_financeira_acompanhamento_e_acessibilidade_por_tipo():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Credito e juros",
        disciplina="Educacao Financeira",
        tipo="credito_endividamento",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Credito e juros",
        disciplina="Educacao Financeira",
        tipo="credito_endividamento",
    )

    assert any("custo total" in item for item in acompanhamento)
    assert any("valor \u00e0 vista" in item for item in acessibilidade)
