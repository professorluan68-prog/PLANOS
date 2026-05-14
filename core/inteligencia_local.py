import re
import unicodedata
from typing import Dict, List, Any
from core.base_conhecimento import PADROES_DISCIPLINARES, TECNICAS_UNIVERSAIS

# ── Técnicas Lemov completas ─────────────────────────────────────────────────
TECNICAS_LEMOV = {
    "interacao": [
        "Virem e conversem",
        "Virar e conversar",
    ],
    "registro": [
        "Todo mundo escreve",
    ],
    "verificacao": [
        "Verificar a compreensão",
        "Bilhete de saída",
    ],
    "mediacao": [
        "Circular pela sala",
    ],
    "sintese": [
        "Com suas palavras",
    ],
}

_TRECHOS_DESCARTAVEIS = (
    "freepik",
    "seduc-sp",
    "produzido pela",
    "veja no livro",
    "de olho no pnld",
    "link para",
    "disponivel em",
    "disponível em",
    "slide",
)
_FINS_FRAGMENTADOS = {"a", "as", "o", "os", "um", "uma", "de", "da", "das", "do", "dos", "em", "e", "com", "para", "por"}


def _normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _limpar_trecho(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip(" -:;•●")
    texto = re.sub(r"\.{2,}", ".", texto)
    return texto.strip()


def _trecho_descartavel(texto: str) -> bool:
    texto = _limpar_trecho(texto)
    if not texto:
        return True
    normalizado = _normalizar_texto(texto)
    if any(marcador in normalizado for marcador in _TRECHOS_DESCARTAVEIS):
        return True
    if any(seta in texto for seta in ["⬅", "←", "→"]):
        return True
    if texto.count("?") >= 2:
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and _normalizar_texto(palavras[-1]) in _FINS_FRAGMENTADOS:
        return True
    primeira = texto[:1]
    inicio = _normalizar_texto(texto)
    if primeira.islower() and not inicio.startswith(("a ", "o ", "as ", "os ", "um ", "uma ", "essa ", "esse ", "esta ", "este ")):
        return True
    return False


def _trecho_seguro(texto: str, fallback: str, limite: int = 220) -> str:
    texto = _limpar_trecho(texto)
    if _trecho_descartavel(texto):
        return fallback
    if len(texto) <= limite:
        return texto
    recorte = texto[:limite].rsplit(" ", 1)[0].strip()
    return recorte if not _trecho_descartavel(recorte) else fallback


class ClassificadorConteudo:
    def analisar(self, texto: str, disciplina: str) -> Dict[str, str]:
        disciplina_lower = disciplina.lower()
        perfil = "geral"
        
        # Detecta o perfil disciplinar
        for p in PADROES_DISCIPLINARES.keys():
            if p.replace("_", " ") in disciplina_lower or p in disciplina_lower:
                perfil = p
                break
        
        # Fallbacks para disciplinas comuns
        if "portugues" in disciplina_lower or "redacao" in disciplina_lower:
            perfil = "lingua_portuguesa"
        elif "projeto de vida" in disciplina_lower:
            perfil = "projeto_de_vida"
            
        # Detecta tipo de aula baseado no conteúdo (verbos e palavras-chave)
        tipo = "conceitual"
        texto_lower = texto.lower()
        if re.search(r'\b(exercício|atividade|resolução|calcule|resolva|pratique)\b', texto_lower):
            tipo = "pratica"
        elif re.search(r'\b(revisão|retomada|relembre|resumo)\b', texto_lower):
            tipo = "revisao"
            
        return {
            "perfil": perfil,
            "tipo": tipo
        }


class ExtratorInteligentePDF:
    """Extrai partes reais do conteúdo do PDF com heurísticas aprimoradas."""

    # Padrões de habilidades BNCC / AE
    _PADRAO_HABILIDADE = re.compile(
        r'((?:EM|EF)\d{2}[A-Z]{2}\d{2}[A-Z]?'   # EM13LP44A, EF09HI01
        r'|AE\d+\s*[-–]?\s*[^\n]{10,})',           # AE1 - Identificar...
        re.IGNORECASE
    )
    _PADRAO_HABILIDADE_TEXTO = re.compile(
        r'(?:habilidade|aprendizagem essencial|competência)[:\s]*([^\n]{20,})',
        re.IGNORECASE
    )

    def extrair_estruturado(self, texto: str, tema: str) -> Dict[str, Any]:
        linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
        
        conceito = tema
        atividade_pratica = ""
        habilidade = ""
        contexto_aula = ""
        palavras_chave = []
        
        # 1. Extrair habilidade/BNCC
        for linha in linhas:
            m = self._PADRAO_HABILIDADE.search(linha)
            if m:
                habilidade = linha.strip()
                break
        if not habilidade:
            for linha in linhas:
                m = self._PADRAO_HABILIDADE_TEXTO.search(linha)
                if m:
                    habilidade = m.group(1).strip()
                    break

        # Palavras que devem ser filtradas dos blocos de conceito/prática
        _filtros = ["todo mundo escreve", "virem e conversem", "com suas palavras",
                    "hora da leitura", "de olho no modelo", "link para vídeo",
                    "um passo de cada vez", "slide", "aula", "veja no livro",
                    "freepik", "produzido pela", "seduc-sp", "de olho no pnld"]

        def _linha_valida(l: str) -> bool:
            ll = l.lower()
            return len(l) > 10 and not any(ll.startswith(f) or ll == f or f in ll for f in _filtros)

        # 2. Heurística de conceito: busca por definições explícitas
        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()
            marcadores = ["o que é", "definição", "conceito", "é o uso de", "é uma estratégia",
                          "consiste em", "refere-se a", "trata-se de", "podemos definir"]
            if any(m in linha_lower for m in marcadores):
                bloco = []
                # Pega a própria linha se for longa o suficiente
                if _linha_valida(linha):
                    bloco.append(linha)
                for j in range(i+1, min(i+4, len(linhas))):
                    if _linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    conceito = " ".join(bloco)[:300]
                break

        # 3. Heurística de prática aprimorada
        marcadores_pratica = ["atividade", "exercício", "na prática", "veja no livro",
                              "assistam", "leiam o texto", "analise", "compare",
                              "identifique", "reescreva", "produz"]
        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()
            if any(m in linha_lower for m in marcadores_pratica) and len(linha) > 15:
                bloco = []
                if _linha_valida(linha):
                    bloco.append(linha)
                for j in range(i+1, min(i+5, len(linhas))):
                    if _linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    atividade_pratica = " ".join(bloco)[:300]
                break
        if not atividade_pratica:
            atividade_pratica = "atividades propostas no material"

        # 4. Contexto da aula (pergunta de abertura ou situação)
        marcadores_contexto = ["você já", "pense em", "imagine", "o que as pessoas",
                               "qual é a importância", "como você", "nas últimas aulas"]
        for linha in linhas:
            linha_lower = linha.lower()
            if any(m in linha_lower for m in marcadores_contexto) and len(linha) > 20:
                contexto_aula = _trecho_seguro(linha, "", 160)
                break

        # 5. Palavras-chave do conteúdo
        for linha in linhas:
            # Linhas curtas em maiúscula ou com termos-chave
            if 5 < len(linha) < 60 and not linha.startswith("AULA") and not linha.startswith("Slide"):
                palavras_chave.append(linha)
            if len(palavras_chave) >= 5:
                break

        conceito = _trecho_seguro(conceito, tema, 220)
        atividade_pratica = _trecho_seguro(
            atividade_pratica,
            f"atividades propostas no material, articuladas ao tema {tema}",
            220,
        )
        contexto_aula = _trecho_seguro(contexto_aula, "", 160)

        return {
            "conceito_extraido": conceito,
            "atividade_extraida": atividade_pratica,
            "habilidade": habilidade,
            "contexto_aula": contexto_aula,
            "palavras_chave": palavras_chave,
            "linhas": linhas
        }


class GeradorMetodologia:
    """Gera metodologia com 6 etapas + técnicas Lemov variadas, como o sistema antigo."""

    def criar_metodologia(self, contexto: Dict[str, str], extracao: Dict[str, Any], tema: str, turma: str) -> List[Dict[str, str]]:
        perfil = contexto["perfil"]
        tipo = contexto["tipo"]
        padrao = PADROES_DISCIPLINARES.get(perfil, PADROES_DISCIPLINARES["geral"])
        
        conceito = extracao["conceito_extraido"]
        pratica = extracao["atividade_extraida"]
        contexto_aula = extracao.get("contexto_aula", "")
        
        etapas = []
        
        # ── 1. Para Começar / Relembre ──────────────────────────────────
        if tipo == "revisao":
            texto_inicio = (
                f"Retomar os conceitos trabalhados anteriormente sobre {tema}. "
            )
            if contexto_aula:
                texto_inicio += (
                    f"O professor retoma, de forma dialogada, a situação \"{contexto_aula}\", "
                    f"convidando os alunos a compartilharem percepções e experiências relacionadas ao tema. "
                )
            else:
                texto_inicio += (
                    "Promover discussão inicial sobre o tema e levantar conhecimentos prévios da turma. "
                )
            texto_inicio += "Técnica Lemov – Virar e conversar: promover troca de ideias."
            etapas.append({"titulo": "Relembre", "texto": texto_inicio})
        else:
            texto_inicio = ""
            if contexto_aula:
                texto_inicio = (
                    f"Promover discussão a partir da questão \"{contexto_aula}\". "
                    f"Levantar conhecimentos prévios dos alunos sobre o tema. "
                )
            else:
                texto_inicio = (
                    f"Promover discussão inicial sobre {tema} e levantar conhecimentos prévios da turma. "
                    f"Questionar o que os alunos já sabem sobre o assunto e quais experiências possuem. "
                )
            texto_inicio += "Técnica Lemov – Virar e conversar: promover troca de ideias."
            etapas.append({"titulo": "Para começar", "texto": texto_inicio})
        
        # ── 2. Foco no conteúdo ─────────────────────────────────────────
        texto_foco = (
            f"Apresentar o conceito central da aula: {conceito}. "
            f"{padrao['instrucoes_especificas']} "
            f"Técnica Lemov – Circular pela sala: acompanhar e orientar."
        )
        etapas.append({"titulo": "Foco no conteúdo", "texto": texto_foco})
        
        # ── 3. Na prática ───────────────────────────────────────────────
        if tipo == "pratica":
            texto_pratica = (
                f"Resolver atividades de identificação e análise sobre {tema}. "
                f"Contexto: '{pratica}'. "
                f"Analisar elementos, classificar e comparar resultados. "
                f"Aplicar conceitos em exemplos contextualizados. "
                f"Técnica Lemov – Virar e conversar: promover troca de ideias."
            )
            etapas.append({"titulo": "Na prática", "texto": texto_pratica})
        else:
            texto_pratica = (
                f"Analisar o conteúdo proposto no material: '{pratica}'. "
                f"Identificar elementos centrais e relações com o tema estudado. "
                f"Discutir efeitos de sentido e escolhas do autor. "
                f"Técnica Lemov – Virar e conversar: promover troca de ideias."
            )
            etapas.append({"titulo": "Na prática", "texto": texto_pratica})
        
        # ── 4. Sistematização ───────────────────────────────────────────
        texto_sistema = (
            f"Registrar características e conceitos trabalhados sobre {tema}. "
            f"Destacar relações, funções e elementos principais identificados durante a aula. "
            f"Técnica Lemov – Verificar a compreensão: perguntas direcionadas."
        )
        etapas.append({"titulo": "Sistematização", "texto": texto_sistema})
        
        # ── 5. Encerramento ─────────────────────────────────────────────
        texto_encerra = (
            f"Retomar a importância dos conceitos trabalhados em {tema} na interpretação e produção de conhecimento. "
            f"Refletir sobre a aplicação prática no cotidiano e em próximas etapas. "
            f"Técnica Lemov – Bilhete de saída: identificar um elemento central da aula."
        )
        etapas.append({"titulo": "Encerramento", "texto": texto_encerra})
        
        return etapas


class ValidadorQualidade:
    def refinar(self, metodologia: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove etapas vazias e formata corretamente os blocos de texto."""
        validada = []
        for etapa in metodologia:
            if etapa.get("texto") and len(etapa["texto"].strip()) > 10:
                # Capitaliza a primeira letra e garante que termina com ponto
                texto = etapa["texto"].strip()
                if not texto.endswith('.'):
                    texto += '.'
                etapa["texto"] = texto
                validada.append(etapa)
        return validada


class SistemaGeracaoMetodologica:
    def __init__(self):
        self.classificador = ClassificadorConteudo()
        self.extrator = ExtratorInteligentePDF()
        self.gerador = GeradorMetodologia()
        self.validador = ValidadorQualidade()
        
    def gerar(self, texto: str, disciplina: str, turma: str, tema: str) -> List[Dict[str, str]]:
        contexto = self.classificador.analisar(texto, disciplina)
        extracao = self.extrator.extrair_estruturado(texto, tema)
        metodologia = self.gerador.criar_metodologia(contexto, extracao, tema, turma)
        return self.validador.refinar(metodologia)
