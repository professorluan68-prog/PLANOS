# core/cdp.py
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile

from docx import Document

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

BASE_DIR = Path(__file__).resolve().parents[1]


# ← ADICIONADO: Função para verificar e buscar planilhas
def _verificar_planilha(caminho_padrao: Path, nome_arquivo: str) -> Path:
    """Verifica se planilha existe, senão busca alternativas."""
    import logging
    logger = logging.getLogger(__name__)

    if caminho_padrao.exists():
        logger.info(f"Planilha encontrada: {caminho_padrao}")
        return caminho_padrao

    # Tentar alternativas
    alternativas = [
        BASE_DIR / "planilhas" / nome_arquivo,
        BASE_DIR / "dados" / nome_arquivo,
        BASE_DIR / nome_arquivo,
        Path.home() / "Downloads" / nome_arquivo,
    ]

    for alt in alternativas:
        if alt.exists():
            logger.warning(f"Planilha encontrada em caminho alternativo: {alt}")
            return alt

    logger.error(f"Planilha não encontrada: {caminho_padrao}")
    logger.error(f"Alternativas tentadas: {[str(a) for a in alternativas]}")
    # Retornar o padrão mesmo se não existir (erro será tratado no uso)
    return caminho_padrao


PLANILHA_CDP = _verificar_planilha(
    BASE_DIR / "Planos feitos" / "PLANILHACDP.xlsx",
    "PLANILHACDP.xlsx"
)
PLANILHA_CDP_MULTISSERIADA = _verificar_planilha(
    BASE_DIR / "Planos feitos" / "Planilhas organizadas" / "cdp-habilidades.xlsx",
    "cdp-habilidades.xlsx"
)
PASTA_CDP_FUNDAMENTAL = BASE_DIR / "Planos feitos" / "Habilidades CDP fundamental"

SEQUENCIA_PADRAO_CDP_MULTISSERIADA = [
    "PORTUGUÊS",
    "MATEMÁTICA",
    "HISTÓRIA",
    "GEOGRAFIA",
    "ARTES",
    "MATEMÁTICA",
    "PORTUGUÊS",
    "PORTUGUÊS",
    "MATEMÁTICA",
    "CIÊNCIAS",
    "ARTES",
    "MATEMÁTICA",
]

ARQUIVOS_CDP_FUNDAMENTAL = {
    "português": "portugues_cdp_20.docx",
    "matematica": "matematica_cdp_20.docx",
    "história": "historia_cdp_profissional.docx",
    "geografia": "geografia_cdp_profissional.docx",
    "ciências": "ciencias_cdp_profissional.docx",
    "arte": "arte_cdp_profissional.docx",
}


# ← ADICIONADO: Função para buscar arquivo com fallback
def obter_arquivo_cdp_fundamental(disciplina: str) -> str:
    """Busca arquivo CDP com fallback seguro."""
    import logging
    logger = logging.getLogger(__name__)

    disc_norm = normalizar(disciplina)
    arquivo = ARQUIVOS_CDP_FUNDAMENTAL.get(disc_norm)

    if not arquivo:
        logger.warning(f"Disciplina '{disciplina}' não tem arquivo CDP específico. Usando padrão.")
        arquivo = "cdp_default.docx"  # Fallback padrão

    return arquivo


def normalizar(texto: str = "") -> str:
    texto = (texto or "").strip().lower()
    for origem, destino in {
        "á": "a", "à": "a", "â": "a", "ã": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
        "ę": "e",
        "°": "º",
    }.items():
        texto = texto.replace(origem, destino)
    return texto


def disciplina_da_linha(texto: str) -> str:
    txt = normalizar(texto)
    if "portugues" in txt:
        return "português"
    if "matematica" in txt:
        return "matematica"
    if "historia" in txt:
        return "história"
    if "geografia" in txt:
        return "geografia"
    if "ciencia" in txt:
        return "ciências"
    if "arte" in txt or "artes" in txt:
        return "arte"
    return ""


def componente_da_linha_multisseriada(texto: str) -> str:
    txt = normalizar(texto)
    if "portugues" in txt:
        return "Língua Portuguesa"
    if "matematica" in txt:
        return "Matemática"
    if "historia" in txt:
        return "História"
    if "geografia" in txt:
        return "Geografia"
    if "ciencia" in txt:
        return "Ciências Naturais"
    if "arte" in txt or "artes" in txt:
        return "Arte"
    if "ingles" in txt or "estrangeira" in txt:
        return "Língua Estrangeira"
    if "educacao fisica" in txt or "educação física" in txt:
        return "Educação Física"
    return ""


def anos_da_turma(turma: str = "") -> List[str]:
    turma_norm = normalizar(turma)
    if "1º" in turma_norm and "2º" in turma_norm and "3º" in turma_norm:
        return ["1º ano", "2º ano", "3º ano"]
    if "4º" in turma_norm and "5º" in turma_norm:
        return ["4º ano", "5º ano"]

    encontrados = re.findall(r"\b([1-5])\s*[º°o]?", turma or "")
    if encontrados:
        return [f"{ano}º ano" for ano in encontrados]
    return ["4º ano", "5º ano"]


def _coluna(ref: str) -> str:
    m = re.match(r"([A-Z]+)", ref or "")
    return m.group(1) if m else ""


def _shared_strings(z: ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.findall(".//a:t", NS)) for si in root.findall("a:si", NS)]


def _sheet_paths(z: ZipFile) -> Dict[str, str]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: "xl/" + rel.attrib["Target"].lstrip("/")
        for rel in rels
    }
    paths = {}
    for sheet in wb.findall("a:sheets/a:sheet", NS):
        nome = sheet.attrib.get("name", "")
        rid = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        if nome and rid in rel_map:
            paths[nome] = rel_map[rid]
    return paths


def _ler_linhas_sheet(z: ZipFile, sheet_path: str, strings: List[str]) -> List[Dict[str, str]]:
    root = ET.fromstring(z.read(sheet_path))
    linhas = []
    cabecalho: Dict[str, str] = {}
    cabecalho_encontrado = False
    nomes_cabecalho = {"ano", "bimestre", "aula", "habilidades", "titulo", "conteudo"}
    for row in root.findall(".//a:row", NS):
        valores: Dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            value = cell.find("a:v", NS)
            texto = ""
            if value is not None:
                texto = value.text or ""
                if cell.attrib.get("t") == "s" and texto.isdigit():
                    i = int(texto)
                    texto = strings[i] if i < len(strings) else ""
            valores[_coluna(cell.attrib.get("r", ""))] = re.sub(r"\s+", " ", texto).strip()
        if not cabecalho_encontrado:
            normalizados = {normalizar(valor) for valor in valores.values() if valor}
            if len(normalizados & nomes_cabecalho) >= 2 or "habilidades" in normalizados:
                cabecalho_encontrado = True
                cabecalho = valores
            continue
        if not valores:
            continue
        item = {nome: valores.get(coluna, "") for coluna, nome in cabecalho.items() if nome}
        if item:
            linhas.append(item)
    return linhas


def _nome_sheet_multisseriada(componente: str, dados: Dict[str, List[Dict[str, str]]]) -> str:
    componente_norm = normalizar(componente)
    mapa = {
        "lingua portuguesa": "portugues",
        "portugues": "portugues",
        "matematica": "matematica",
        "historia": "historia",
        "geografia": "geografia",
        "ciencias naturais": "ciencias",
        "ciencia": "ciencias",
        "ciencias": "ciencias",
        "arte": "arte",
        "artes": "arte",
    }
    alvo = mapa.get(componente_norm, componente_norm)
    for nome in dados:
        if alvo in normalizar(nome):
            return nome
    return componente


def _linhas_multisseriada_por_componente(componente: str) -> List[Dict[str, str]]:
    dados = carregar_planilha_cdp_multisseriada()
    if not dados:
        return []
    sheet = _nome_sheet_multisseriada(componente, dados)
    return dados.get(sheet, [])


def _numero_bimestre(texto: str = "") -> str:
    match = re.search(r"([1-4])", texto or "")
    return match.group(1) if match else ""


def _ano_da_linha_multisseriada(linha: Dict[str, str]) -> str:
    ano = _primeiro_valor(linha, "ANO", "Ano", "Série", "SERIE")
    if ano:
        return ano
    habilidade = _primeiro_valor(linha, "HABILIDADES", "Habilidades")
    match = re.search(r"\(EF0?([1-5])", habilidade)
    if match:
        return f"{int(match.group(1))}º ano"
    return ""


def _linha_pertence_bimestre(linha: Dict[str, str], bimestre: str = "") -> bool:
    numero = _numero_bimestre(bimestre)
    if not numero:
        return True
    return _numero_bimestre(_primeiro_valor(linha, "BIMESTRE", "Bimestre")) == numero


def _linha_multisseriada_tem_conteudo(linha: Dict[str, str]) -> bool:
    return bool(_primeiro_valor(
        linha,
        "HABILIDADES",
        "Habilidades",
        "Habilidades Específicas",
        "Habilidades Procedimentais",
        "Habilidade/Conteúdo",
        "TÍTULO",
        "TEMA",
        "CONTEÚDO",
        "Conteúdo",
        "OBJETIVOS",
        "Objetivos",
        "OBJETO DE CONHECIMENTO",
    ))


def _linha_pertence_turma_multisseriada(linha: Dict[str, str], turma: str = "") -> bool:
    if not turma:
        return True
    anos_alvo = {normalizar(ano) for ano in anos_da_turma(turma)}
    ano_linha = normalizar(_ano_da_linha_multisseriada(linha))
    if ano_linha:
        return ano_linha in anos_alvo

    # Compatibilidade com a planilha antiga, que usava séries do ciclo II.
    turma_norm = normalizar(turma)
    if "1º" in turma_norm and "2º" in turma_norm and "3º" in turma_norm:
        series_alvo = {normalizar("5ª série"), normalizar("6ª série"), normalizar("7ª série")}
    elif "4º" in turma_norm and "5º" in turma_norm:
        series_alvo = {normalizar("8ª série"), normalizar("9ª série")}
    else:
        series_alvo = {turma_norm}
    return normalizar(_primeiro_valor(linha, "Série", "SERIE")) in series_alvo


def _filtrar_linhas_multisseriadas(
        linhas: List[Dict[str, str]],
        turma: str = "",
        bimestre: str = "",
) -> List[Dict[str, str]]:
    if not linhas:
        return []

    linhas_validas = [linha for linha in linhas if _linha_multisseriada_tem_conteudo(linha)]
    por_turma = [linha for linha in linhas_validas if _linha_pertence_turma_multisseriada(linha, turma)]
    base = por_turma if por_turma else []
    por_bimestre = [linha for linha in base if _linha_pertence_bimestre(linha, bimestre)]
    return por_bimestre or base


def _nome_componente_exibicao(nome: str) -> str:
    nome_norm = normalizar(nome)
    if "portugues" in nome_norm:
        return "Língua Portuguesa"
    if "ciencia" in nome_norm:
        return "Ciências"
    if "matematica" in nome_norm:
        return "Matemática"
    if "historia" in nome_norm:
        return "História"
    if "geografia" in nome_norm:
        return "Geografia"
    if "arte" in nome_norm:
        return "Arte"
    return nome


def _remover_duplicatas_preservando_ordem(valores: List[str]) -> List[str]:
    vistos = set()
    saida = []
    for valor in valores:
        chave = normalizar(valor)
        if not valor or chave in vistos:
            continue
        vistos.add(chave)
        saida.append(valor)
    return saida


@lru_cache(maxsize=1)
def carregar_planilha_cdp_multisseriada() -> Dict[str, List[Dict[str, str]]]:
    """
    Carrega a planilha específica do CDP multisseriado (EJA) e retorna dados por sheet.
    """
    if not PLANILHA_CDP_MULTISSERIADA.exists():
        return {}
    with ZipFile(PLANILHA_CDP_MULTISSERIADA) as z:
        strings = _shared_strings(z)
        sheets = _sheet_paths(z)
        dados: Dict[str, List[Dict[str, str]]] = {}
        for nome, path in sheets.items():
            if normalizar(nome) == "resumo geral":
                continue
            componente = _nome_componente_exibicao(nome)
            dados[componente] = _ler_linhas_sheet(z, path, strings)
        return dados


def _valor_celula_linha(row, idx: int) -> str:
    if idx >= len(row.cells):
        return ""
    return re.sub(r"\s+", " ", row.cells[idx].text or "").strip()


def _ler_habilidades_docx(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    doc = Document(path)
    linhas: List[Dict[str, str]] = []
    aula = 1
    for table in doc.tables:
        if not table.rows:
            continue
        cabecalho = [normalizar(cell.text) for cell in table.rows[0].cells]
        if not any("habilidade" in col for col in cabecalho):
            continue

        for row in table.rows[1:]:
            unidade = _valor_celula_linha(row, 0)
            objeto = _valor_celula_linha(row, 1)
            habilidade = _valor_celula_linha(row, 2)
            if not any([unidade, objeto, habilidade]):
                continue
            linhas.append({
                "AULA": str(aula),
                "BIMESTRE": "",
                "ANO": "Ensino Fundamental",
                "UNIDADE TEMÁTICA": unidade,
                "OBJETO DE CONHECIMENTO": objeto,
                "OBJETOS DE CONHECIMENTO": objeto,
                "CONTEÚDO": objeto,
                "TÍTULO": objeto or unidade or "Conteúdo proposto",
                "HABILIDADES": habilidade,
                "OBJETIVOS": habilidade,
            })
            aula += 1
    return linhas


@lru_cache(maxsize=1)
def carregar_planilha_cdp() -> Dict[str, List[Dict[str, str]]]:
    """
    Carrega a planilha CDP e retorna dados estruturados por sheet.
    Cada sheet contém lista de dicionários com colunas da planilha.
    """
    if not PLANILHA_CDP.exists():
        return {}
    with ZipFile(PLANILHA_CDP) as z:
        strings = _shared_strings(z)
        sheets = _sheet_paths(z)
        return {
            nome: _ler_linhas_sheet(z, path, strings)
            for nome, path in sheets.items()
        }


def listar_habilidades_cdp(disciplina: str, turma: str = "", bimestre: str = "1°") -> List[Dict[str, str]]:
    """
    Lista todas as habilidades (alfanuméricas) de uma disciplina para seleção pelo usuário.
    Retorna lista de dicts com 'codigo' (ex: EF15LP01) e 'descricao' (ex: tema + conteúdo).
    Filtra por turma (se multisseriada) e bimestre (se especificado).
    """
    dados = carregar_planilha_cdp()
    linhas = dados.get(disciplina, [])

    if not linhas:
        return []

    # Filtrar por turma (multisseriada 1-3 ou 4-5)
    anos = [normalizar(a) for a in anos_da_turma(turma)]
    filtradas = [
        linha for linha in linhas
        if normalizar(linha.get("ANO", "")) in anos
           and (not bimestre or normalizar(linha.get("BIMESTRE", "")) == normalizar(bimestre))
    ]

    if not filtradas:
        filtradas = [linha for linha in linhas if normalizar(linha.get("ANO", "")) in anos]

    if not filtradas:
        filtradas = linhas

    # Montar lista de habilidades para exibição
    habilidades = []
    vistas = set()

    for linha in filtradas:
        # Extrair código da habilidade (ex: EF15LP01)
        codigo = linha.get("HABILIDADES", "").strip()
        if not codigo or codigo in vistas:
            continue

        vistas.add(codigo)
        titulo = linha.get("TÍTULO", "")
        conteudo = linha.get("CONTEÚDO", titulo)

        habilidades.append({
            "codigo": codigo,
            "descricao": f"{codigo} - {conteudo}",
            "titulo": titulo,
            "dados_completos": linha  # Guardar para depois preencher o DOCX
        })

    return habilidades


def listar_componentes_cdp_multisseriada() -> List[str]:
    dados = carregar_planilha_cdp_multisseriada()
    return _remover_duplicatas_preservando_ordem([
        _nome_componente_exibicao(nome)
        for nome in dados.keys()
        if normalizar(nome) != "resumo geral"
    ])


def _colunas_multisseriadas(componente: str) -> tuple[str, str]:
    componente_norm = normalizar(componente)
    mapa = {
        # Estrutura atual: Planos feitos/Planilhas organizadas/cdp-habilidades.xlsx
        "arte": ("HABILIDADES", "TÍTULO"),
        "ciencias": ("HABILIDADES", "TÍTULO"),
        "historia": ("HABILIDADES", "CONTEÚDO"),
        "geografia": ("HABILIDADES", "TEMA"),
        "matematica": ("HABILIDADES", "TÍTULO"),
        "lingua portuguesa": ("HABILIDADES", "TÍTULO"),
        "portugues": ("HABILIDADES", "TÍTULO"),
        # Compatibilidade com a planilha antiga.
        "ciencias naturais": ("HABILIDADES", "TÍTULO"),
        "lingua estrangeira": ("Habilidades", "Conteúdos Principais"),
        "educacao fisica": ("Habilidades", "Características"),
    }
    legado = {
        "arte": ("Habilidade/Conteúdo", "Habilidade/Conteúdo"),
        "ciencias naturais": ("Habilidades Específicas", "Conteúdo Principal"),
        "geografia": ("Habilidades Específicas", "Conteúdo Principal (%)"),
        "historia": ("Habilidades Procedimentais", "Conteúdo"),
        "matematica": ("Conteúdos Considerados Relevantes", "Conteúdos Ensinados (%)"),
        "lingua portuguesa": ("Habilidades", "Foco do Ensino"),
        "lingua estrangeira": ("Habilidades", "Conteúdos Principais"),
        "educacao fisica": ("Habilidades", "Características"),
    }
    return mapa.get(componente_norm, legado.get(componente_norm, ("HABILIDADES", "CONTEÚDO")))


def _primeiro_valor(item: Dict[str, str], *chaves: str) -> str:
    for chave in chaves:
        valor = str(item.get(chave, "") or "").strip()
        if valor:
            return valor
    return ""


def limpar_texto_cdp(texto: str = "") -> str:
    texto = re.sub(r"\s*\([^)]*\d+(?:[,.]\d+)?\s*%[^)]*\)", "", texto or "")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def titulo_item_cdp(item: Dict[str, str]) -> str:
    return limpar_texto_cdp(_primeiro_valor(
        item,
        "TÍTULO",
        "TEMA",
        "CONTEÚDO",
        "Conteúdo Principal",
        "Conteúdo Principal (%)",
        "Conteúdo",
        "OBJETOS DE CONHECIMENTO",
        "Conteúdos Ensinados (%)",
        "Conteúdos Principais",
        "Característica",
        "Características",
        "Subcategoria",
        "Categoria",
        "Concepção",
        "Aspecto",
        "Habilidade/Conteúdo",
    ))


def habilidade_item_cdp(item: Dict[str, str]) -> str:
    return limpar_texto_cdp(_primeiro_valor(
        item,
        "HABILIDADES",
        "Habilidades Específicas",
        "Habilidades Procedimentais",
        "Habilidades",
        "Habilidade/Conteúdo",
        "Conteúdos Considerados Relevantes",
    ))


def objeto_item_cdp(item: Dict[str, str]) -> str:
    return limpar_texto_cdp(_primeiro_valor(
        item,
        "OBJETOS DE CONHECIMENTO",
        "OBJETO DE CONHECIMENTO",
        "CONTEÚDO",
        "Conteúdo",
        "Conteúdo Principal",
        "Conteúdo Principal (%)",
        "Conteúdos Ensinados (%)",
        "Conteúdos Principais",
        "Estratégias Didáticas",
        "Abordagens Inovadoras",
        "Observações",
        "Características",
    ))


def _titulo_para_frase(titulo: str) -> str:
    return (titulo or "").strip().rstrip(".!?;:")


def listar_habilidades_cdp_multisseriada(
        componente: str,
        turma: str = "",
        bimestre: str = "",
) -> List[Dict[str, str]]:
    linhas = _linhas_multisseriada_por_componente(componente)
    if not linhas:
        return []

    filtradas = _filtrar_linhas_multisseriadas(linhas, turma, bimestre)
    habilidades = []
    vistas = set()
    coluna_habilidade, coluna_titulo = _colunas_multisseriadas(componente)
    for linha in filtradas:
        conteudo = _primeiro_valor(
            linha,
            coluna_titulo,
            "TÍTULO",
            "TEMA",
            "CONTEÚDO",
            "Conteúdo",
            "Subcategoria",
        )
        habilidade = _primeiro_valor(
            linha,
            coluna_habilidade,
            "HABILIDADES",
            "Habilidades",
            "Habilidades Específicas",
            "Habilidades Procedimentais",
        )
        if not habilidade or habilidade in vistas:
            continue
        vistas.add(habilidade)
        habilidades.append({
            "codigo": habilidade,
            "descricao": f"{habilidade} - {conteudo or componente}",
            "titulo": conteudo or componente,
            "dados_completos": linha,
        })
    return habilidades


def buscar_item_por_habilidade_cdp_multisseriada(
        componente: str,
        habilidade_codigo: str,
        turma: str = "",
        bimestre: str = "",
) -> Dict[str, str]:
    linhas = _linhas_multisseriada_por_componente(componente)
    if not linhas:
        return {}
    filtradas = _filtrar_linhas_multisseriadas(linhas, turma, bimestre)
    coluna_habilidade, _ = _colunas_multisseriadas(componente)
    for linha in filtradas:
        habilidade = _primeiro_valor(linha, coluna_habilidade, "HABILIDADES", "Habilidades")
        if habilidade == habilidade_codigo:
            return linha
    return {}


def buscar_item_por_habilidade(disciplina: str, habilidade_codigo: str, turma: str = "", bimestre: str = "1°") -> Dict[
    str, str]:
    """
    Busca o item (linha) da planilha que corresponde à habilidade selecionada.
    Retorna o dicionário completo com todos os campos.
    """
    dados = carregar_planilha_cdp()
    linhas = dados.get(disciplina, [])

    if not linhas:
        return {}

    # Filtrar por turma e bimestre
    anos = [normalizar(a) for a in anos_da_turma(turma)]
    filtradas = [
        linha for linha in linhas
        if normalizar(linha.get("ANO", "")) in anos
           and (not bimestre or normalizar(linha.get("BIMESTRE", "")) == normalizar(bimestre))
    ]

    if not filtradas:
        filtradas = [linha for linha in linhas if normalizar(linha.get("ANO", "")) in anos]

    if not filtradas:
        filtradas = linhas

    # Encontrar a linha com a habilidade correspondente
    for linha in filtradas:
        if linha.get("HABILIDADES", "").strip() == habilidade_codigo:
            return linha

    return {}


@lru_cache(maxsize=1)
def carregar_habilidades_cdp_fundamental() -> Dict[str, List[Dict[str, str]]]:
    return {
        disciplina: _ler_habilidades_docx(PASTA_CDP_FUNDAMENTAL / arquivo)
        for disciplina, arquivo in ARQUIVOS_CDP_FUNDAMENTAL.items()
    }


def _selecionar_por_contador(linhas: List[Dict[str, str]], contador: int, aula_inicial: int = 1) -> Dict[str, str]:
    if not linhas:
        return {}
    inicio = max(int(aula_inicial or 1), 1)
    tem_aula = any(str(linha.get("AULA", "")).strip().isdigit() for linha in linhas)
    if inicio > 1 and tem_aula:
        filtradas = [
            linha for linha in linhas
            if str(linha.get("AULA", "")).strip().isdigit()
               and int(str(linha.get("AULA", "")).strip()) >= inicio
        ]
        if not filtradas:
            return {}
    else:
        filtradas = linhas
    return filtradas[contador % len(filtradas)]


def selecionar_item(
        disciplina: str,
        contador: int,
        turma: str = "",
        bimestre: str = "1°",
        aula_inicial: int = 1,
        fundamental: bool = False,
        multisseriada: bool = False,
        componente_cdp: str = "",
) -> Dict[str, str]:
    if fundamental:
        dados_fundamental = carregar_habilidades_cdp_fundamental()
        return _selecionar_por_contador(dados_fundamental.get(disciplina, []), contador, aula_inicial)

    if multisseriada:
        componente = componente_cdp or componente_da_linha_multisseriada(disciplina) or disciplina
        linhas = _linhas_multisseriada_por_componente(componente)
        linhas = _filtrar_linhas_multisseriadas(linhas, turma, bimestre)
        return _selecionar_por_contador(linhas, contador, aula_inicial)

    dados = carregar_planilha_cdp()
    linhas = dados.get(disciplina, [])
    anos = [normalizar(a) for a in anos_da_turma(turma)]
    filtradas = [
        linha for linha in linhas
        if normalizar(linha.get("ANO", "")) in anos
           and (not bimestre or normalizar(linha.get("BIMESTRE", "")) == normalizar(bimestre))
    ]
    if not filtradas:
        filtradas = [linha for linha in linhas if normalizar(linha.get("ANO", "")) in anos]
    if not filtradas:
        filtradas = linhas
    if not filtradas:
        return {}

    return _selecionar_por_contador(filtradas, contador, aula_inicial)


def _metodologia_cdp_por_modelo(disciplina: str, tema: str, objeto: str) -> str:
    disciplina_norm = normalizar(disciplina)
    tema_frase = _titulo_para_frase(tema or objeto or "conteúdo proposto")

    if "portugues" in disciplina_norm or "lingua" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com uma conversa breve sobre o tema {tema_frase}, perguntando o que os alunos já sabem "
            "e registrando no quadro palavras ou ideias importantes.\n\n"
            "2. Desenvolvimento: realizar leitura mediada do texto ou apresentação do conteúdo, explicando vocabulário, "
            "informações principais e exemplos simples. Durante a explicação, fazer perguntas orais para verificar a compreensão.\n\n"
            "3. Atividade: orientar os alunos na resolução das questões de leitura, escrita ou interpretação no caderno, "
            "acompanhando a turma e auxiliando quem apresentar dificuldade.\n\n"
            "4. Fechamento: realizar correção coletiva, retomar as respostas principais e registrar uma síntese simples do que foi estudado."
        )

    if "matematica" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com uma situação do cotidiano relacionada ao tema {tema_frase}, como contagens, medidas, "
            "compras, horários, formas ou organização de quantidades.\n\n"
            "2. Desenvolvimento: explicar o conteúdo no quadro com exemplos simples e resolução passo a passo, mostrando como "
            "organizar os cálculos, desenhos, tabelas ou registros necessários.\n\n"
            "3. Atividade: propor exercícios no caderno, permitindo que os alunos resolvam com apoio do professor e comparem "
            "suas estratégias durante a correção.\n\n"
            "4. Fechamento: conferir os resultados coletivamente e retomar o procedimento principal da aula."
        )

    if "historia" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com uma pergunta simples sobre o tema {tema_frase}, relacionando o assunto a experiências, "
            "memórias ou situações conhecidas pela turma.\n\n"
            "2. Desenvolvimento: explicar o conteúdo de forma dialogada, destacando acontecimentos, personagens, mudanças, "
            "permanências e relações entre passado e presente.\n\n"
            "3. Atividade: orientar registros no caderno e questões de compreensão, acompanhando as respostas e retomando "
            "os pontos que gerarem dúvida.\n\n"
            "4. Fechamento: fazer correção coletiva e organizar no quadro as ideias principais estudadas."
        )

    if "geografia" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com conversa sobre lugares, paisagens, moradias, deslocamentos ou situações do cotidiano "
            f"relacionadas ao tema {tema_frase}.\n\n"
            "2. Desenvolvimento: apresentar o conteúdo com explicação clara, exemplos próximos da realidade dos alunos e "
            "registros no quadro para organizar as informações.\n\n"
            "3. Atividade: propor observação, comparação, identificação ou registro no caderno, acompanhando a turma durante "
            "a realização das tarefas.\n\n"
            "4. Fechamento: socializar algumas respostas, corrigir as atividades e retomar o conceito principal da aula."
        )

    if "ciencia" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com exemplos do cotidiano relacionados ao tema {tema_frase}, perguntando o que os alunos "
            "observam em casa, na escola ou na comunidade.\n\n"
            "2. Desenvolvimento: explicar o conteúdo com linguagem simples, exemplos concretos, esquemas no quadro e perguntas "
            "orais para verificar a compreensão.\n\n"
            "3. Atividade: orientar atividades de identificação, classificação, registro ou interpretação, acompanhando os alunos "
            "durante a realização das questões.\n\n"
            "4. Fechamento: corrigir coletivamente e retomar os cuidados, conceitos ou informações principais da aula."
        )

    if "arte" in disciplina_norm:
        return (
            f"1. Abertura: iniciar com conversa sobre manifestações artísticas, culturais ou corporais relacionadas ao tema {tema_frase}, "
            "valorizando experiências conhecidas pelos alunos.\n\n"
            "2. Desenvolvimento: apresentar o conteúdo com exemplos simples, explicação oral e demonstração da proposta quando necessário.\n\n"
            "3. Atividade: orientar produção, registro, apreciação ou movimento, acompanhando a participação da turma e respeitando "
            "diferentes formas de expressão.\n\n"
            "4. Fechamento: socializar as produções ou comentários e retomar as ideias principais da aula."
        )

    return (
        f"1. Abertura: iniciar com conversa breve sobre o tema {tema_frase}, levantando conhecimentos prévios dos alunos.\n\n"
        "2. Desenvolvimento: apresentar o conteúdo com linguagem simples, exemplos próximos da realidade da turma e registros no quadro.\n\n"
        "3. Atividade: orientar exercícios ou registros no caderno, acompanhando a realização das tarefas e apoiando quem precisar.\n\n"
        "4. Fechamento: realizar correção coletiva e retomar os principais pontos trabalhados."
    )


def montar_metodologia_cdp(disciplina: str, item: Dict[str, str], fundamental: bool = False) -> str:
    """
    Monta a metodologia específica do CDP em linguagem simples e direta.
    """
    titulo = titulo_item_cdp(item) or "conteúdo proposto"
    objeto = objeto_item_cdp(item) or titulo
    return _metodologia_cdp_por_modelo(disciplina, titulo, objeto)


def montar_acompanhamento_cdp(disciplina: str, item: Dict[str, str], fundamental: bool = False) -> List[str]:
    """
    Monta acompanhamento simples para CDP.
    """
    disciplina_norm = normalizar(disciplina)
    tema = _titulo_para_frase(titulo_item_cdp(item) or objeto_item_cdp(item) or "conteúdo trabalhado")

    if "portugues" in disciplina_norm or "lingua" in disciplina_norm:
        return [
            "☑ Participação durante a leitura e a conversa inicial.",
            f"☑ Compreensão do tema {tema} nas respostas orais e escritas.",
            "☑ Organização das atividades de leitura, escrita e interpretação no caderno.",
        ]
    if "matematica" in disciplina_norm:
        return [
            "☑ Participação na resolução das atividades propostas.",
            f"☑ Compreensão do tema {tema} por meio dos cálculos, registros e explicações.",
            "☑ Organização dos procedimentos e participação na correção coletiva.",
        ]
    if "historia" in disciplina_norm:
        return [
            "☑ Participação durante a conversa e a explicação do conteúdo.",
            f"☑ Compreensão do tema {tema} nas atividades e registros realizados.",
            "☑ Relação entre as informações estudadas e os exemplos trabalhados em aula.",
        ]
    if "geografia" in disciplina_norm:
        return [
            "☑ Participação na conversa inicial e nos exemplos apresentados.",
            f"☑ Compreensão do tema {tema} nas atividades de observação, comparação e registro.",
            "☑ Relação entre o conteúdo e situações do espaço vivido pelos alunos.",
        ]
    if "ciencia" in disciplina_norm:
        return [
            "☑ Participação nas conversas e exemplos apresentados.",
            f"☑ Compreensão do tema {tema} nas atividades de identificação, registro ou classificação.",
            "☑ Respostas apresentadas durante a correção coletiva e a retomada do conteúdo.",
        ]
    if "arte" in disciplina_norm:
        return [
            "☑ Participação na conversa, apreciação ou atividade artística.",
            f"☑ Compreensão do tema {tema} por meio de registros, comentários ou produções.",
            "☑ Envolvimento e expressão durante a atividade proposta.",
        ]

    return [
        "☑ Participação durante a conversa inicial e as atividades propostas.",
        f"☑ Compreensão do tema {tema} por meio das respostas orais e escritas.",
        "☑ Organização dos registros no caderno e participação na correção coletiva.",
    ]


def montar_acessibilidade_cdp(disciplina: str, item: Dict[str, str], fundamental: bool = False) -> List[str]:
    """
    Monta acessibilidade simples para CDP.
    """
    disciplina_norm = normalizar(disciplina)

    if "portugues" in disciplina_norm or "lingua" in disciplina_norm:
        return [
            "☑ Leitura pausada, com explicação oral de palavras e trechos mais difíceis.",
            "☑ Registro no quadro para organizar as informações principais.",
            "☑ Apoio individual nas atividades de leitura, escrita e interpretação.",
        ]
    if "matematica" in disciplina_norm:
        return [
            "☑ Explicação passo a passo com exemplos concretos e registros no quadro.",
            "☑ Retomada oral dos procedimentos antes da resolução das atividades.",
            "☑ Apoio individual na organização dos cálculos e respostas.",
        ]
    if "historia" in disciplina_norm:
        return [
            "☑ Explicação oral pausada dos conteúdos históricos.",
            "☑ Registro de palavras-chave e exemplos simples no quadro.",
            "☑ Apoio individual na interpretação e organização das respostas.",
        ]
    if "geografia" in disciplina_norm:
        return [
            "☑ Explicação oral pausada com exemplos do município, da comunidade e dos espaços de vivência.",
            "☑ Registro no quadro para organizar conceitos e exemplos.",
            "☑ Apoio individual na leitura, interpretação e registro das atividades.",
        ]
    if "ciencia" in disciplina_norm:
        return [
            "☑ Explicação oral pausada com exemplos concretos e próximos da realidade dos alunos.",
            "☑ Esquemas simples no quadro para organizar as informações.",
            "☑ Apoio individual na leitura, escrita e compreensão das atividades.",
        ]
    if "arte" in disciplina_norm:
        return [
            "☑ Orientações orais claras, com demonstração simples da atividade antes da realização.",
            "☑ Possibilidade de participação por meio de desenho, movimento, fala, registro ou apreciação.",
            "☑ Apoio individual na organização da produção ou expressão das ideias.",
        ]

    return [
        "☑ Linguagem simples e explicação oral pausada.",
        "☑ Registro no quadro para apoiar a organização das informações.",
        "☑ Apoio individual aos alunos com dificuldade na realização das atividades.",
    ]
