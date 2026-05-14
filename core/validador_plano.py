"""
Validador pedagógico expandido para planos de aula.

Valida não apenas tema e metodologia, mas também acompanhamento,
acessibilidade, aprendizagem, e detecta repetições e inconsistências.
"""

import re


def validar_aulas_geradas(aulas) -> list[str]:
    """
    Valida a qualidade pedagógica das aulas geradas.

    Retorna lista de problemas encontrados (vazia = sem problemas).
    """
    problemas = []
    if not aulas:
        return ["Nenhuma aula foi gerada."]

    temas_vistos = set()

    for idx, aula in enumerate(aulas, start=1):
        tema = str(aula.get("tema", "")).strip()

        # ── Validação de tema ──────────────────────────────────────────
        if not tema:
            problemas.append(f"Aula {idx}: tema não identificado.")

        # Tema repetido (exato)
        if tema and tema in temas_vistos:
            problemas.append(
                f"Aula {idx}: tema '{tema}' repetido de aula anterior. "
                "Considere diferenciar com subtema ou continuidade."
            )
        temas_vistos.add(tema)

        # ── Validação de metodologia ───────────────────────────────────
        metodologia = aula.get("metodologia") or []
        if not metodologia:
            problemas.append(f"Aula {idx}: metodologia vazia.")
            continue

        primeiro = metodologia[0]
        texto_primeiro = primeiro.get("texto", "") if isinstance(primeiro, dict) else str(primeiro)
        if len(texto_primeiro.strip()) < 40:
            problemas.append(f"Aula {idx}: desenvolvimento muito curto.")

        # Verifica se tem etapas mínimas
        titulos = set()
        for item in metodologia:
            if isinstance(item, dict):
                titulo = (item.get("titulo") or "").strip().lower()
                titulo = re.sub(r"[^a-záàâãéêíóôõúç\s]", "", titulo).strip()
                titulos.add(titulo)

        # Pelo menos 3 etapas para ser considerado um plano válido
        if len(titulos) < 3 and len(metodologia) < 3:
            problemas.append(
                f"Aula {idx}: metodologia com poucas etapas ({len(titulos)}). "
                "Um plano completo deve ter pelo menos 3 etapas."
            )

        # ── Validação de aprendizagem ──────────────────────────────────
        aprendizagem = str(aula.get("aprendizagem", "")).strip()
        if not aprendizagem:
            problemas.append(f"Aula {idx}: campo de aprendizagem vazio.")
        elif len(aprendizagem) < 20:
            problemas.append(f"Aula {idx}: aprendizagem muito curta ({len(aprendizagem)} chars).")

        # ── Validação de acompanhamento ────────────────────────────────
        acompanhamento = aula.get("acompanhamento") or []
        if not acompanhamento:
            problemas.append(f"Aula {idx}: acompanhamento da aprendizagem vazio.")
        elif isinstance(acompanhamento, list):
            itens_validos = [item for item in acompanhamento if str(item).strip()]
            if len(itens_validos) < 2:
                problemas.append(
                    f"Aula {idx}: acompanhamento com poucos itens ({len(itens_validos)}). "
                    "Recomendado pelo menos 3."
                )

        # ── Validação de acessibilidade ────────────────────────────────
        acessibilidade = aula.get("acessibilidade") or []
        if not acessibilidade:
            problemas.append(f"Aula {idx}: acessibilidade vazia.")
        elif isinstance(acessibilidade, list):
            itens_validos = [item for item in acessibilidade if str(item).strip()]
            if len(itens_validos) < 2:
                problemas.append(
                    f"Aula {idx}: acessibilidade com poucos itens ({len(itens_validos)}). "
                    "Recomendado pelo menos 3."
                )

    return problemas
