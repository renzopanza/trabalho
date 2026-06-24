# -*- coding: utf-8 -*-
"""
============================================================================
ETAPA 3 - Injeção de Contexto e Validação com LLM
============================================================================
Disciplina : Especificação Formal de Software

Este script auxiliar:
  1. Lê a narrativa gerada na Etapa 2 (narrativa_gerada.txt).
  2. Monta o SYSTEM PROMPT de validação (instrução anti-alucinação).
  3. Organiza a bateria de testes (QA) com 5 perguntas por cenário,
     cobrindo: perguntas diretas, de inferência relacional e de
     restrição semântica.
  4. (Opcional) Envia as perguntas a uma LLM local via Ollama, caso o
     serviço esteja disponível em http://localhost:11434.

Como executar a validação real:
  - Local : instale o Ollama (https://ollama.com), rode `ollama pull llama3`
            e em seguida `python3 03_validar_llm.py --executar`.
  - API   : adapte a função `chamar_llm_api()` com sua chave do Google AI
            Studio (ou outro provedor compatível).

Sem a flag --executar, o script apenas imprime os prompts prontos para
serem copiados manualmente para a interface da LLM.
============================================================================
"""

import os
import sys
import json
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_NARRATIVA = os.path.join(BASE, "saida", "narrativa_gerada.txt")

# Parâmetros recomendados para o experimento (baixa temperatura = menos alucinação)
MODELO_LLM = "llama3"
TEMPERATURA = 0.0

# ---------------------------------------------------------------------------
# 1. SYSTEM PROMPT (injeção de contexto)
# ---------------------------------------------------------------------------
def montar_system_prompt(narrativa):
    return (
        "Você é um assistente de validação. Utilize ESTRITAMENTE os fatos "
        "contidos no texto abaixo para responder às perguntas, sem alucinar "
        "ou trazer conhecimentos externos. Se a informação não estiver "
        "presente no texto, responda exatamente: 'Informação não consta no "
        "contexto fornecido.'\n\n"
        "===== CONTEXTO (BASE DE CONHECIMENTO) =====\n"
        f"{narrativa}\n"
        "===== FIM DO CONTEXTO =====\n"
    )


# ---------------------------------------------------------------------------
# 2. BATERIA DE TESTES (QA) - 5 perguntas por cenário
# ---------------------------------------------------------------------------
# Cada item: (tipo, pergunta, resposta_esperada_segundo_a_ontologia)
BATERIA = {
    "Cenário 1 - Ana Lima (Ansiedade Generalizada)": [
        ("Direta",
         "Quem é o profissional responsável pela paciente Ana Lima?",
         "Dr. André Souza (Psiquiatra)."),
        ("Direta",
         "Qual a idade da paciente Ana Lima e qual sua afecção?",
         "29 anos; Ansiedade Generalizada."),
        ("Inferência relacional",
         "Considerando os sintomas descritos, qual o tratamento "
         "farmacológico associado a esta paciente?",
         "Sertralina (Sertralina 50mg)."),
        ("Inferência relacional",
         "Por que é coerente que um psiquiatra atenda Ana Lima, "
         "dado o tratamento prescrito?",
         "Porque há prescrição de medicamento (Sertralina), e o profissional "
         "que a atende é psiquiatra, habilitado a prescrever fármacos."),
        ("Restrição semântica",
         "Ana Lima possui diagnóstico de Depressão Maior? Responda apenas "
         "com base no contexto.",
         "Não. Segundo o contexto, sua afecção é Ansiedade Generalizada. "
         "(TBox: TranstornoAnsioso e TranstornoDepressivo são disjuntos.)"),
    ],
    "Cenário 2 - Carlos Mendes (Depressão Maior)": [
        ("Direta",
         "Qual é a afecção do paciente Carlos Mendes?",
         "Depressão Maior."),
        ("Direta",
         "Quem realiza o atendimento de Carlos Mendes e qual sua formação?",
         "Dra. Beatriz Costa, Psicóloga."),
        ("Inferência relacional",
         "Qual a linha de intervenção indicada para Carlos Mendes?",
         "Terapia Interpessoal (intervenção não farmacológica)."),
        ("Inferência relacional",
         "Carlos Mendes recebeu algum medicamento? Justifique pelo contexto.",
         "Não. O contexto indica apenas Terapia Interpessoal; nenhuma "
         "prescrição de medicamento é mencionada para ele."),
        ("Restrição semântica",
         "A Dra. Beatriz Costa prescreveu algum fármaco a Carlos Mendes?",
         "Informação não consta / Não. O contexto não atribui medicamento a "
         "este paciente (coerente com o papel de psicóloga)."),
    ],
    "Cenário 3 - Daniela Rocha (Transtorno de Pânico)": [
        ("Direta",
         "Qual a afecção e a data de diagnóstico de Daniela Rocha?",
         "Transtorno de Pânico; diagnosticada em 2025-05-02."),
        ("Direta",
         "Quais sintomas Daniela Rocha manifesta?",
         "Palpitação, falta de ar e medo intenso."),
        ("Inferência relacional",
         "Qual o medicamento prescrito para Daniela Rocha?",
         "Escitalopram (Escitalopram 10mg)."),
        ("Inferência relacional",
         "O mesmo profissional atende mais de um paciente no contexto? Quem?",
         "Sim, Dr. André Souza atende Ana Lima e Daniela Rocha."),
        ("Restrição semântica",
         "Daniela Rocha é atendida por uma psicóloga? Responda pelo contexto.",
         "Não. É atendida pelo Dr. André Souza, psiquiatra."),
    ],
}


# ---------------------------------------------------------------------------
# 3. INTEGRAÇÃO COM LLM LOCAL (Ollama) - opcional
# ---------------------------------------------------------------------------
def chamar_ollama(system_prompt, pergunta):
    """Envia uma pergunta ao Ollama local. Retorna a resposta ou erro."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": MODELO_LLM,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pergunta},
        ],
        "stream": False,
        "options": {"temperature": TEMPERATURA},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            corpo = json.loads(resp.read().decode("utf-8"))
            return corpo.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[ERRO ao contatar Ollama: {e}]"


# ---------------------------------------------------------------------------
# 4. EXECUÇÃO
# ---------------------------------------------------------------------------
def main():
    with open(ARQ_NARRATIVA, encoding="utf-8") as f:
        narrativa = f.read()

    system_prompt = montar_system_prompt(narrativa)
    executar = "--executar" in sys.argv

    print("#" * 74)
    print("# SYSTEM PROMPT (a ser injetado na LLM)")
    print("#" * 74)
    print(system_prompt)

    print("#" * 74)
    print(f"# BATERIA DE TESTES  (modelo={MODELO_LLM}, temperatura={TEMPERATURA})")
    print(f"# Modo: {'EXECUÇÃO REAL via Ollama' if executar else 'APENAS IMPRESSÃO'}")
    print("#" * 74)

    for cenario, perguntas in BATERIA.items():
        print(f"\n{'='*74}\n{cenario}\n{'='*74}")
        for i, (tipo, pergunta, esperada) in enumerate(perguntas, start=1):
            print(f"\n[Q{i}] ({tipo})")
            print(f"  Pergunta : {pergunta}")
            print(f"  Esperado : {esperada}")
            if executar:
                resposta = chamar_ollama(system_prompt, pergunta)
                print(f"  LLM      : {resposta}")


if __name__ == "__main__":
    main()
