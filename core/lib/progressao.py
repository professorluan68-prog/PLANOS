"""
Módulo de progressão entre aulas sequenciais.

Evita que aulas com o mesmo tema ou da mesma sequência
gerem textos idênticos em acompanhamento, acessibilidade e metodologia.
"""

import hashlib


# ── Verbos de ação com variação por posição ─────────────────────────────────

VERBOS_OBSERVACAO = [
    "Observar",
    "Verificar",
    "Identificar",
    "Perceber",
    "Notar",
    "Acompanhar",
]

VERBOS_VERIFICACAO = [
    "Verificar",
    "Checar",
    "Conferir",
    "Avaliar",
    "Examinar",
    "Constatar",
]

VERBOS_ACOMPANHAMENTO = [
    "Acompanhar",
    "Monitorar",
    "Observar ao longo da aula",
    "Registrar",
    "Documentar",
    "Mapear",
]

CONECTORES_PROGRESSAO = {
    0: "durante as discussões e atividades propostas",
    1: "ao longo das etapas de trabalho",
    2: "nos registros e nas interações",
    3: "nas respostas e justificativas apresentadas",
    4: "na resolução e na socialização das atividades",
}

# ── Frases de progressão por posição na sequência ──────────────────────────

FOCO_PROGRESSAO = {
    0: "introduzir e explorar",
    1: "aprofundar e aplicar",
    2: "consolidar e sistematizar",
    3: "avaliar e retomar",
}


def _indice_hash(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(p or "") for p in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


def verbo_observacao(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de observação variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed], 3)) % len(VERBOS_OBSERVACAO)
    return VERBOS_OBSERVACAO[idx]


def verbo_verificacao(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de verificação variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed, "ver"], 3)) % len(VERBOS_VERIFICACAO)
    return VERBOS_VERIFICACAO[idx]


def verbo_acompanhamento(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de acompanhamento variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed, "acomp"], 3)) % len(VERBOS_ACOMPANHAMENTO)
    return VERBOS_ACOMPANHAMENTO[idx]


def conector_progressao(indice_aula: int) -> str:
    """Retorna um conector de progressão pela posição da aula."""
    return CONECTORES_PROGRESSAO.get(indice_aula % len(CONECTORES_PROGRESSAO), CONECTORES_PROGRESSAO[0])


def foco_progressao(indice_aula: int) -> str:
    """Retorna o foco pedagógico pela posição na sequência."""
    return FOCO_PROGRESSAO.get(indice_aula % len(FOCO_PROGRESSAO), FOCO_PROGRESSAO[0])


def ajustar_texto_por_posicao(texto: str, indice_aula: int, total_aulas: int, tema: str = "") -> str:
    """
    Ajusta sutilmente o texto de uma etapa com base na posição
    da aula na sequência, para evitar repetição.
    """
    if total_aulas <= 1:
        return texto

    posicao = indice_aula % len(FOCO_PROGRESSAO)

    # Adiciona marca de continuidade a partir da 2ª aula
    if posicao == 1 and "retomar" not in texto.lower():
        texto = texto.replace(
            "Retomar conhecimentos prévios",
            "Retomar os conceitos trabalhados na aula anterior",
            1,
        )
    elif posicao == 2 and "consolidar" not in texto.lower():
        texto = texto.replace(
            "Promover discussão inicial",
            "Retomar e consolidar as discussões anteriores",
            1,
        )
    elif posicao >= 3 and "avaliar" not in texto.lower()[:80]:
        texto = texto.replace(
            "Promover discussão inicial",
            "Avaliar, por meio de discussão, a compreensão acumulada",
            1,
        )

    return texto
