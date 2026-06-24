# Trabalho Prático — Especificação Formal de Software
## Engenharia de Conhecimento e Validação de Grafos com LLMs
### Domínio: Ontologia de Saúde Mental

---

## Integrantes do Grupo
- Renzo Faedda Panza
- Henrique Lamarca
- 

---

## Estrutura dos arquivos

```
trabalho/
├── ontologia/
│   └── ontologia_saude_mental.owl      # Etapa 1: TBox + ABox (OWL/RDF-XML)
├── codigo/
│   ├── 02_gerar_narrativa.py           # Etapa 2: SPARQL + NLG -> narrativa
│   ├── 03_validar_llm.py               # Etapa 3: System Prompt + bateria QA
├── saida/
│   ├── narrativa_gerada.txt            # Narrativa injetada na LLM
│   ├── diagrama_tbox.png               # Diagrama conceitual da TBox
│   └── Relatorio Tecnico - Trabalho final - Especificação Formal de Software.pdf           # Relatório completo (PDF)
└── README.md
```

---

## Como executar

Requisitos (Python 3.10+):
```bash
pip install rdflib owlready2 reportlab
```

### Etapa 1 — Gerar a narrativa
```bash
python codigo/02_gerar_narrativa.py
```
Carrega o `.owl`, extrai as triplas via SPARQL e gera `saida/narrativa_gerada.txt`.

### Etapa 2 — Validar com a LLM
```bash
# Apenas imprime os prompts e a bateria de testes:
python codigo/03_validar_llm.py
```
Alternativamente, copie o System Prompt e as perguntas para o **Gemini**, **ChatGPT**, ou outra interface de LLM.

---

## Resumo da ontologia
- **15 classes** (4 hierarquias: Individuo, CondicaoClinica, Sintoma, Intervencao)
- **7 object properties** (com domain/range)
- **5 data properties** (funcionais, tipadas)
- **3 cenários clínicos** na ABox (22 indivíduos)
- **5 axiomas de disjunção**

## Parâmetros do experimento com LLM
- 15 perguntas (5 por cenário): diretas, de inferência e de restrição semântica