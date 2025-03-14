import streamlit as st
import pandas as pd
import datetime
import json
import hashlib
import os

# Configuração da página
st.set_page_config(page_title="Estudo", page_icon=":books:", layout="wide")

# Função para carregar usuários salvos
def carregar_usuarios():
    try:
        with open("usuarios.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Função para salvar usuários
def salvar_usuarios(usuarios):
    with open("usuarios.json", "w") as file:
        json.dump(usuarios, file)

# Função para gerar hash da senha
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Função para carregar dados do usuário
def carregar_dados_usuario(usuario):
    caminho = f"dados_{usuario}.json"
    if os.path.exists(caminho):
        with open(caminho, "r") as file:
            return json.load(file)
    return {"df": {}, "df2": {}}

# Função para salvar dados do usuário
def salvar_dados_usuario(usuario):
    if usuario:
        dados = {
            "df": st.session_state.df.to_dict(orient='list'),
            "df2": st.session_state.df2.to_dict(orient='list')
        }
        with open(f"dados_{usuario}.json", "w") as file:
            json.dump(dados, file)

# Inicializando sessão de usuário
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# Seção de login e registro
usuarios = carregar_usuarios()
st.sidebar.title("Autenticação")
opcao = st.sidebar.radio("Escolha uma opção", ["Login", "Registrar"])

if opcao == "Registrar":
    novo_usuario = st.sidebar.text_input("Nome de usuário")
    nova_senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Registrar"):
        if novo_usuario in usuarios:
            st.sidebar.warning("Usuário já existe!")
        else:
            usuarios[novo_usuario] = hash_senha(nova_senha)
            salvar_usuarios(usuarios)
            st.sidebar.success("Usuário registrado com sucesso!")

elif opcao == "Login":
    usuario = st.sidebar.text_input("Nome de usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == hash_senha(senha):
            st.session_state.usuario_logado = usuario
            st.sidebar.success(f"Bem-vindo, {usuario}!")
            # Carregar dados do usuário ao logar
            dados_usuario = carregar_dados_usuario(usuario)
            st.session_state.df = pd.DataFrame.from_dict(dados_usuario["df"])
            st.session_state.df2 = pd.DataFrame.from_dict(dados_usuario["df2"])
            
            # Garantir que as colunas necessárias existam
            colunas_revisoes = ["materia", "assunto", "data_inicial", "revisao_1", "revisao_2", "revisao_3", "revisao_4"]
            for col in colunas_revisoes:
                if col not in st.session_state.df.columns:
                    st.session_state.df[col] = None
        else:
            st.sidebar.error("Usuário ou senha incorretos!")

# Se o usuário não estiver logado, interrompe a execução
if not st.session_state.usuario_logado:
    st.stop()

# Botão de logout
if st.sidebar.button("Sair"):
    salvar_dados_usuario(st.session_state.usuario_logado)
    st.session_state.usuario_logado = None
    st.rerun()

# Título do aplicativo
st.title("Estudo")
st.write("Aqui você pode configurar seus estudos programando revisões ou fazendo ciclo de estudos para o mês!")

# Criando DataFrames na sessão do Streamlit
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["materia", "assunto", "data_inicial", "revisao_1", "revisao_2", "revisao_3", "revisao_4"])
if "df2" not in st.session_state:
    st.session_state.df2 = pd.DataFrame(columns=["Matéria", "Dificuldade", "Tempo de estudo mensal"])

# Função para monitorar mudanças e salvar dados automaticamente
def monitorar_mudancas():
    if st.session_state.usuario_logado:
        salvar_dados_usuario(st.session_state.usuario_logado)

# Adicionando um botão para forçar a atualização dos dados
if st.button("Salvar progresso"):
    monitorar_mudancas()
    st.success("Progresso salvo com sucesso!")

# Função para baixar DataFrame como Excel
def baixar_excel(df, nome_arquivo, botao_label):
    """Permite baixar um DataFrame como um arquivo Excel."""
    excel_file = nome_arquivo
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as file:
        st.download_button(
            label=botao_label,
            data=file,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

tabs = st.tabs(["Revisões", "Ciclo de Estudos"])

with tabs[0]:
    st.title("Revisões")
    st.write("Aqui você pode criar novos estudos e programar revisões para cada um deles!")
    
    INTERVALOS = [1, 7, 15, 30]

    def adicionar_estudo(materia, assunto):
        """Adiciona um novo estudo e calcula as revisões."""
        hoje = datetime.date.today().isoformat()
        revisoes = [(datetime.date.today() + datetime.timedelta(days=d)).isoformat() for d in INTERVALOS]
        novo_dado = pd.DataFrame([[materia, assunto, hoje, *revisoes]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
        st.success(f"📚 Matéria '{materia}' - Assunto '{assunto}' registrada!")
    
    def listar_revisoes():
        """Mostra quais revisões estão programadas para hoje."""
        hoje = datetime.date.today().isoformat()
        revisoes_hoje = st.session_state.df[
            (st.session_state.df[["revisao_1", "revisao_2", "revisao_3", "revisao_4"]] == hoje).any(axis=1)
        ]
        if not revisoes_hoje.empty:
            st.subheader("📆 Revisões para hoje:")
            st.dataframe(revisoes_hoje[["materia", "assunto"]])
        else:
            st.write("🎉 Nenhuma revisão programada para hoje!")
    
    st.header("Adicionar Novo Estudo")
    materia = st.text_input("Nome da matéria")
    assunto = st.text_input("Assunto")
    if st.button("Adicionar"):
        if materia.strip() and assunto.strip():
            adicionar_estudo(materia.strip(), assunto.strip())
        else:
            st.warning("Por favor, digite um nome válido para a matéria e o assunto.")

    st.header("Revisões de Hoje")
    listar_revisoes()
    
    st.header("📊 Todas as Revisões")
    st.dataframe(st.session_state.df)
    
    st.header("📂 Exportar Dados")
    baixar_excel(st.session_state.df, "revisoes.xlsx", "📥 Baixar Revisões (Excel)")

with tabs[1]:
    st.title("Ciclo de Estudos")
    st.write("Aqui você pode fazer um ciclo de estudos e marcar as horas estudadas! "
    "Um ciclo de estudos é um metódo onde você estuda determinadas horas da matéria até completar o tempo de estudo mensal dela.")
    st.header("Adicionar Matéria, Dificuldade e Tempo de Estudo Mensal")
    materia = st.text_input("Matéria")
    dificuldade = st.number_input("Dificuldade (ponha um valor de 1 a 3 para a dificuldade)", min_value=1, max_value=3)
    horas = st.number_input("Insira seu tempo de estudo mensal em horas", min_value=0)

    colunas = ["Matéria", "Dificuldade", "Tempo de estudo mensal"]
    
    def adicionar_materia(materia, dificuldade, horas):
        novo_dado = pd.DataFrame([[materia, int(dificuldade), int(horas)]], columns=colunas)
        st.session_state.df2 = pd.concat([st.session_state.df2, novo_dado], ignore_index=True)
        st.success(f"Matéria '{materia}' adicionada com sucesso com dificuldade {dificuldade}!")

    if st.button("Adicionar matéria e dificuldade"):
        if materia.strip():
            adicionar_materia(materia.strip(), dificuldade, horas)
        else:
            st.warning("Por favor, digite um nome válido para a matéria.")

    def calcular_tempo_estudo(horas):
        if not st.session_state.df2.empty:
            df = st.session_state.df2.copy()
            if df["Dificuldade"].sum() > 0:
                df["Tempo de estudo mensal"] = (df["Dificuldade"] / df["Dificuldade"].sum()) * horas
                df["Tempo de estudo mensal"] = df["Tempo de estudo mensal"].astype(int)
                st.session_state.df2 = df
            else:
                st.warning("Não há dificuldades cadastradas para cálculo.")
        else:
            st.warning("Nenhuma matéria cadastrada para calcular o tempo de estudo.")

    if st.button("Calcular tempo de estudo"):
        if horas > 0:
            calcular_tempo_estudo(horas)
        else:
            st.warning("Por favor, insira um valor válido para o tempo de estudo mensal.")

    def excluir_assunto(materia):
        """Exclui uma matéria específica."""
        df = st.session_state.df2
        df = df[df["Matéria"] != materia]  # Remove apenas a matéria selecionada
        st.session_state.df2 = df  # Atualiza os dados na sessão
        st.warning(f"Matéria '{materia}' removida com sucesso!")
        st.rerun()  # Atualiza automaticamente a página

    st.header("Matérias Cadastradas")
    if not st.session_state.df2.empty:
        st.dataframe(st.session_state.df2)
    else:
        st.write("Nenhuma matéria cadastrada.")

    st.header("CheckList das Matérias")  # Adicionar um checklist para cada hora em cada matéria
    st.write("Aqui você pode marcar as horas de estudo de cada matéria, clique na matéria para expandir o checklist.")	

    df = st.session_state.df2

    if not df.empty:
        for _, row in df.iterrows():
            materia = row["Matéria"]
            total_horas = int(row["Tempo de estudo mensal"])  # Garante que é um número inteiro

            # Inicializa a visibilidade da matéria no session_state
            if f"mostrar_{materia}" not in st.session_state:
                st.session_state[f"mostrar_{materia}"] = False  # Começa oculta

            # Usa toggle para manter o estado da visibilidade
            st.session_state[f"mostrar_{materia}"] = st.toggle(f"{materia}", value=st.session_state[f"mostrar_{materia}"], key=f"toggle_{materia}")

            if st.session_state[f"mostrar_{materia}"]:  # Se estiver visível
                st.subheader(f"📖 {materia}")  # Exibe a matéria como título

                # Define o número máximo de colunas antes de quebrar para a próxima linha (exemplo: 5)
                max_columns = 5
                num_columns = (total_horas + max_columns - 1) // max_columns  # Número de linhas necessárias

                # Criando um dicionário para armazenar o progresso dos checkboxes
                if f"progress_{materia}" not in st.session_state:
                    st.session_state[f"progress_{materia}"] = {}

                # Criando os checkboxes
                for i in range(num_columns):
                    cols = st.columns(min(total_horas - i * max_columns, max_columns))  # Divide as horas em colunas
                    for hora in range(i * max_columns + 1, min((i + 1) * max_columns + 1, total_horas + 1)):
                        key = f"{materia}_hora_{hora}"
                        
                        # Se ainda não existir no session_state, inicializa como False
                        if key not in st.session_state[f"progress_{materia}"]:
                            st.session_state[f"progress_{materia}"][key] = False
                        
                        # Criando checkbox e armazenando no session_state
                        checked = st.session_state[f"progress_{materia}"][key]
                        new_checked = cols[hora - 1 - i * max_columns].checkbox(f"{hora}h", value=checked, key=key)
                        
                        # Atualiza o estado do checkbox no session_state
                        st.session_state[f"progress_{materia}"][key] = new_checked
    else:
        st.write("Nenhuma matéria cadastrada.")

        # Novo cabeçalho para o botão de zerar
    st.header("Zerar Todos os Checkpoints")

    # Botão para zerar todos os checkboxes
    if st.button("Zerar todos os checkboxes"):
        # Percorre todas as matérias e desmarca os checkboxes
        for _, row in df.iterrows():
            materia = row["Matéria"]
            total_horas = int(row["Tempo de estudo mensal"])  # Garante que é um número inteiro

            # Zera o progresso dos checkboxes removendo os valores do session_state
            if f"progress_{materia}" in st.session_state:
                st.session_state[f"progress_{materia}"] = {}  # Reseta todos os checkboxes

        st.success("Todos os checkboxes foram zerados!")

    else:
        st.write("Clique no botão acima para zerar todos os checkboxes.")

    # Novo cabeçalho para o botão de salvar
    st.header("Salvar Progresso")

    def baixar_excel():
        """Permite baixar o DataFrame como um arquivo Excel."""
        df = st.session_state.df2
        excel_file = "Ciclo_Estudos.xlsx"
        df.to_excel(excel_file, index=False)
        
        with open(excel_file, "rb") as file:
            st.download_button(
                label="📥 Baixar seu Ciclo de Estudos (Excel)",
                data=file,
                file_name="Ciclo_Estudos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    baixar_excel()
