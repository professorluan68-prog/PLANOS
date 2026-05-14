from collections.abc import Iterable


def horario_para_plano(horario) -> str:
    if isinstance(horario, tuple) and len(horario) >= 2:
        return f"{horario[0]}\n{horario[1]}"
    return str(horario or "")


def texto_lista(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, Iterable) and not isinstance(valor, (bytes, bytearray, dict)):
        return "\n".join(f"- {item}" for item in valor if str(item).strip())
    return str(valor)


def montar_relatorio_geracao(aulas, disciplina: str, turma: str, bimestre: str, mes: str) -> str:
    linhas = [
        "RELATORIO DE CONFERENCIA DO PLANO",
        f"Disciplina: {disciplina}",
        f"Turma: {turma}",
        f"Bimestre: {bimestre}",
        f"Mes: {mes}",
        f"Total de aulas: {len(aulas or [])}",
        "",
    ]
    for idx, aula in enumerate(aulas or [], start=1):
        linhas.extend(
            [
                f"Aula {idx}",
                f"Tema: {aula.get('tema', '')}",
                f"Data: {aula.get('data', '')}",
                f"Horario: {str(aula.get('horario', '')).replace(chr(10), ' - ')}",
                f"IA usada: {'sim' if aula.get('ia_usada') else 'nao'}",
                "",
            ]
        )
    return "\n".join(linhas)

