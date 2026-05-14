from dataclasses import dataclass


BIMESTRES = ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"]
MODO_PDF = "pdf"
MODO_CDP = "cdp"
MODO_CDP_FUNDAMENTAL = "cdp_fundamental"


@dataclass(frozen=True)
class DisciplinaConfig:
    nome: str
    modo: str = MODO_PDF
    exige_pdf: bool = True
    aprendizagem_padrao: str = (
        "Desenvolver habilidades relacionadas ao tema da aula, participando das "
        "atividades propostas e registrando as principais aprendizagens."
    )


_DISCIPLINAS = [
    "Arte",
    "Biologia",
    "Ciências",
    "Educação Financeira",
    "Educação Física",
    "Filosofia",
    "Física",
    "Geografia",
    "História",
    "Língua Inglesa",
    "Língua Portuguesa",
    "Matemática",
    "CDP- Multisseriada",
    "CDP-ENSINO FUNDAMENTAL",
    "Projeto de Vida",
    "Química",
    "Redação e Leitura",
    "Sociologia",
    "Outra",
]

TURMAS_CDP = [
    "MULTISSERIADO 1º, 2º e 3º ano",
    "MULTISSERIADO 4º e 5º ano",
]
TURMAS_CDP_MULTISSERIADA = TURMAS_CDP


def nomes_disciplinas() -> list[str]:
    return list(_DISCIPLINAS)


def obter_config(disciplina: str) -> DisciplinaConfig:
    nome = (disciplina or "Outra").strip() or "Outra"
    if nome == "CDP- Multisseriada":
        return DisciplinaConfig(nome=nome, modo=MODO_CDP, exige_pdf=False)
    if nome == "CDP-ENSINO FUNDAMENTAL":
        return DisciplinaConfig(nome=nome, modo=MODO_CDP_FUNDAMENTAL, exige_pdf=False)
    return DisciplinaConfig(nome=nome)


def eh_cdp(nome: str) -> bool:
    return obter_config(nome).modo in {MODO_CDP, MODO_CDP_FUNDAMENTAL}


def eh_cdp_multisseriada(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP


def eh_cdp_fundamental(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP_FUNDAMENTAL
