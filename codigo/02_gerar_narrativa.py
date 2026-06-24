from rdflib import Graph, Namespace, Literal, URIRef, RDF, OWL
import os


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_ONTOLOGIA = os.path.join(BASE, "ontologia", "ontologia_saude_mental.owl")
ARQ_SAIDA = os.path.join(BASE, "saida", "narrativa_gerada.txt")

NS = Namespace("http://www.efs.ufjf.br/ontologias/saude_mental.owl#")


def valor(literal):
    if literal is None:
        return None
    if isinstance(literal, Literal):
        return str(literal.toPython())
    return str(literal)


def limpar(uri_ou_literal):
    if isinstance(uri_ou_literal, Literal):
        return valor(uri_ou_literal)
    texto = str(uri_ou_literal)
    if "#" in texto:
        texto = texto.split("#")[-1]
    for suf in ("_C1", "_C2", "_C3"):
        if texto.endswith(suf):
            texto = texto[:-3]
    return texto.replace("_", " ").strip()

def carregar_grafo(caminho):
    g = Graph()
    g.parse(caminho, format="xml")
    print(f"[OK] Ontologia carregada: {len(g)} triplas.")
    return g


def extrair_pacientes(g):
    q = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?paciente WHERE { ?paciente rdf:type sm:Paciente . }
    """
    return [row.paciente for row in g.query(q)]


def dados_do_paciente(g, paciente_uri):
    q = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    SELECT ?nome ?idade ?afeccao ?dataDiag WHERE {
        ?p sm:temNome ?nome .
        OPTIONAL { ?p sm:temIdade ?idade . }
        OPTIONAL {
            ?p sm:apresentaAfeccao ?afeccao .
            OPTIONAL { ?afeccao sm:dataDiagnostico ?dataDiag . }
        }
        FILTER(?p = <%s>)
    }
    """ % str(paciente_uri)

    info = {"uri": paciente_uri, "nome": None, "idade": None,
            "afeccao": None, "data_diag": None,
            "sintomas": [], "tratamentos": [], "medicamentos": [],
            "profissional": None, "prof_tipo": None, "prof_registro": None}

    for row in g.query(q):
        info["nome"] = valor(row.nome) if row.nome else None
        info["idade"] = valor(row.idade) if row.idade else None
        info["afeccao"] = limpar(row.afeccao) if row.afeccao else None
        info["data_diag"] = valor(row.dataDiag) if row.dataDiag else None

    q_sint = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    SELECT ?s WHERE { <%s> sm:manifestaSintoma ?s . }
    """ % str(paciente_uri)
    info["sintomas"] = [limpar(r.s) for r in g.query(q_sint)]

    q_trat = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    SELECT ?t WHERE { <%s> sm:recebeTratamento ?t . }
    """ % str(paciente_uri)
    info["tratamentos"] = [limpar(r.t) for r in g.query(q_trat)]

    q_med = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    SELECT ?nomeMed WHERE {
        <%s> sm:recebeTratamento ?t .
        ?t sm:nomeMedicamento ?nomeMed .
    }
    """ % str(paciente_uri)
    info["medicamentos"] = [valor(r.nomeMed) for r in g.query(q_med)]

    q_prof = """
    PREFIX sm: <http://www.efs.ufjf.br/ontologias/saude_mental.owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?nomeProf ?tipo ?reg WHERE {
        ?prof sm:atendePaciente <%s> .
        ?prof sm:temNome ?nomeProf .
        ?prof rdf:type ?tipo .
        OPTIONAL { ?prof sm:registroProfissional ?reg . }
        FILTER(?tipo IN (sm:Psiquiatra, sm:Psicologo))
    }
    """ % str(paciente_uri)
    for r in g.query(q_prof):
        info["profissional"] = valor(r.nomeProf)
        info["prof_tipo"] = limpar(r.tipo)
        info["prof_registro"] = valor(r.reg) if r.reg else None

    return info

def listar_em_portugues(itens):
    if not itens:
        return ""
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def gerar_narrativa_paciente(info, n_cenario):
    frases = []

    abertura = f"O paciente {info['nome']}"
    if info["idade"]:
        abertura += f", de {info['idade']} anos,"
    if info["afeccao"]:
        abertura += f" apresenta a afecção de {info['afeccao']}"
        if info["data_diag"]:
            abertura += f", diagnosticada em {info['data_diag']}"
    abertura += "."
    frases.append(abertura)

    if info["sintomas"]:
        sint = listar_em_portugues([s.lower() for s in info["sintomas"]])
        frases.append(f"Este paciente manifesta os seguintes sintomas: {sint}.")

    if info["profissional"]:
        f_prof = f"O profissional responsável pelo seu atendimento é " \
                 f"{info['profissional']}, que atua como {info['prof_tipo']}"
        if info["prof_registro"]:
            f_prof += f" (registro {info['prof_registro']})"
        f_prof += "."
        frases.append(f_prof)

    if info["tratamentos"]:
        trat = listar_em_portugues(info["tratamentos"])
        frases.append(f"A linha de intervenção indicada para {info['nome']} "
                      f"compreende: {trat}.")

    if info["medicamentos"]:
        med = listar_em_portugues(info["medicamentos"])
        frases.append(f"Quanto à terapia farmacológica, foi prescrito "
                      f"o medicamento {med}.")

    cabecalho = f"=== CENÁRIO CLÍNICO {n_cenario} ==="
    return cabecalho + "\n" + " ".join(frases)


def main():
    g = carregar_grafo(ARQ_ONTOLOGIA)

    pacientes = extrair_pacientes(g)
    print(f"[OK] {len(pacientes)} pacientes encontrados na ABox.")

    pacientes = sorted(pacientes, key=lambda u: limpar(u))

    blocos = []
    intro = ("CONTEXTO CLÍNICO EXTRAÍDO DA ONTOLOGIA DE SAÚDE MENTAL\n"
             "(Narrativa gerada automaticamente a partir de triplas RDF)\n")
    blocos.append(intro)

    for i, p in enumerate(pacientes, start=1):
        info = dados_do_paciente(g, p)
        narrativa = gerar_narrativa_paciente(info, i)
        blocos.append(narrativa)
        print(f"\n--- Triplas do Cenário {i} ({info['nome']}) ---")
        print(f"  {info['nome']} -> apresentaAfeccao -> {info['afeccao']}")
        for s in info["sintomas"]:
            print(f"  {info['nome']} -> manifestaSintoma -> {s}")
        if info["profissional"]:
            print(f"  {info['profissional']} -> atendePaciente -> {info['nome']}")
        for t in info["tratamentos"]:
            print(f"  {info['nome']} -> recebeTratamento -> {t}")

    texto_final = "\n\n".join(blocos)

    with open(ARQ_SAIDA, "w", encoding="utf-8") as f:
        f.write(texto_final)

    print(f"\n[OK] Narrativa salva em: {ARQ_SAIDA}")
    print("\n" + "=" * 70)
    print("NARRATIVA GERADA:")
    print("=" * 70)
    print(texto_final)


if __name__ == "__main__":
    main()
