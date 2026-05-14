from core.lote import _montar_etapas_metodologia


def test_projeto_vida_nao_usa_marcador_como_conceito():
    etapas = _montar_etapas_metodologia(
        texto=(
            "Relembre\n"
            "Nossas frases modelo Na última aula, a turma criou frases para conversar sobre respeito.\n"
            "Foco no conteúdo\n"
            "Pontos de vista Quando convivemos, lidamos com opiniões diferentes.\n"
        ),
        disciplina="Projeto de Vida",
        turma="6º ano A",
        tema="Preparando nosso círculo de convivência",
    )

    foco = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Foco no conteudo")
    assert "Relembre" not in foco
    assert "Preparando nosso círculo de convivência" not in foco
    assert "relacionar sentir, pensar e agir" in foco


def test_projeto_vida_mantem_tom_acolhedor():
    etapas = _montar_etapas_metodologia(
        texto="Na prática\nRegistro individual e conversa em dupla sobre autoconhecimento.",
        disciplina="Projeto de Vida",
        turma="6º ano B",
        tema="Quem sou quando estou comigo?",
    )

    para_comecar = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Para comecar")
    pratica = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Na pratica")
    assert "sem exigir exposicao pessoal" in para_comecar
    assert "socializacao seja opcional ou mediada" in pratica
