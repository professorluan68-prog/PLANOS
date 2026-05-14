import os
import re
import unicodedata
import hashlib
from pathlib import Path

import pdfplumber

from config import PDF_TEXTO_LIMITE_CHARS
from core.avaliacao import gerar_acessibilidade_dinamica, gerar_acompanhamento_dinamico
from divisor_metodologia import processar_pdf_e_dividir_metodologia


def _limpar_linhas(texto: str) -> list[str]:
    linhas = []
    for linha in (texto or "").splitlines():
        linha = re.sub(r"\s+", " ", linha).strip()
        if linha:
            linhas.append(linha)
    return linhas


def _extrair_texto_pdf(caminho_pdf: str) -> str:
    partes = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            partes.append(pagina.extract_text() or "")
            if sum(len(p) for p in partes) >= PDF_TEXTO_LIMITE_CHARS:
                break
    return "\n".join(partes)[:PDF_TEXTO_LIMITE_CHARS]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _limpar_titulo_material(linha: str, disciplina: str) -> str:
    titulo = re.sub(r"\s+", " ", linha or "").strip(" -–—:")
    disciplina_norm = _normalizar(disciplina)
    titulo_norm = _normalizar(titulo)

    if titulo_norm == disciplina_norm:
        return ""

    if disciplina_norm and titulo_norm.startswith(disciplina_norm):
        titulo = titulo[len(disciplina):].strip(" -–—:")

    titulo = re.sub(r"\s+(?:[1-4][º°oªa]?)\s*bimestre\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+ensino\s+(?:fundamental|m[eé]dio)\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+anos?\s+(?:iniciais|finais)\b.*$", "", titulo, flags=re.I)
    return titulo.strip(" -–—:")


def _linha_generica(linha: str, disciplina: str) -> bool:
    texto = _normalizar(linha)
    disciplina_norm = _normalizar(disciplina)
    genericas = {
        "",
        disciplina_norm,
        "ensino fundamental",
        "ensino medio",
        "anos iniciais",
        "anos finais",
        "material digital",
        "aula digital",
    }
    if texto in genericas:
        return True
    return bool(re.fullmatch(r"(?:[1-4][oº°]?\s*)?bimestre", texto))


def _linhas_relevantes(texto: str, disciplina: str, tema: str) -> list[str]:
    relevantes = []
    vistos = set()
    for linha in _limpar_linhas(texto):
        linha = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(linha)
        if not linha or normalizada in vistos:
            continue
        if _linha_generica(linha, disciplina) or _normalizar(tema) == normalizada:
            continue
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
            continue
        vistos.add(normalizada)
        relevantes.append(linha)
    return relevantes


def _extrair_titulo_multilinha(texto: str, disciplina: str) -> str:
    linhas = _limpar_linhas(texto)
    partes = []
    for linha in linhas[:8]:
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(titulo)
        if not titulo or _linha_generica(titulo, disciplina) or normalizada == _normalizar(disciplina):
            continue
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        partes.append(titulo)
        if len(partes) >= 2:
            break

    if not partes:
        return ""

    if len(partes) == 1:
        return _limpar_titulo_material(partes[0], disciplina)

    primeira = partes[0].rstrip(" -:")
    if primeira.lower().endswith((" de", " da", " do", " das", " dos", " e")) or len(primeira) <= 28:
        return _limpar_titulo_material(f"{primeira} {partes[1].lstrip('-: ')}".strip(), disciplina)
    return _limpar_titulo_material(primeira, disciplina)


def _contem(base: str, termos: list[str]) -> bool:
    return any(termo in base for termo in termos)


def _detectar_tecnicas_matematica(texto: str, tema: str) -> set[str]:
    base = _normalizar(f"{tema} {texto}")
    tecnicas = set()
    mapa = {
        "virem_conversem": ["virem e conversem"],
        "todo_mundo_escreve": ["todo mundo escreve"],
        "com_suas_palavras": ["com suas palavras"],
        "hora_leitura": ["hora da leitura"],
        "de_olho_modelo": ["de olho no modelo"],
        "relembre": ["relembre"],
        "geogebra": ["geogebra"],
        "calculadora": ["calculadora"],
        "arvore_possibilidades": ["arvore de possibilidades", "árvore de possibilidades"],
        "mapa_mental": ["mapa mental"],
        "resolucao_etapas": ["compreender", "planejar", "executar", "verificar"],
    }
    for tecnica, termos in mapa.items():
        if _contem(base, termos):
            tecnicas.add(tecnica)
    return tecnicas


def _linhas_secao_matematica(texto: str, marcador: str) -> list[str]:
    marcadores = {
        "para comecar",
        "relembre",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "encerramento",
    }
    linhas = _limpar_linhas(texto)
    alvo = _normalizar(marcador)
    inicio = None

    for indice, linha in enumerate(linhas):
        if _normalizar(linha) == alvo:
            inicio = indice + 1
            break

    if inicio is None:
        return []

    ignorar = {
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "veja no livro!",
        "resolucao",
        "fica a dica",
        "conversando sobre o tema",
        "planejando fica mais facil",
    }

    coletadas = []
    for linha in linhas[inicio:]:
        normalizada = _normalizar(linha)
        if normalizada in marcadores:
            break
        if normalizada in ignorar:
            continue
        if re.fullmatch(r"\d+\s*minutos?", normalizada):
            continue
        if "freepik" in normalizada or "pixabay" in normalizada or "disponivel em:" in normalizada:
            continue
        coletadas.append(linha)
    return coletadas


def _tem_secao_matematica(texto: str, marcador: str) -> bool:
    alvo = _normalizar(marcador)
    return any(_normalizar(linha) == alvo for linha in _limpar_linhas(texto))


def _primeira_secao_matematica(texto: str) -> str:
    secoes = ["relembre", "para comecar", "exploracao", "foco no conteudo", "na pratica", "encerramento"]
    melhor_indice = None
    melhor_secao = ""
    for indice, linha in enumerate(_limpar_linhas(texto)):
        normalizada = _normalizar(linha)
        if normalizada in secoes and (melhor_indice is None or indice < melhor_indice):
            melhor_indice = indice
            melhor_secao = normalizada
    return melhor_secao


def _contar_atividades_matematica(texto: str) -> int:
    return len(set(re.findall(r"atividade\s*(\d+)", _normalizar(texto), flags=re.I)))


def _detectar_formato_aula_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    primeira_secao = _primeira_secao_matematica(texto)
    tem_pause = _tem_secao_matematica(texto, "pause e responda")
    tem_foco = _tem_secao_matematica(texto, "foco no conteudo")
    total_atividades = _contar_atividades_matematica(texto)

    if "aula de verificacao" in base or re.search(r"\bverificacao\b", _normalizar(tema)):
        return "verificacao"
    if primeira_secao == "relembre" and not tem_foco:
        return "verificacao"
    if primeira_secao == "na pratica" and total_atividades >= 2 and not tem_foco and not tem_pause:
        return "pratica_intensiva"
    if _contem(base, ["modelagem", "polya", "hora da leitura", "de olho no modelo", "um passo de cada vez"]):
        return "modelagem"
    if _contem(_normalizar(tema), ["retomando"]) or _contem(base, ["retomar os conceitos", "retomar os conceitos de"]):
        return "retomada"
    return "conceito_novo"


def _resumo_contexto_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "a situação de Marta, que quer comprar um celular de R$ 3.800,00 e precisa planejar quanto economizar por mês"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "a comparação entre os custos de um carro elétrico e de um carro híbrido, considerando gasto por quilômetro e manutenção anual"
    if "josue" in base and "salada de frutas" in base:
        return "as situações-problema sobre compra de frutas, lucro de vendedores, tempos de viagem e descontos progressivos"
    if "internet discada" in base and "banda larga" in base:
        return "a comparação entre internet discada e banda larga para analisar tempo de download e razão entre grandezas"
    if "construcao civil" in base and "agua" in base and "concreto" in base:
        return "o consumo de água na construção civil para relacionar volume de concreto e quantidade de água utilizada"

    linhas = _linhas_secao_matematica(texto, "para comecar") or _linhas_secao_matematica(texto, "na pratica")
    if linhas:
        linhas_contexto = []
        for linha in linhas:
            if _linha_com_marcador_metodologico(linha):
                continue
            linha_limpa = _limpar_linha_metodologica(linha)
            if _linha_instrucao_matematica(linha_limpa):
                continue
            linhas_contexto.append(linha_limpa)
            if len(linhas_contexto) >= 3:
                break
        resumo = re.sub(r"\s+", " ", " ".join(linhas_contexto)).strip()
        if resumo:
            return resumo[:220].rstrip(" .")
    return tema


def _resumo_pratica_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "josue" in base and "bia" in base and "bruna" in base:
        return "situações sobre compra de frutas, lucro de vendedores online, tempos de viagem e descontos progressivos"
    if "idade de ana" in base or "triplo da minha idade" in base:
        return "situações sobre idade, distribuição de estudantes e equações do 1º grau"
    if "carro eletrico" in base and "concessionaria" in base:
        return "atividades progressivas de modelagem algébrica em contextos de veículos, produção e investimento"
    if "internet discada" in base and "banda larga" in base:
        return "situações de comparação entre velocidades, tamanhos de arquivo e relações entre grandezas"
    if "construcao civil" in base and "agua" in base:
        return "situações de leitura de tabelas, construção de pares ordenados e representação gráfica entre grandezas"

    if _contar_atividades_matematica(texto) >= 2:
        return "atividades progressivas de resolução, registro e verificação das respostas"
    return f"problemas e registros relacionados a {tema}"


def _pergunta_pause_matematica(texto: str) -> str:
    linhas = _linhas_secao_matematica(texto, "pause e responda")
    if not linhas:
        return ""
    bloco = re.sub(r"\s+", " ", " ".join(linhas)).strip()
    if "idade de ana" in _normalizar(bloco):
        return "O triplo da idade de Ana, aumentado em 6 anos, totaliza 108 anos. Solicitar que os estudantes escrevam a equacao que modela essa situacao."
    citacao = re.search(r"falou:\s*[\"“]?([^\"”]{25,220})", bloco, flags=re.I)
    if citacao:
        return citacao.group(1).strip(" .")
    if ":" in bloco:
        apos_dois_pontos = bloco.split(":", 1)[1].strip(" \"")
        if len(apos_dois_pontos) >= 25:
            return apos_dois_pontos[:220].rstrip(" .")
    for trecho in re.findall(r"[^?]{25,220}\?", bloco):
        trecho_limpo = trecho.strip(" \"")
        if len(trecho_limpo) >= 30:
            return trecho_limpo
    return bloco[:220].rstrip(" .")


def _fechamento_reflexivo_matematica(texto: str, tema: str, formato: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "retomar o significado de incógnita, solução e verificação, conectando a resposta final à meta financeira de Marta"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "sistematizar as quatro etapas de Polya e discutir quando uma equação do 1º grau é um bom modelo matemático para a situação"
    if "josue" in base and "bruna" in base:
        return "destacar que o valor da incógnita nem sempre é a resposta final e reforçar a importância de verificar cada solução no contexto"
    if "internet discada" in base and "banda larga" in base:
        return "retomar como razão entre grandezas de espécies diferentes ajuda a interpretar tempo, velocidade e unidades de medida"
    if "construcao civil" in base and "agua" in base:
        return "sintetizar como a relação entre grandezas pode ser representada por tabela e gráfico, conectando a leitura matemática ao contexto ambiental"
    if formato == "pratica_intensiva":
        return "retomar os caminhos de resolução usados pela turma e reforçar a importância de verificar se o resultado encontrado faz sentido no problema"
    return f"sistematizar as estratégias construídas pela turma para compreender e resolver situações relacionadas a {tema}"


def _aprendizagem_matematica(tema: str, tipo: str, texto: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "Retomar e aplicar equações do 1º grau para modelar situações do cotidiano, identificar a incógnita, resolver por operações inversas e verificar a solução encontrada."
    if tipo == "modelagem":
        return "Modelar situações-problema utilizando equações do 1º grau, aplicando estratégias de resolução, interpretação do enunciado e verificação do resultado no contexto."
    if tipo == "funcoes":
        return "Identificar relações de dependência entre grandezas e representá-las por tabelas, expressões e gráficos, interpretando o comportamento da função no contexto analisado."
    if tipo == "grandezas_medidas":
        return "Compreender e comparar relações entre grandezas de espécies diferentes, analisando razões, unidades e proporcionalidade em situações-problema."
    if tipo == "estatistica_probabilidade":
        return "Ler, organizar e interpretar dados, tabelas e gráficos para justificar conclusões e resolver situações que envolvam análise de informações."
    if tipo == "algebra":
        return "Resolver e interpretar situações-problema por meio de equações do 1º grau, identificando incógnitas, organizando procedimentos e verificando a coerência das soluções."
    return f"Compreender e aplicar conceitos relacionados a {tema}."


def _perfil_disciplina(disciplina: str) -> str:
    base = _normalizar(disciplina)
    if _contem(base, ["orientacao de estudos", "orientacao estudos", "orienestudos", "orient"]):
        return "orientacao_estudos"
    if _contem(base, ["redacao e leitura", "leitura e redacao", "redacao", "leitura"]):
        return "leitura_redacao"
    if _contem(base, ["lingua portuguesa", "portugues"]):
        if _contem(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"
    if _contem(base, ["ciencias", "cienc"]):
        return "ciencias_ef"
    if _contem(base, ["biologia", "biolog"]):
        return "biologia"
    if _contem(base, ["quimica", "quim"]):
        return "quimica"
    if _contem(base, ["fisica", "fis"]):
        return "fisica"
    if _contem(base, ["historia", "histor"]):
        return "historia"
    if _contem(base, ["geografia", "geograf"]):
        return "geografia"
    if _contem(base, ["ingles", "lingua inglesa", "ingl"]):
        return "ingles"
    if _contem(base, ["arte"]):
        return "arte"
    if _contem(base, ["projeto de vida", "projeto"]):
        return "projeto_de_vida"
    if _contem(base, ["educacao financeira", "financeir"]):
        return "educacao_financeira"
    if _contem(base, ["matematica", "matem"]):
        return "matematica"
    if _contem(base, ["tecnologia", "inovacao", "tecnolog"]):
        return "tecnologia_inovacao"
    if _contem(base, ["sociologia", "sociolog"]):
        return "sociologia"
    if _contem(base, ["lideranca", "oratoria", "lideranc", "orator"]):
        return "lideranca_oratoria"
    return "geral"


def _detectar_tipo_aula(texto: str, tema: str, disciplina: str = "") -> str:
    base = _normalizar(f"{disciplina} {tema} {texto}")
    perfil = _perfil_disciplina(disciplina)

    if perfil == "educacao_financeira":
        if _contem(base, ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]):
            return "credito_endividamento"
        if _contem(base, ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]):
            return "empreendedorismo"
        if _contem(base, ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]):
            return "cidadania_financeira"
        if _contem(base, ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]):
            return "instituicoes_financeiras"
        if _contem(base, ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]):
            return "investimento_poupanca"
        if _contem(base, ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]):
            return "orcamento_planejamento"
        if _contem(base, ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]):
            return "consumo_consciente"
        return "decisao_financeira"

    if perfil == "matematica":
        tema_base = _normalizar(tema)
        if _contem(
            base,
            [
                "modelagem",
                "modelar situacoes",
                "modelar situacoes-problema",
                "metodo de polya",
                "polya",
                "representar matematicamente",
                "sentenca matematica",
            ],
        ):
            return "modelagem"
        if _contem(tema_base, ["grandeza", "razao", "proporcao"]):
            return "grandezas_medidas"
        if _contem(base, ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]):
            return "algebra"
        if _contem(base, ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]):
            return "funcoes"
        if _contem(base, ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha"]):
            return "combinatoria"
        if _contem(base, ["grandeza", "razao", "proporcao", "velocidade media", "mbps", "kbps"]):
            return "grandezas_medidas"
        if _contem(base, ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "frequencia", "censo", "pesquisa"]):
            return "estatistica_probabilidade"
        if _contem(base, ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]):
            return "geometria"
        if _contem(base, ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]):
            return "numeros_operacoes"
        return "resolucao_problemas"

    if _contem(base, ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]):
        return "producao"
    if _contem(base, ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]):
        return "argumentacao"
    if _contem(base, ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]):
        return "fonte_historica"
    if _contem(base, ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]):
        return "analise_geografica"
    if _contem(base, ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]):
        return "investigacao"
    if _contem(base, ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]):
        return "resolucao_problemas"
    if _contem(base, ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue"]):
        return "lingua_estrangeira"
    if _contem(base, ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]):
        return "arte_pratica"
    if _contem(base, ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]):
        return "reflexiva"
    if _contem(
        base,
        [
            "leitura",
            "leia",
            "texto",
            "interpreta",
            "genero textual",
            "conto",
            "cronica",
            "anuncio",
            "publicidade",
            "publicitario",
            "slogan",
            "observe",
        ],
    ):
        return "leitura"
    return "geral"


def _conceito_principal(linhas: list[str], tema: str) -> str:
    marcadores_ignorar = {
        "para comecar",
        "contextualizacao",
        "leitura analitica",
        "leitura e construcao do conteudo",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "revisao e reescrita",
        "relembre",
        "encerramento",
        "sistematizacao",
        "todo mundo escreve",
        "virem e conversem",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "listen and repeat",
        "write and share",
        "say it in english",
    }
    candidatos = []
    for linha in linhas[:12]:
        normalizada = _normalizar(linha)
        if normalizada in marcadores_ignorar:
            continue
        if _linha_com_marcador_metodologico(linha):
            continue
        linha_limpa = _limpar_linha_metodologica(linha)
        if not linha_limpa:
            continue
        if _linha_instrucao_matematica(linha_limpa):
            continue
        if 8 <= len(linha_limpa) <= 120:
            candidatos.append(linha_limpa)
    return candidatos[0] if candidatos else tema


def _linha_com_marcador_metodologico(linha: str) -> bool:
    normalizada = _normalizar(linha)
    marcadores = [
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "para comecar",
        "foco no conteudo",
        "na pratica",
        "encerramento",
    ]
    quantidade = sum(1 for marcador in marcadores if marcador in normalizada)
    if quantidade >= 2:
        return True
    return any(normalizada.startswith(marcador) for marcador in marcadores)


def _limpar_linha_metodologica(linha: str) -> str:
    limpa = re.sub(r"\s+", " ", str(linha or "")).strip(" -:;•\t")
    padroes = [
        r"\bVIREM\s+E\s+CONVERSEM\b",
        r"\bTODO\s+MUNDO\s+ESCREVE\b",
        r"\bCOM\s+SUAS\s+PALAVRAS\b",
        r"\bHORA\s+DA\s+LEITURA\b",
        r"\bDE\s+OLHO\s+NO\s+MODELO\b",
        r"\bUM\s+PASSO\s+DE\s+CADA\s+VEZ\b",
    ]
    for padrao in padroes:
        limpa = re.sub(padrao, "", limpa, flags=re.I)
    limpa = re.sub(r"\s+", " ", limpa).strip(" -:;•\t")
    return limpa


def _linha_instrucao_matematica(linha: str) -> bool:
    normalizada = _normalizar(linha)
    inicios_instrucao = (
        "resolva",
        "calcule",
        "determine",
        "registre",
        "complete",
        "observe",
        "assinale",
        "responda",
        "explique",
        "justifique",
        "copie",
        "escreva",
        "analise",
    )
    return normalizada.startswith(inicios_instrucao)


def _perguntas_orientadoras(tipo: str, tema: str, conceito: str) -> str:
    perguntas = {
        "algebra": [
            "Quais grandezas estao envolvidas na situacao?",
            "Como representar matematicamente essa relacao?",
            "O resultado encontrado faz sentido no contexto?",
        ],
        "funcoes": [
            "Que relacao de dependencia existe entre as grandezas?",
            "Como a tabela e o grafico representam essa variacao?",
            "O comportamento e crescente ou decrescente? Por quê?",
        ],
        "geometria": [
            "Que propriedades da figura ajudam na resolucao?",
            "Que medidas precisam ser observadas ou calculadas?",
            "Como justificar o procedimento utilizado?",
        ],
        "grandezas_medidas": [
            "Quais sao as grandezas envolvidas e suas unidades?",
            "A relacao e direta ou inversamente proporcional?",
            "Como interpretar o valor obtido no contexto?",
        ],
        "estatistica_probabilidade": [
            "Que dados ou eventos precisam ser analisados?",
            "Como organizar essas informacoes para interpretar melhor?",
            "O resultado pode ser expresso em fracao, decimal e porcentagem?",
        ],
        "combinatoria": [
            "A ordem dos elementos importa nesta situacao?",
            "Como listar ou contar os casos possiveis de modo organizado?",
            "O total encontrado faz sentido no contexto?",
        ],
        "modelagem": [
            "Que grandezas e relacoes aparecem na situacao?",
            "Como traduzir o problema para linguagem matematica?",
            "Como interpretar a resposta no contexto original?",
        ],
        "verificacao": [
            "Que conceito ou procedimento precisa ser retomado?",
            "Qual estrategia e mais adequada para resolver cada item?",
            "Como verificar se a resposta final esta coerente?",
        ],
        "leitura": [
            f"O que o titulo {tema} antecipa sobre o texto?",
            "Quais informacoes ajudam a compreender a finalidade do material?",
            "Que pistas do texto ou da imagem justificam as respostas?",
        ],
        "argumentacao": [
            "Qual opiniao ou ponto de vista aparece no material?",
            "Que argumentos sustentam essa ideia?",
            "Que recursos tornam a mensagem mais convincente?",
        ],
        "producao": [
            "Para quem o texto sera escrito?",
            "Qual finalidade deve orientar a producao?",
            "Que criterios precisam ser observados na revisao?",
        ],
        "investigacao": [
            "Que fenomeno ou problema esta sendo investigado?",
            "Quais evidencias aparecem no material?",
            "Como podemos explicar o processo com nossas palavras?",
        ],
        "fonte_historica": [
            "Quem produziu essa fonte e em que contexto?",
            "Que informacoes ela revela sobre o periodo estudado?",
            "Que relacao podemos fazer com o presente?",
        ],
        "analise_geografica": [
            "Que elementos da paisagem, mapa ou grafico precisam ser observados?",
            "Que relacoes existem entre espaco, sociedade e natureza?",
            "Que exemplos do cotidiano ajudam a entender o tema?",
        ],
        "resolucao_problemas": [
            "Quais dados o problema apresenta?",
            "Que estrategia de resolucao pode ser usada?",
            "Como verificar se o resultado faz sentido?",
        ],
        "lingua_estrangeira": [
            "Quais palavras ou expressoes ja conhecemos?",
            "Em que situacao real podemos usar esse vocabulario?",
            "Como pronunciar e empregar as estruturas trabalhadas?",
        ],
        "arte_pratica": [
            "Que sensacoes, ideias ou referencias a obra/material provoca?",
            "Que elementos visuais, sonoros ou corporais podemos perceber?",
            "Como transformar essa observacao em criacao ou registro?",
        ],
        "reflexiva": [
            "Como esse tema aparece na vida escolar ou pessoal?",
            "Que escolhas ou atitudes podem ser observadas nessa situacao?",
            "Que compromisso simples pode ser assumido a partir da aula?",
        ],
    }
    escolhidas = perguntas.get(tipo) or [
        f"O que ja sabemos sobre {tema}?",
        f"Quais ideias principais aparecem em {conceito}?",
        "Como registrar e aplicar o que foi discutido?",
    ]
    return "Perguntas orientadoras: " + " ".join(f"- {p}" for p in escolhidas)


def _tecnica_por_perfil(perfil: str) -> dict[str, str]:
    tecnicas = {
        "lingua_portuguesa_ef": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa_em": {
            "discussao": "DEBATE ORIENTADO",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "leitura_redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao_estudos": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "ciencias_ef": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "biologia": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "quimica": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM PROCEDIMENTOS E RESULTADOS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "fisica": {
            "discussao": "OBSERVEM E LEVANTEM HIPOTESES",
            "registro": "REGISTREM MEDIDAS E RELACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "historia": {
            "discussao": "ANALISEM AS FONTES",
            "registro": "REGISTREM A CRONOLOGIA",
            "sintese": "COM SUAS PALAVRAS",
        },
        "geografia": {
            "discussao": "OBSERVEM O MAPA/IMAGEM",
            "registro": "REGISTREM AS RELACOES ESPACIAIS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "ingles": {
            "discussao": "LISTEN AND REPEAT",
            "registro": "WRITE AND SHARE",
            "sintese": "SAY IT IN ENGLISH",
        },
        "arte": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "REGISTRO NO DIARIO DE BORDO",
            "sintese": "APRECIACAO COMPARTILHADA",
        },
        "projeto_de_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
        "educacao_financeira": {
            "discussao": "analise orientada de caso",
            "registro": "registro de calculos, criterios e decisoes",
            "sintese": "planejamento de aplicacao",
        },
        "matematica": {
            "discussao": "uma conversa em duplas",
            "registro": "um registro individual no caderno",
            "sintese": "síntese com as próprias palavras",
        },
        "tecnologia_inovacao": {
            "discussao": "PENSEM EM SOLUCOES",
            "registro": "REGISTREM O PROTOTIPO OU ALGORITMO",
            "sintese": "APRESENTEM A SOLUCAO",
        },
        "sociologia": {
            "discussao": "DEBATAM O FENOMENO SOCIAL",
            "registro": "REGISTREM ARGUMENTOS E EVIDENCIAS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lideranca_oratoria": {
            "discussao": "PRATIQUEM EM DUPLAS OU GRUPOS",
            "registro": "REGISTREM FEEDBACKS E AVANCOS",
            "sintese": "AUTOAVALIACAO BREVE",
        },
        "ciencias": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "projeto_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
    }
    return tecnicas.get(perfil, tecnicas["lingua_portuguesa_ef"])


def _frases_por_contexto(perfil: str, tipo: str, tema: str, conceito: str, turma: str, texto_base: str = "") -> dict[str, str]:
    tecnicas = _tecnica_por_perfil(perfil)
    tecnicas_pdf = _detectar_tecnicas_matematica(texto=texto_base, tema=tema) if perfil == "matematica" else set()

    base = {
        "para_comecar": (
            f"Retomar conhecimentos previos da turma sobre {tema}. Propor {tecnicas['discussao']} "
            "para levantar hipoteses, exemplos e duvidas iniciais."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informacoes relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situacoes do cotidiano, repertorios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteudo e relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analitica do texto, imagem, dado ou situacao apresentada, destacando escolhas de "
            "linguagem, organizacao das ideias, pistas visuais e informacoes que sustentam a compreensao."
        ),
        "exploracao": (
            "Estimular os estudantes a levantar estrategias, testar caminhos e comparar representacoes antes da "
            "sistematizacao, valorizando diferentes formas de pensar e justificar o raciocinio."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteudo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relacoes entre conceito, exemplo e atividade."
        ),
        "formalizacao": (
            "Sistematizar no quadro os conceitos, propriedades, procedimentos e registros essenciais da aula, "
            "nomeando cada etapa da resolucao e retomando criterios para validar as respostas."
        ),
        "pratica": (
            f"Orientar a resolucao das atividades propostas, usando {tecnicas['registro']} para garantir registro "
            "individual. Circular pela sala, mediar duvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            "Socializar algumas respostas e realizar correcao dialogada, retomando trechos do material, registros "
            "dos estudantes e duvidas comuns antes de avancar."
        ),
        "encerramento": (
            f"Finalizar com {tecnicas['sintese']}, retomando os aprendizados sobre {tema} e registrando uma sintese "
            "curta no quadro ou no caderno."
        ),
    }

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de producao e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, genero textual e criterios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as caracteristicas do genero relacionado a {tema}, observando estrutura, linguagem, "
                "organizacao das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                "Orientar o planejamento, a escrita do rascunho e a revisao. Solicitar que os estudantes confiram "
                "se o texto atende a finalidade, ao publico e aos criterios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opiniao, argumentos e estrategias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando genero, finalidade, publico-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensao."
            )

    elif perfil == "orientacao_estudos" or perfil == "orientacao":
        base["foco"] = (
            f"Trabalhar {conceito} como oportunidade para ensinar uma estrategia de estudo: localizar informacoes, "
            "interpretar comandos, justificar respostas e revisar registros."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades explicitando o passo a passo de estudo: ler o comando, marcar "
            "palavras-chave, buscar evidencias, responder e revisar a resposta."
        )
        base["encerramento"] = (
            f"Finalizar com autoavaliacao breve sobre qual estrategia ajudou mais a compreender {tema} e como ela "
            "pode ser usada em outras disciplinas."
        )

    elif perfil in {"ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        base["para_comecar"] = (
            f"Contextualizar {tema} com uma situacao-problema, imagem, dado ou exemplo do cotidiano. Propor "
            f"{tecnicas['discussao']} para que os estudantes antecipem explicacoes e levantem evidencias."
        )
        base["foco"] = (
            f"Explicar {conceito} de forma progressiva, relacionando fenomeno, causa, consequencia e exemplos. "
            "Usar esquemas no quadro para diferenciar observacao, hipotese e conceito cientifico."
        )
        base["pratica"] = (
            f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {tecnicas['registro']}. "
            "Retomar as evidencias usadas pelos estudantes para justificar as respostas."
        )

    elif perfil == "historia":
        base["foco"] = (
            f"Apresentar o contexto historico de {conceito}, situando sujeitos, tempo, espaco e conflitos envolvidos. "
            "Relacionar as ideias iniciais da turma com os conceitos historicos em estudo."
        )
        base["pratica"] = (
            "Orientar a analise de fontes, imagens, mapas, linhas do tempo ou textos do material. Solicitar registro "
            "das evidencias encontradas e mediacao para diferenciar fato, interpretacao e contexto."
        )

    elif perfil == "geografia":
        base["foco"] = (
            f"Analisar {conceito} considerando paisagem, territorio, escala, localizacao e relacoes entre sociedade "
            "e natureza. Usar mapa, imagem, tabela ou grafico como apoio para a explicacao."
        )
        base["pratica"] = (
            "Orientar leitura de mapas, imagens, graficos ou situacoes-problema, solicitando que os estudantes "
            "identifiquem elementos espaciais e expliquem relacoes de causa e consequencia."
        )

    elif perfil == "ingles":
        base["para_comecar"] = (
            f"Retomar vocabulario conhecido relacionado a {tema} com repeticao oral breve e exemplos no quadro. "
            "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematizacao."
        )
        base["leitura"] = (
            "Apresentar o texto, dialogo, imagem ou situacao comunicativa, alternando leitura em voz alta, escuta "
            "e repeticao. Destacar vocabulario-chave e estruturas em ingles com apoio em exemplos."
        )
        base["foco"] = (
            f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressoes estudadas. "
            "Registrar no quadro exemplos curtos em ingles e seus sentidos em contexto."
        )
        base["pratica"] = (
            "Organizar pratica oral e escrita em pares, com repeticao, preenchimento, pequenas respostas ou dialogos. "
            "Acompanhar pronuncia, compreensao e uso funcional das expressoes."
        )

    elif perfil == "arte":
        base["foco"] = (
            f"Apresentar referencias artisticas relacionadas a {conceito}, orientando apreciacao de elementos visuais, "
            "sonoros, corporais ou culturais. Valorizar percepcoes diferentes sem reduzir a aula a explicacao teorica."
        )
        base["pratica"] = (
            "Propor experimentacao, criacao ou apreciacao orientada, com registro no diario de bordo. Acompanhar "
            "processos criativos, escolhas dos estudantes e socializacao das producoes ou percepcoes."
        )

    elif perfil == "projeto_de_vida" or perfil == "projeto_vida":
        base["para_comecar"] = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
        )
        base["foco"] = (
            f"Construir o conceito de {conceito} por meio de exemplos escolares e cotidianos, ajudando a turma a "
            "relacionar sentir, pensar e agir de forma respeitosa."
        )
        base["pratica"] = (
            "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
            "que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        )
        base["encerramento"] = (
            f"Encerrar com um compromisso simples ou observacao para a semana, relacionado a {tema}, reforcando "
            "autonomia, respeito e cuidado nas relacoes."
        )

    elif perfil == "educacao_financeira":
        conceito_seguro = tema if _normalizar(conceito) in {"educacao financeira", "financeira"} else conceito

        situacoes = {
            "orcamento_planejamento": "uma situacao de organizacao de renda, gastos e prioridades para cumprir uma meta simples",
            "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preco, durabilidade e impacto da escolha",
            "investimento_poupanca": "uma situacao de poupanca ou reserva de emergencia em que pequenos valores acumulados ajudam a lidar com imprevistos",
            "credito_endividamento": "uma compra parcelada ou oferta de credito em que seja necessario comparar valor a vista, juros, parcelas e custo total",
            "empreendedorismo": "um pequeno projeto de venda, servico ou solucao para a comunidade escolar, analisando custos, preco e viabilidade",
            "cidadania_financeira": "uma situacao de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de servicos financeiros",
            "instituicoes_financeiras": "uma situacao cotidiana sobre onde guardar, movimentar e proteger o dinheiro com seguranca",
        }
        situacao = situacoes.get(tipo, f"uma situacao financeira real relacionada a {tema}")

        base["para_comecar"] = (
            f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre habitos financeiros familiares. "
            "Convidar os estudantes a levantar hipoteses sobre escolhas, riscos, prioridades e consequencias antes da sistematizacao."
        )
        base["analise_caso"] = (
            f"Conduzir a analise do caso ligado a {tema}, identificando dados importantes, alternativas possiveis, "
            "criterios de decisao e consequencias de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
        )
        base["foco"] = (
            f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situacoes reais de consumo, "
            "planejamento, poupanca, credito ou organizacao de recursos. Explicar o vocabulario financeiro necessario e construir criterios claros para a tomada de decisao."
        )
        base["pause"] = (
            "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
            "retomando dados do material e duvidas comuns antes de seguir para a aplicacao."
        )
        base["calculos"] = (
            "Orientar calculos financeiros de forma guiada, destacando dados, operacoes, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
            "Relacionar cada resultado numerico a uma decisao possivel, evitando que a atividade fique apenas mecanica."
        )
        base["planejamento"] = (
            "Orientar a elaboracao ou analise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
            "Acompanhar os registros para que os estudantes expliquem os criterios usados nas escolhas."
        )
        base["simulacao"] = (
            "Organizar uma simulacao financeira ou analise de alternativas, aplicando os criterios construidos na aula para escolher, comparar, planejar ou revisar uma decisao. "
            "Solicitar registro de calculos, justificativas e possiveis consequencias."
        )
        base["projeto"] = (
            "Orientar a organizacao de um projeto empreendedor simples, levantando recursos necessarios, custos, preco, publico, viabilidade e cuidados eticos. "
            "Solicitar que os estudantes justifiquem as decisoes tomadas no planejamento."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparacao de alternativas e justificativa das decisoes. "
            "Retomar vocabulario financeiro e criterios de escolha sempre que surgirem duvidas."
        )

        if tipo == "orcamento_planejamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} como estrategia de organizacao financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                "Construir com a turma criterios para controlar recursos e ajustar escolhas conforme limites e objetivos."
            )
            base["pratica"] = base["planejamento"]
        elif tipo == "consumo_consciente":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} a partir de criterios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-beneficio e impacto da escolha. "
                "Evitar tom moralista e conduzir a analise com base em argumentos, dados e consequencias."
            )
        elif tipo == "investimento_poupanca":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando poupanca, reserva, rendimento, constancia e planejamento de metas. "
                "Mostrar como a organizacao dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "credito_endividamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} com foco no uso responsavel do credito, analisando juros, parcelas, custo total, riscos de endividamento e criterios para decidir. "
                "Comparar alternativas sem estimular consumo, priorizando avaliacao critica e planejamento."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "empreendedorismo":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou servico, custos, preco, lucro e viabilidade. "
                "Relacionar a proposta a planejamento, responsabilidade e analise do contexto."
            )
            base["pratica"] = base["projeto"]
        elif tipo == "cidadania_financeira":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, seguranca, comprovantes, garantias e autonomia nas decisoes financeiras. "
                "Orientar a turma a identificar formas de protecao e uso consciente de servicos financeiros."
            )
        elif tipo == "instituicoes_financeiras":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} explicando a funcao das instituicoes financeiras na guarda, movimentacao, controle e protecao do dinheiro. "
                "Comparar exemplos como banco, conta digital, poupanca e outros servicos, destacando seguranca e planejamento."
            )

        base["encerramento"] = (
            f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando criterios de decisao, organizacao e responsabilidade. "
            "Propor um fechamento com planejamento de aplicacao no cotidiano, sem solicitar exposicao de informacoes financeiras pessoais."
        )

    elif perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        contexto = _resumo_contexto_matematica(texto_base, tema)
        pratica = _resumo_pratica_matematica(texto_base, tema)
        pergunta_pause = _pergunta_pause_matematica(texto_base)
        tecnica_inicio = "uma conversa em duplas" if "virem_conversem" in tecnicas_pdf else "uma discussão coletiva inicial"
        tecnica_registro = "um registro individual no caderno" if "todo_mundo_escreve" in tecnicas_pdf else tecnicas["registro"]

        if formato == "verificacao":
            base["para_comecar"] = (
                f"Retomar com a turma os procedimentos essenciais relacionados a {tema}, recuperando "
                "criterios de resolucao, organizacao dos registros e verificacao das respostas antes das atividades."
            )
        elif formato == "pratica_intensiva":
            base["para_comecar"] = (
                "Retomar brevemente as estrategias discutidas na aula anterior e combinar com a turma como registrar "
                "equacao, resolucao e verificacao em cada situacao proposta."
            )
        else:
            base["para_comecar"] = (
                f"Apresentar {contexto} e propor {tecnica_inicio} para que os estudantes mobilizem conhecimentos "
                "previos, levantem hipoteses e identifiquem o que precisa ser descoberto na situacao."
            )

        if tipo == "algebra":
            base["foco"] = (
                f"Conduzir a construcao de {conceito}, identificando a incognita, organizando os dados do problema e "
                "mostrando como as propriedades da igualdade ajudam a transformar e validar cada passo da resolucao."
            )
        elif tipo == "funcoes":
            base["foco"] = (
                f"Conduzir a leitura de {conceito} articulando tabela, pares ordenados, representacao grafica e "
                "interpretacao da dependencia entre as grandezas envolvidas no contexto estudado."
            )
        elif tipo == "grandezas_medidas":
            base["foco"] = (
                f"Desenvolver {conceito} relacionando unidades, razoes e comparacoes entre grandezas, destacando como "
                "as variacoes do contexto ajudam a construir significado para os calculos."
            )
        elif tipo == "estatistica_probabilidade":
            base["foco"] = (
                f"Desenvolver {conceito} por meio da leitura de dados, tabelas e graficos, orientando a turma a "
                "organizar informacoes, justificar conclusoes e conferir a coerencia das interpretacoes."
            )
        elif tipo == "combinatoria":
            base["foco"] = (
                f"Desenvolver {conceito} discutindo criterios de contagem, verificando se a ordem importa e escolhendo "
                "a estrategia mais adequada antes de iniciar os calculos."
            )
        elif tipo == "modelagem":
            base["foco"] = (
                f"Conduzir a modelagem da situacao apresentada em {tema}, traduzindo os dados para linguagem "
                "matematica, construindo a equacao e interpretando a solucao no contexto original."
            )
        else:
            base["foco"] = (
                f"Explorar {conceito} com exemplos guiados, destacando dados, relacoes, procedimentos e criterios para "
                "verificar se o resultado encontrado faz sentido na situacao estudada."
            )

        if "hora_leitura" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Integrar leitura orientada para explicitar como interpretar o enunciado, selecionar informações "
                "relevantes e planejar o caminho de resolução."
            )
        if "um_passo" in tecnicas_pdf or "um passo de cada vez" in _normalizar(texto_base):
            base["foco"] = (
                base["foco"]
                + " Construir a estratégia de forma gradual, nomeando cada etapa do procedimento."
            )
        if "de_olho_modelo" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Apoiar a explicação com um exemplo resolvido, comentando por que a solução encontrada é válida."
            )

        base["formalizacao"] = ""
        if pergunta_pause:
            base["pause"] = (
                f"Propor a questao do material: {pergunta_pause} Socializar as respostas e realizar correcao "
                "dialogada, retomando as justificativas matematicas construidas pela turma."
            )
        else:
            base["pause"] = (
                "Socializar algumas estrategias, comparar caminhos de resolucao e retomar com a turma os criterios "
                "usados para validar cada resposta."
            )

        if formato == "verificacao":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com atividades de retomada e verificacao, solicitando resolucao "
                "completa, comparacao de estrategias e conferência cuidadosa da coerencia dos resultados."
            )
        elif formato == "pratica_intensiva":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com {pratica}, solicitando que cada estudante registre equacao, "
                "resolucao, justificativa e verificacao da resposta em todas as atividades propostas."
            )
        else:
            base["pratica"] = (
                f"Orientar {tecnica_registro} com {pratica}, acompanhando a interpretacao dos enunciados, a "
                "organizacao dos calculos e a validacao das solucoes construidas pela turma."
            )

        fechamento = _fechamento_reflexivo_matematica(texto_base, tema, formato)
        base["encerramento"] = (
            f"Encerrar com {tecnicas['sintese']}, para {fechamento} e registrar uma sintese coletiva do que "
            "foi aprendido na aula."
        )

    elif perfil == "tecnologia_inovacao":
        base["para_comecar"] = (
            f"Apresentar um problema real relacionado a {tema}, incentivando observacao do contexto e levantamento "
            "de necessidades antes da construcao de solucoes."
        )
        base["pratica"] = (
            "Orientar criacao, programacao, prototipagem ou teste de solucao, acompanhando escolhas tecnicas, "
            "iteracoes e registros do processo."
        )

    elif perfil == "sociologia":
        base["para_comecar"] = (
            f"Apresentar um fenomeno social ligado a {tema} por meio de situacao, imagem, dado ou relato, "
            "provocando estranhamento e questionamentos iniciais."
        )
        base["foco"] = (
            f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
            "para superar leituras baseadas apenas no senso comum."
        )

    elif perfil == "lideranca_oratoria":
        base["para_comecar"] = (
            f"Realizar aquecimento vocal, corporal ou mental relacionado a {tema}, criando um ambiente acolhedor "
            "para a pratica de comunicacao e reduzindo a ansiedade de exposicao."
        )
        base["foco"] = (
            f"Apresentar tecnicas e conceitos ligados a {conceito}, demonstrando aplicacoes em fala publica, "
            "argumentacao, escuta ativa ou lideranca colaborativa."
        )
        base["pause"] = (
            "Promover pratica oral breve com feedback positivo sobre avancos observados antes de sugerir ajustes, "
            "fortalecendo confianca e progressao da turma."
        )
        base["pratica"] = (
            "Orientar exercicios, miniapresentacoes, debates ou dinamicas de lideranca de forma progressiva, "
            "sem expor estudantes abruptamente e valorizando preparo, escuta e cooperacao."
        )
        base["encerramento"] = (
            "Encerrar com autoavaliacao breve sobre comunicacao, postura e participacao, registrando um proximo "
            "passo de desenvolvimento para a turma."
        )

    return base


def _etapas_por_perfil(perfil: str, tipo: str, texto_base: str = "", tema: str = "") -> list[tuple[str, str]]:
    if perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        if formato == "verificacao":
            return [
                ("Relembre", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if formato == "pratica_intensiva":
            return [
                ("Para comecar", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]

        etapas = [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
        ]
        if _tem_secao_matematica(texto_base, "pause e responda"):
            etapas.append(("Pause e responda", "pause"))
        etapas.extend(
            [
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        )
        return etapas

    if perfil == "lingua_portuguesa_em":
        return [
            ("Para comecar", "para_comecar"),
            ("Contextualizacao", "contextualizacao"),
            ("Leitura analitica", "leitura_analitica"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "leitura_redacao" and tipo == "producao":
        return [
            ("Para comecar", "para_comecar"),
            ("Leitura e construcao do conteudo", "leitura"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Revisao e reescrita", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        etapas = [
            ("Para comecar", "para_comecar"),
            ("Analise de caso", "analise_caso"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
        ]
        base = _normalizar(f"{texto_base} {tema}")
        if tipo in {"credito_endividamento", "investimento_poupanca"} or _contem(base, ["juros", "porcentagem", "parcela", "rendimento", "calculo"]):
            etapas.append(("Calculos financeiros", "calculos"))
        if tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orcamentario", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na pratica", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    return [
        ("Para comecar", "para_comecar"),
        ("Leitura e construcao do conteudo", "leitura"),
        ("Foco no conteudo", "foco"),
        ("Pause e responda", "pause"),
        ("Na pratica", "pratica"),
        ("Encerramento", "encerramento"),
    ]


def _montar_etapas_metodologia(texto: str, disciplina: str, turma: str, tema: str) -> list[dict]:
    linhas = _linhas_relevantes(texto, disciplina, tema)
    conceito = _conceito_principal(linhas, tema)
    perfil = _perfil_disciplina(disciplina)
    if perfil == "matematica" and _normalizar(conceito) in {"matematica", "matemática"}:
        conceito = tema
    tipo = _detectar_tipo_aula(texto, tema, disciplina)
    frases = _frases_por_contexto(perfil, tipo, tema, conceito, turma, texto)
    etapas = []
    for titulo, chave in _etapas_por_perfil(perfil, tipo, texto, tema):
        texto_etapa = frases.get(chave, "").strip()
        if texto_etapa:
            etapas.append({"titulo": titulo, "texto": texto_etapa})
    return etapas


def _tema_por_texto(texto: str, caminho_pdf: str, disciplina: str) -> str:
    def limpar_prefixo_disciplina(titulo: str) -> str:
        palavras_titulo = str(titulo or "").split()
        palavras_disciplina = str(disciplina or "").split()
        if not palavras_titulo or not palavras_disciplina:
            return str(titulo or "").strip()

        prefixo_titulo = [_normalizar(p) for p in palavras_titulo[: len(palavras_disciplina)]]
        prefixo_disciplina = [_normalizar(p) for p in palavras_disciplina]
        if prefixo_titulo == prefixo_disciplina:
            return " ".join(palavras_titulo[len(palavras_disciplina) :]).strip()

        primeiro_titulo = _normalizar(palavras_titulo[0])
        primeiro_disciplina = _normalizar(palavras_disciplina[0])
        if primeiro_titulo and primeiro_disciplina and primeiro_titulo[:5] == primeiro_disciplina[:5]:
            return " ".join(palavras_titulo[1:]).strip()

        return str(titulo or "").strip()

    linhas = _limpar_linhas(texto)
    candidatos = []
    disciplina_norm = _normalizar(disciplina)
    disciplina_base = disciplina_norm.split()[0] if disciplina_norm else ""
    for linha in linhas[:8]:
        linha_norm = _normalizar(linha)
        if linha_norm == disciplina_norm:
            continue
        if disciplina_base and len(linha.split()) <= max(2, len(str(disciplina or "").split())) and linha_norm.startswith(disciplina_base[:5]):
            continue
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(titulo)
        if len(titulo) < 4 or not titulo:
            continue
        if _linha_generica(titulo, disciplina):
            continue
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        candidatos.append(titulo)
        if len(candidatos) >= 2:
            break

    if candidatos:
        titulo = candidatos[0]
        if len(candidatos) > 1 and (
            titulo.lower().endswith((" de", " da", " do", " das", " dos", " e")) or len(titulo) <= 28
        ):
            titulo = f"{titulo.rstrip(' -:')} {candidatos[1].lstrip('-: ')}".strip()
        titulo = limpar_prefixo_disciplina(titulo)
        if len(titulo) >= 6:
            return titulo[:120]

    titulo_multilinha = limpar_prefixo_disciplina(_extrair_titulo_multilinha(texto, disciplina))
    if len(titulo_multilinha) >= 6:
        return titulo_multilinha[:120]
    for linha in _limpar_linhas(texto):
        titulo = limpar_prefixo_disciplina(_limpar_titulo_material(linha, disciplina))
        if len(titulo) >= 6 and not _linha_generica(titulo, disciplina) and not _normalizar(titulo).startswith(("aula ", "slide ")):
            return titulo[:120]
    return Path(caminho_pdf).stem.replace("_", " ").replace("-", " ").title()


def _texto_metodologia(metodologia) -> str:
    blocos = []
    for item in metodologia or []:
        if isinstance(item, dict):
            blocos.append(f"{item.get('titulo', '')}\n{item.get('texto', '')}".strip())
        else:
            blocos.append(str(item))
    return "\n\n".join(blocos)


_PADRAO_CODIGO_APRENDIZAGEM = re.compile(r"\(?((?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?)\)?", flags=re.I)
_PADRAO_TURMA_METODOLOGIA = re.compile(
    r"\b(da turma|com a turma)\s+\d{1,2}\s*[º°oªa?]?\s*(?:ano|s[ée]rie|em|ef)?\s*[A-Z]?\b",
    flags=re.I,
)
_FINS_INCOMPLETOS_APRENDIZAGEM = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "em",
    "e",
    "com",
    "para",
    "por",
    "que",
}


def _trecho_incompleto_aprendizagem(texto: str) -> bool:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return True
    normalizado = _normalizar(texto)
    if any(marcador in texto for marcador in ["⬅", "←", "→"]):
        return True
    if "http" in normalizado or "disponivel em" in normalizado:
        return True
    if texto.endswith((",", ";", ":", "/", "-")):
        return True
    if texto.count("(") > texto.count(")") or texto.count("[") > texto.count("]"):
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and _normalizar(palavras[-1]) in _FINS_INCOMPLETOS_APRENDIZAGEM:
        return True
    if texto.count("?") >= 2 or re.match(r"^(?:o que|como|por que|qual)\b", normalizado):
        return True
    return len(texto) > 260


def _foco_limpo_aprendizagem(tema: str, conceito: str = "") -> str:
    for candidato in [tema, conceito, "o tema da aula"]:
        texto = re.sub(r"\s+", " ", str(candidato or "")).strip(" .:-")
        if texto and not _trecho_incompleto_aprendizagem(texto):
            return texto[:140]
    return "o tema da aula"


def _sanitizar_aprendizagem(aprendizagem: str, tema: str, conceito: str = "") -> str:
    texto = re.sub(r"\s+", " ", str(aprendizagem or "")).strip()
    texto = re.sub(r"^(?:C\d+\s*:\s*)?(?:Habilidade\s*:\s*)?", "", texto, flags=re.I).strip()
    match = _PADRAO_CODIGO_APRENDIZAGEM.search(texto)
    codigo = f"({match.group(1).upper()})" if match else ""

    if _trecho_incompleto_aprendizagem(texto):
        foco = _foco_limpo_aprendizagem(tema, conceito)
        if codigo:
            return f"Habilidade: {codigo} Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."
        return f"Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."

    if codigo and not texto.lower().startswith("habilidade:"):
        texto = f"Habilidade: {texto}"
    return texto


def _remover_turma_metodologia(texto: str) -> str:
    return _PADRAO_TURMA_METODOLOGIA.sub(lambda m: m.group(1), str(texto or ""))


def _indice_variacao(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(parte or "") for parte in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


def _escolher_variacao(opcoes: list[str], partes: list[str]) -> str:
    return opcoes[_indice_variacao(partes, len(opcoes))]


_VARIACOES_INICIO_METODOLOGIA = [
    (
        r"^Retomar conhecimentos previos",
        [
            "Retomar conhecimentos previos",
            "Mobilizar conhecimentos previos",
            "Ativar conhecimentos previos",
            "Iniciar pela retomada dos conhecimentos previos",
        ],
    ),
    (
        r"^Retomar conhecimentos prévios",
        [
            "Retomar conhecimentos prévios",
            "Mobilizar conhecimentos prévios",
            "Ativar conhecimentos prévios",
            "Iniciar pela retomada dos conhecimentos prévios",
        ],
    ),
    (
        r"^Promover discussao",
        [
            "Promover discussao",
            "Abrir dialogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Promover discussão",
        [
            "Promover discussão",
            "Abrir diálogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Apresentar",
        [
            "Apresentar",
            "Introduzir",
            "Explorar",
            "Contextualizar",
        ],
    ),
    (
        r"^Realizar leitura guiada",
        [
            "Realizar leitura guiada",
            "Conduzir leitura guiada",
            "Mediar a leitura guiada",
            "Organizar leitura orientada",
        ],
    ),
    (
        r"^Conduzir leitura",
        [
            "Conduzir leitura",
            "Mediar leitura",
            "Organizar leitura",
            "Orientar leitura",
        ],
    ),
    (
        r"^Analisar",
        [
            "Analisar",
            "Explorar",
            "Examinar",
            "Investigar com a turma",
        ],
    ),
    (
        r"^Explicar",
        [
            "Explicar",
            "Desenvolver a explicacao sobre",
            "Construir a explicacao de",
            "Apresentar de forma progressiva",
        ],
    ),
    (
        r"^Orientar",
        [
            "Orientar",
            "Acompanhar",
            "Conduzir",
            "Mediar",
        ],
    ),
    (
        r"^Socializar",
        [
            "Socializar",
            "Compartilhar coletivamente",
            "Promover a socializacao de",
            "Retomar com a turma",
        ],
    ),
    (
        r"^Sistematizar",
        [
            "Sistematizar",
            "Organizar",
            "Registrar de forma coletiva",
            "Consolidar",
        ],
    ),
    (
        r"^Finalizar com",
        [
            "Finalizar com",
            "Concluir com",
            "Encaminhar o fechamento com",
            "Organizar uma sintese final com",
        ],
    ),
    (
        r"^Encerrar com",
        [
            "Encerrar com",
            "Fechar a aula com",
            "Concluir com",
            "Promover o encerramento com",
        ],
    ),
    (
        r"^Retomar a importancia",
        [
            "Retomar a importancia",
            "Destacar, no fechamento, a importancia",
            "Conduzir uma sintese sobre a importancia",
            "Fechar a aula reforcando a importancia",
        ],
    ),
    (
        r"^Retomar a importância",
        [
            "Retomar a importância",
            "Destacar, no fechamento, a importância",
            "Conduzir uma síntese sobre a importância",
            "Fechar a aula reforçando a importância",
        ],
    ),
]


def _variar_inicio_etapa(texto: str, partes_seed: list[str]) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return ""

    for padrao, opcoes in _VARIACOES_INICIO_METODOLOGIA:
        if re.search(padrao, texto, flags=re.IGNORECASE):
            escolha = _escolher_variacao(opcoes, partes_seed + [padrao, texto[:160]])
            return re.sub(padrao, escolha, texto, count=1, flags=re.IGNORECASE)
    return texto


def _variar_linguagem_metodologia(metodologia, disciplina: str, turma: str, tema: str):
    """Aplica variacao linguistica controlada sem alterar a estrutura pedagogica."""
    variadas = []
    for idx, item in enumerate(metodologia or []):
        if not isinstance(item, dict):
            variadas.append(item)
            continue

        titulo = str(item.get("titulo", "")).strip()
        texto = str(item.get("texto", "")).strip()
        texto_variado = _variar_inicio_etapa(
            texto,
            [disciplina, turma, tema, titulo, str(idx)],
        )
        texto_variado = _remover_turma_metodologia(texto_variado)
        novo_item = dict(item)
        novo_item["texto"] = texto_variado
        variadas.append(novo_item)
    return variadas


def _acompanhamento_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        f"Verificar se os estudantes compreendem os conceitos centrais relacionados a {tema} durante as discussões e atividades propostas.",
        "Observar a participação, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
        "Acompanhar se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
    ]

    if perfil == "matematica":
        return [
            f"Verificar se os estudantes identificam corretamente os elementos matemáticos envolvidos em {tema} e organizam estratégias coerentes de resolução.",
            "Observar se os estudantes utilizam adequadamente procedimentos, propriedades e registros matemáticos durante as resoluções.",
            "Acompanhar se os estudantes interpretam os resultados encontrados e conseguem justificar os caminhos escolhidos ao longo das atividades.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            f"Verificar se os estudantes compreendem as ideias centrais de {tema} e identificam os elementos textuais trabalhados na aula.",
            "Observar a participação nas leituras, discussões e registros, considerando a capacidade de argumentar, interpretar e revisar as respostas.",
            "Acompanhar se os estudantes aplicam as estratégias de leitura, análise ou produção textual com progressiva autonomia.",
        ]

    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return [
            f"Verificar se os estudantes relacionam {tema} aos conceitos científicos trabalhados e utilizam evidências para sustentar suas respostas.",
            "Observar a participação nas investigações, registros e socializações, considerando a clareza das hipóteses e explicações apresentadas.",
            "Acompanhar se os estudantes conseguem interpretar fenômenos, dados ou experimentos com base nos conceitos desenvolvidos na aula.",
        ]

    return base


def _acessibilidade_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        "Disponibilizar mediação individualizada durante as atividades, adequando explicações, tempo e forma de resposta conforme as necessidades da turma.",
        "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensão dos conceitos trabalhados.",
        "Organizar intervenções com exemplos comentados e acompanhamento próximo para apoiar estudantes com dificuldades de leitura, interpretação ou organização das tarefas.",
    ]

    if perfil == "matematica":
        return [
            "Disponibilizar resolução comentada e exemplos passo a passo para favorecer a compreensão dos procedimentos matemáticos.",
            "Utilizar apoio visual e retomadas coletivas para auxiliar estudantes com dificuldades na interpretação dos problemas.",
            "Realizar acompanhamento individualizado durante as atividades, auxiliando na organização dos cálculos e identificação das operações necessárias.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            "Oferecer apoio à leitura com destaque para palavras-chave, trechos importantes e orientações passo a passo para a realização das atividades.",
            "Utilizar mediação oral, retomadas coletivas e exemplos comentados para favorecer a compreensão dos textos e comandos.",
            "Adaptar tempo, forma de registro e acompanhamento das produções conforme as necessidades observadas na turma.",
        ]

    return base


def _acompanhamento_dinamico_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acompanhamento_dinamico(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


def _acessibilidade_dinamica_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acessibilidade_dinamica(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


from core.inteligencia_local import SistemaGeracaoMetodologica
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.extrator_pdf import ExtratorPDF

gerador_inteligente = SistemaGeracaoMetodologica()
_extrator_lib = ExtratorPDF()

def _aula_por_pdf(caminho_pdf: str, disciplina: str, turma: str, usar_ia: bool, provedor_ia: str, modelo_ia: str = "") -> dict:
    texto = _extrair_texto_pdf(caminho_pdf)
    tema = _tema_por_texto(texto, caminho_pdf, disciplina)
    perfil = _perfil_disciplina(disciplina)
    tipo = _detectar_tipo_aula(texto, tema, disciplina)
    
    ia_usada = False
    ia_erro = ""
    
    # 1. Tentar processar com IA
    if usar_ia:
        try:
            from core.ia import processar_plano_ia
            plano_ia = processar_plano_ia(texto, disciplina, turma, provedor_ia, modelo_ia)
            tema = plano_ia.get("tema") or tema
            aprendizagem = plano_ia.get("aprendizagem", "")
            metodologia = plano_ia.get("metodologia", [])
            metodologia = _variar_linguagem_metodologia(metodologia, disciplina, turma, tema)
            aprendizagem = _sanitizar_aprendizagem(aprendizagem, tema)
            
            desenvolvimento = _texto_metodologia(metodologia)
            
            # Extrair etapas e dados para acompanhamento enriquecido
            etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
            extracao = _extrator_lib.extrair(texto, tema)
            
            return {
                "tema": tema,
                "aprendizagem": aprendizagem,
                "metodologia": metodologia,
                "acompanhamento": gerar_acompanhamento_aprimorado(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina, perfil=perfil, tipo=tipo,
                    habilidade=extracao.get("habilidade", ""),
                    etapas_metodologia=etapas_titulos,
                ),
                "acessibilidade": gerar_acessibilidade_aprimorada(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina, perfil=perfil, tipo=tipo,
                    recursos_detectados=extracao.get("recursos_detectados"),
                ),
                "ia_usada": True,
                "ia_provedor": provedor_ia,
                "ia_erro": "",
            }
        except Exception as e:
            ia_erro = f"Falha na IA ({provedor_ia}): {str(e)[:150]}. Usando motor heurístico local."
    
    # 2. Fallback heurístico — usa o motor sofisticado do lote.py
    #    em vez do motor fraco do inteligencia_local.py
    metodologia = _montar_etapas_metodologia(texto, disciplina, turma, tema)
    metodologia = _variar_linguagem_metodologia(metodologia, disciplina, turma, tema)
    
    # Extrair dados estruturados do PDF
    extracao = _extrator_lib.extrair(texto, tema)
    conceito = extracao.get("conceito_extraido", tema)
    habilidade = extracao.get("habilidade", "")
    recursos = extracao.get("recursos_detectados", [])
    
    # Se o extrator encontrou uma habilidade/BNCC no PDF, usa ela diretamente
    if habilidade and len(habilidade) > 15:
        aprendizagem = habilidade
    else:
        verbo = "Aplicar atividades e compreender" if tipo == "pratica" else "Compreender e analisar"
        conceito_aprendizagem = _foco_limpo_aprendizagem(tema, conceito)
        aprendizagem = f"{verbo} os conceitos relacionados a: {conceito_aprendizagem}."
    aprendizagem = _sanitizar_aprendizagem(aprendizagem, tema, conceito)
    
    desenvolvimento = _texto_metodologia(metodologia)
    etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
    
    return {
        "tema": tema,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        ),
        "acessibilidade": gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        ),
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro,
    }


def processar_varios_pdfs(
    caminhos_pdf,
    disciplina: str,
    turma: str,
    bimestre: str = "",
    usar_ia: bool = False,
    provedor_ia: str = "",
    modelo_ia: str = "",
    dividir_metodologia: bool = False,
) -> list[dict]:
    aulas = []
    for idx, caminho in enumerate(caminhos_pdf or []):
        aula = _aula_por_pdf(caminho, disciplina, turma, usar_ia, provedor_ia, modelo_ia)
        if dividir_metodologia:
            texto = _texto_metodologia(aula["metodologia"])
            parte1, parte2 = processar_pdf_e_dividir_metodologia(texto)
            if idx % 2 == 0:
                aula["metodologia"] = [{"titulo": "Primeiro momento", "texto": parte1}]
            else:
                aula["tema"] = f"{aula['tema']} - continuidade"
                aula["metodologia"] = [{"titulo": "Segundo momento", "texto": parte2}]
            aulas.append(aula)
        else:
            aulas.append(aula)
    return aulas
