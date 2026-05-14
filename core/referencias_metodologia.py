import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple


BASE_DIR = Path(__file__).resolve().parents[1]
PASTA_REFERENCIAS = BASE_DIR / "REFERENCIAS_METODOLOGIA"

LIMITE_REFERENCIA_CHARS = 6200
LIMITE_INTERDISCIPLINAR_CHARS = 1800

REFERENCIA_INTERDISCIPLINAR = "ADAPTAÇÃO METODOLÓGICA INTERDISCIPLINAR.md"

REFERENCIA_PORTUGUES_GERAL = "ANÁLISE METODOLÓGICA COMPLETA - LÍNGUA PORTUGUESA.md"
REFERENCIA_PORTUGUES_FUNDAMENTAL = "ANÁLISE METODOLÓGICA - LÍNGUA PORTUGUESA ENSINO FUNDAMENTAL.md"
REFERENCIA_PORTUGUES_MEDIO = "ANÁLISE METODOLÓGICA - LÍNGUA PORTUGUESA ENSINO MÉDIO.md"

REFERENCIA_PV_FUNDAMENTAL = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA ENSINO FUNDAMENTAL.md"
REFERENCIA_PV_REFINADA_FUNDAMENTAL = "ANÁLISE METODOLÓGICA REFINADA - PROJETO DE VIDA ENSINO FUNDAMENTAL.md"
REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA - ENSINO FUNDAMENTAL ANOS FINAIS.md"
REFERENCIA_PV_7_ANO = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA 7º ANO.md"

MAPA_REFERENCIAS = {
    "lingua portuguesa": REFERENCIA_PORTUGUES_GERAL,
    "portugues": REFERENCIA_PORTUGUES_GERAL,
    "ciencias": "ANÁLISE METODOLÓGICA - CIÊNCIAS 7º ANO.md",
    "ciencia": "ANÁLISE METODOLÓGICA - CIÊNCIAS 7º ANO.md",
    "arte": "ANÁLISE METODOLÓGICA - ARTE - ENSINO FUNDAMENTAL ANOS FINAIS.md",
    "artes": "ANÁLISE METODOLÓGICA - ARTE - ENSINO FUNDAMENTAL ANOS FINAIS.md",
    "historia": "ANÁLISE METODOLÓGICA - HISTÓRIA ENSINO FUNDAMENTAL.md",
    "projeto de vida": (
        REFERENCIA_PV_REFINADA_FUNDAMENTAL,
        REFERENCIA_PV_FUNDAMENTAL,
        REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS,
    ),
    "ingles": "ANÁLISE METODOLÓGICA - INGLÊS ENSINO FUNDAMENTAL.md",
    "english": "ANÁLISE METODOLÓGICA - INGLÊS ENSINO FUNDAMENTAL.md",
    "orientacao de estudos": "ANÁLISE METODOLÓGICA PROFUNDA - ORIENTAÇÃO DE ESTUDOS.md",
    "educacao financeira": "EDUCAÇÃO FINANCEIRA-7ANO_METODOLOGIA.docx",
    "cdp": (
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).md",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).mdparte2.md",
    ),
    "eja": (
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).md",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).mdparte2.md",
    ),
}


def normalizar_disciplina(texto: str = "") -> str:
    texto = (texto or "").strip().lower()
    mapa = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "â": "a",
            "ã": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
            "º": "",
            "ª": "",
            "°": "",
        }
    )
    texto = texto.translate(mapa)
    return re.sub(r"\s+", " ", texto)


def _eh_turma_fundamental(turma: str = "") -> bool:
    turma_norm = normalizar_disciplina(turma)
    return bool(re.search(r"\b(?:6|7|8|9)\s*(?:ano|a|b|c|d|e)?\b", turma_norm))


def _ano_turma(turma: str = "") -> int:
    turma_norm = normalizar_disciplina(turma)
    match = re.search(r"\b([1-9])\s*(?:ano|em|a|b|c|d|e)?\b", turma_norm)
    return int(match.group(1)) if match else 0


def _eh_portugues(disciplina: str = "") -> bool:
    disciplina_norm = normalizar_disciplina(disciplina)
    return "portugues" in disciplina_norm or "lingua portuguesa" in disciplina_norm


def _eh_projeto_vida(disciplina: str = "") -> bool:
    return "projeto de vida" in normalizar_disciplina(disciplina)


def _arquivos_para_disciplina(disciplina: str = "") -> Tuple[str, ...]:
    disciplina_norm = normalizar_disciplina(disciplina)
    for chave, arquivos in MAPA_REFERENCIAS.items():
        if chave in disciplina_norm:
            if isinstance(arquivos, str):
                return (arquivos,)
            return tuple(arquivos)
    return ()


def _limpar_markdown(texto: str) -> str:
    texto = re.sub(r"```.*?```", " ", texto or "", flags=re.DOTALL)
    texto = re.sub(r"#{1,6}\s*", "", texto)
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _limpar_interdisciplinar(texto: str) -> str:
    texto = _limpar_markdown(texto)
    texto = re.sub(
        r"(?is)1\.\s*Aplicabilidade dos Padrões por Disciplina.*?(?=2\.\s*Adaptações Específicas por Disciplina)",
        "",
        texto,
    )
    texto = re.sub(r"(?is)3\.\s*Riscos de Confusão no Código Python.*", "", texto)
    texto = re.sub(r"(?im)^#+\s*", "", texto)
    return texto.strip()


def _reforcar_regras_do_sistema(texto: str) -> str:
    reforco = (
        "REGRAS FIXAS DO SISTEMA:\n"
        "- Use esta biblioteca apenas como referência de estilo e qualidade, sem copiar trechos prontos.\n"
        "- Priorize textos completos; não use reticências para encurtar frases em desenvolvimento, acompanhamento ou acessibilidade.\n"
        "- Se precisar reduzir, reescreva a frase de forma mais curta e completa.\n"
        "- Não invente técnicas pedagógicas; só cite técnicas quando estiverem explicitamente presentes nos slides.\n"
        "- Exceção: Pause e responda sempre é verificação da aprendizagem com correção mediada.\n"
        "- Respeite a ordem real dos slides enviados.\n"
        "- Mantenha metodologia fluida, objetiva e adequada ao conteúdo da aula.\n\n"
    )
    return reforco + texto


def _carregar_referencia_interdisciplinar() -> str:
    caminho = PASTA_REFERENCIAS / REFERENCIA_INTERDISCIPLINAR
    if not caminho.exists():
        return ""

    texto = _limpar_interdisciplinar(caminho.read_text(encoding="utf-8", errors="ignore"))
    if not texto:
        return ""

    texto = (
        "REFERÊNCIA INTERDISCIPLINAR COMPLEMENTAR:\n"
        "- Use apenas para variar verbos, progressão pedagógica e linguagem de mediação.\n"
        "- Não use esta referência para criar tempos fixos, etapas inexistentes ou técnicas não presentes nos slides.\n"
        "- A referência específica da disciplina e a ordem real dos slides têm prioridade.\n\n"
        + texto
    )
    if len(texto) <= LIMITE_INTERDISCIPLINAR_CHARS:
        return texto
    return texto[:LIMITE_INTERDISCIPLINAR_CHARS].rsplit("\n", 1)[0].strip()


def _ler_arquivos_referencia(arquivos: Iterable[str]) -> str:
    partes = []
    for arquivo in arquivos:
        caminho = PASTA_REFERENCIAS / arquivo
        if not caminho.exists():
            continue
        if caminho.suffix.lower() == ".md":
            texto = caminho.read_text(encoding="utf-8", errors="ignore")
            texto = _limpar_markdown(texto)
        else:
            texto = caminho.name
        if texto:
            partes.append(texto)
    return "\n\n".join(partes)


@lru_cache(maxsize=32)
def carregar_referencia_metodologica(disciplina: str = "", turma: str = "") -> str:
    if _eh_portugues(disciplina) and _eh_turma_fundamental(turma):
        arquivos = (REFERENCIA_PORTUGUES_FUNDAMENTAL, REFERENCIA_PORTUGUES_GERAL)
    elif _eh_portugues(disciplina):
        arquivos = (REFERENCIA_PORTUGUES_MEDIO, REFERENCIA_PORTUGUES_GERAL)
    elif _eh_projeto_vida(disciplina) and _ano_turma(turma) == 7:
        arquivos = (
            REFERENCIA_PV_REFINADA_FUNDAMENTAL,
            REFERENCIA_PV_7_ANO,
            REFERENCIA_PV_FUNDAMENTAL,
            REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS,
        )
    else:
        arquivos = _arquivos_para_disciplina(disciplina)
    if not arquivos:
        return ""

    texto = _ler_arquivos_referencia(arquivos)
    if not texto:
        return ""

    interdisciplinar = _carregar_referencia_interdisciplinar()
    if interdisciplinar:
        limite_texto_principal = max(2600, LIMITE_REFERENCIA_CHARS - len(interdisciplinar) - 400)
        if len(texto) > limite_texto_principal:
            texto = texto[:limite_texto_principal].rsplit("\n", 1)[0].strip()
        texto = texto + "\n\n" + interdisciplinar

    texto = _reforcar_regras_do_sistema(texto)
    if len(texto) <= LIMITE_REFERENCIA_CHARS:
        return texto
    return texto[:LIMITE_REFERENCIA_CHARS].rsplit("\n", 1)[0].strip()


def listar_referencias_disponiveis() -> Dict[str, str]:
    disponiveis = {}
    for disciplina, arquivos in MAPA_REFERENCIAS.items():
        lista = (arquivos,) if isinstance(arquivos, str) else tuple(arquivos)
        caminhos = [str(PASTA_REFERENCIAS / arquivo) for arquivo in lista if (PASTA_REFERENCIAS / arquivo).exists()]
        if caminhos:
            disponiveis[disciplina] = " | ".join(caminhos)
    return disponiveis
