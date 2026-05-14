"""
Classificador unificado de perfil disciplinar e tipo de aula.

Centraliza a lógica que antes estava duplicada em lote.py e avaliacao.py,
garantindo que todos os módulos usem a mesma classificação.
"""

import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza espaços para comparação."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def contem_termos(base: str, termos: list[str]) -> bool:
    """Verifica se algum dos termos aparece na string base."""
    return any(termo in base for termo in termos)


# ── Mapeamento de perfil disciplinar ────────────────────────────────────────

_MAPA_PERFIL = [
    ("orientacao_estudos", ["orientacao de estudos", "orientacao estudos", "orienestudos", "orient"]),
    ("leitura_redacao", ["redacao e leitura", "leitura e redacao", "redacao", "leitura"]),
    ("lingua_portuguesa_em", ["lingua portuguesa"]),  # refinado por turma abaixo
    ("lingua_portuguesa_ef", ["lingua portuguesa", "portugues"]),
    ("ciencias_ef", ["ciencias", "cienc"]),
    ("biologia", ["biologia", "biolog"]),
    ("quimica", ["quimica", "quim"]),
    ("fisica", ["fisica", "fis"]),
    ("historia", ["historia", "histor"]),
    ("geografia", ["geografia", "geograf"]),
    ("ingles", ["ingles", "lingua inglesa", "ingl"]),
    ("arte", ["arte"]),
    ("projeto_de_vida", ["projeto de vida", "projeto"]),
    ("educacao_financeira", ["educacao financeira", "financeir"]),
    ("matematica", ["matematica", "matem"]),
    ("tecnologia_inovacao", ["tecnologia", "inovacao", "tecnolog"]),
    ("sociologia", ["sociologia", "sociolog"]),
    ("lideranca_oratoria", ["lideranca", "oratoria", "lideranc", "orator"]),
]


def perfil_disciplina(disciplina: str) -> str:
    """Retorna o perfil pedagógico da disciplina."""
    base = normalizar_texto(disciplina)

    # Tratamento especial: LP diferencia EF vs EM
    if contem_termos(base, ["lingua portuguesa", "portugues"]):
        if contem_termos(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"

    for perfil, termos in _MAPA_PERFIL:
        if perfil.startswith("lingua_portuguesa"):
            continue  # já tratado acima
        if contem_termos(base, termos):
            return perfil

    return "geral"


# ── Detecção de tipo de aula ────────────────────────────────────────────────

_TIPOS_ESPECIFICOS = [
    ("producao", ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]),
    ("argumentacao", ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]),
    ("fonte_historica", ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]),
    ("analise_geografica", ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]),
    ("investigacao", ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]),
    ("resolucao_problemas", ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]),
    ("lingua_estrangeira", ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue"]),
    ("arte_pratica", ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]),
    ("reflexiva", ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]),
    ("leitura", ["leitura", "leia", "texto", "interpreta", "genero textual", "conto", "cronica",
                 "anuncio", "publicidade", "publicitario", "slogan", "observe"]),
]

_TIPOS_MATEMATICA = [
    ("modelagem", ["modelagem", "modelar situacoes", "metodo de polya", "polya", "representar matematicamente", "sentenca matematica"]),
    ("grandezas_medidas", ["grandeza", "razao", "proporcao"]),
    ("algebra", ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]),
    ("funcoes", ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]),
    ("combinatoria", ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha"]),
    ("estatistica_probabilidade", ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "frequencia", "censo", "pesquisa"]),
    ("geometria", ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]),
    ("numeros_operacoes", ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]),
]

_TIPOS_EDUCACAO_FINANCEIRA = [
    ("credito_endividamento", ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]),
    ("empreendedorismo", ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]),
    ("cidadania_financeira", ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]),
    ("instituicoes_financeiras", ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]),
    ("investimento_poupanca", ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]),
    ("orcamento_planejamento", ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]),
    ("consumo_consciente", ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]),
]


def detectar_tipo_aula(texto: str, tema: str, disciplina: str = "") -> str:
    """Classifica o tipo de aula a partir do conteúdo."""
    base = normalizar_texto(f"{disciplina} {tema} {texto}")
    perfil = perfil_disciplina(disciplina)

    if perfil == "matematica":
        tema_base = normalizar_texto(tema)
        for tipo, termos in _TIPOS_MATEMATICA:
            if contem_termos(base, termos) or contem_termos(tema_base, termos):
                return tipo
        return "resolucao_problemas"

    if perfil == "educacao_financeira":
        tema_base = normalizar_texto(tema)
        for tipo, termos in _TIPOS_EDUCACAO_FINANCEIRA:
            if contem_termos(base, termos) or contem_termos(tema_base, termos):
                return tipo
        return "decisao_financeira"

    for tipo, termos in _TIPOS_ESPECIFICOS:
        if contem_termos(base, termos):
            return tipo

    return "geral"


# ── Detecção de recursos no conteúdo ────────────────────────────────────────

_RECURSOS_DETECTAVEIS = {
    "leitura_texto": ["leitura", "leia", "texto", "trecho", "conto", "cronica", "poema", "artigo", "noticia"],
    "analise_imagem": ["imagem", "ilustracao", "foto", "fotografia", "pintura", "obra", "charge"],
    "analise_grafico": ["grafico", "tabela", "dados", "infografico", "mapa"],
    "calculo_resolucao": ["calcule", "resolva", "operacao", "equacao", "formula", "expressao"],
    "producao_textual": ["producao", "escreva", "redija", "rascunho", "reescrita", "revisao"],
    "experimentacao": ["experimento", "observacao", "laboratorio", "material", "procedimento"],
    "debate_oral": ["debate", "discussao", "opiniao", "argumento", "apresentacao", "oralidade"],
    "escuta_audio": ["audio", "musica", "som", "podcast", "video", "assista"],
}


def detectar_recursos(texto: str, tema: str = "") -> list[str]:
    """Detecta tipos de recursos/atividades presentes no conteúdo."""
    base = normalizar_texto(f"{tema} {texto}")
    recursos = []
    for recurso, termos in _RECURSOS_DETECTAVEIS.items():
        if contem_termos(base, termos):
            recursos.append(recurso)
    return recursos or ["leitura_texto"]  # fallback
