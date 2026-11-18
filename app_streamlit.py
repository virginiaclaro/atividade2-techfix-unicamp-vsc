import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
CHAVE = os.getenv("SUPABASE_KEY")

st.set_page_config(
    page_title="TechFix - Painel Administrativo",
    page_icon="🖥️",
    layout="wide"
)

if not URL or not CHAVE:
    st.error("Configurações do Supabase ausentes.")
    st.stop()


def criar_conexao():
    return create_client(URL, CHAVE)


def fazer_logout():
    banco = st.session_state.get("banco")
    if banco is not None:
        try:
            banco.auth.sign_out()
        except Exception:
            pass

    st.session_state.pop("banco", None)
    st.session_state.pop("gerente_email", None)


st.title("🖥️ TechFix Informática")
st.caption("Painel administrativo de ordens de serviço")

# Inicializar a sessão do Streamlit
if "banco" not in st.session_state:
    st.session_state.banco = None

if "gerente_email" not in st.session_state:
    st.session_state.gerente_email = None


# Tela de login
if st.session_state.banco is None:

    st.subheader("Acesso do gerente")

    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        try:
            banco = criar_conexao()

            login = banco.auth.sign_in_with_password({
                "email": email.strip(),
                "password": senha
            })

            if not login.session:
                raise ValueError("Falha na autenticação.")

            perfil = banco.rpc("meu_perfil").execute().data

            if perfil != "gerente":
                banco.auth.sign_out()
                st.error("Acesso permitido apenas ao gerente.")
            else:
                st.session_state.banco = banco
                st.session_state.gerente_email = email.strip()
                st.rerun()

        except Exception:
            st.error("Não foi possível realizar o login.")

    st.stop()


# Painel autenticado
banco = st.session_state.banco

with st.sidebar:
    st.subheader("Administração")
    st.write(st.session_state.gerente_email)

    if st.button("Sair"):
        fazer_logout()
        st.rerun()


st.subheader("Ordens de serviço")

try:
    resposta = (
        banco.table("ordens_servico")
        .select(
            "id, cliente_id, modelo_computador, "
            "problema_relatado, status, "
            "data_abertura, data_atualizacao"
        )
        .order("id", desc=True)
        .execute()
    )

    df = pd.DataFrame(resposta.data)

    if df.empty:
        st.info("Nenhuma ordem de serviço cadastrada.")

    else:
        # Indicadores
        col1, col2, col3 = st.columns(3)

        col1.metric("Total de OS", len(df))
        col2.metric(
            "OS abertas",
            int((df["status"] == "Aberto").sum())
        )
        col3.metric(
            "OS concluídas",
            int((df["status"] == "Concluído").sum())
        )

        # Filtro por status
        opcoes = ["Todos"] + sorted(
            df["status"].dropna().unique().tolist()
        )

        status_escolhido = st.selectbox(
            "Filtrar por status",
            opcoes
        )

        if status_escolhido == "Todos":
            df_filtrado = df
        else:
            df_filtrado = df[
                df["status"] == status_escolhido
            ]

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )

except Exception:
    st.error(
        "Não foi possível consultar as ordens de serviço. "
        "Verifique a conexão e tente novamente."
    )


# ---------------------------------------
# Atualização do status da ordem de serviço
# ---------------------------------------

st.divider()
st.subheader("Atualizar status de uma OS")

try:
    # Buscar novamente as ordens disponíveis.
    resposta_os = (
        banco.table("ordens_servico")
        .select("id, modelo_computador, status")
        .order("id", desc=True)
        .execute()
    )

    ordens = resposta_os.data or []

    if not ordens:
        st.info("Não existem ordens de serviço para atualizar.")

    else:
        opcoes_os = {
            f"OS {item['id']} - {item['modelo_computador']}":
                item
            for item in ordens
        }

        with st.form("form_atualizar_status"):

            os_selecionada = st.selectbox(
                "Selecione a ordem de serviço",
                list(opcoes_os.keys())
            )

            dados_os = opcoes_os[os_selecionada]

            status_disponiveis = [
                "Aberto",
                "Em análise",
                "Aguardando peça",
                "Concluído",
                "Entregue"
            ]

            status_atual = dados_os["status"]

            novo_status = st.selectbox(
                "Novo status",
                status_disponiveis,
                index=status_disponiveis.index(status_atual)
            )

            salvar = st.form_submit_button(
                "Salvar alteração"
            )

        if salvar:
            if novo_status == status_atual:
                st.info("O status selecionado já é o atual.")

            else:
                (
                    banco.table("ordens_servico")
                    .update({
                        "status": novo_status
                })

                    .eq("id", dados_os["id"])
                    .execute()
                )

                st.success(
                    f"OS {dados_os['id']} atualizada "
                    f"para '{novo_status}'!"
                )

                st.rerun()

except Exception as erro:
    st.error(
        "Não foi possível atualizar as ordens de serviço."
    )


# ---------------------------------------
# Edição dos dados da ordem de serviço
# ---------------------------------------

st.divider()
st.subheader("Editar dados de uma OS")

try:
    resposta_edicao = (
        banco.table("ordens_servico")
        .select("id, modelo_computador, problema_relatado")
        .order("id", desc=True)
        .execute()
    )

    ordens_edicao = resposta_edicao.data or []

    if ordens_edicao:

        opcoes_edicao = {
            f"OS {item['id']} - {item['modelo_computador']}": item
            for item in ordens_edicao
        }

        with st.form("form_editar_os"):

            os_edicao = st.selectbox(
                "Selecione a OS para editar",
                list(opcoes_edicao.keys())
            )

            dados = opcoes_edicao[os_edicao]

            modelo_editado = st.text_input(
                "Modelo do computador",
                value=dados["modelo_computador"]
            )

            problema_editado = st.text_area(
                "Problema relatado",
                value=dados["problema_relatado"]
            )

            salvar_edicao = st.form_submit_button(
                "Salvar alterações"
            )

        if salvar_edicao:

            if not modelo_editado.strip() or not problema_editado.strip():
                st.error("Preencha todos os campos.")

            else:
                (
                    banco.table("ordens_servico")
                    .update({
                        "modelo_computador": modelo_editado.strip(),
                        "problema_relatado": problema_editado.strip()
                    })
                    .eq("id", dados["id"])
                    .execute()
                )

                st.success(
                    f"Dados da OS {dados['id']} atualizados!"
                )

                st.rerun()

    else:
        st.info("Nenhuma ordem de serviço disponível.")

except Exception:
    st.error("Não foi possível editar a ordem de serviço.")



# ---------------------------------------
# Exclusão de ordem de serviço
# ---------------------------------------

st.divider()
st.subheader("Excluir ordem de serviço")

try:
    resposta_exclusao = (
        banco.table("ordens_servico")
        .select("id, modelo_computador, status")
        .order("id", desc=True)
        .execute()
    )

    ordens_exclusao = resposta_exclusao.data or []

    if ordens_exclusao:
        opcoes_exclusao = {
            f"OS {item['id']} - {item['modelo_computador']}": item
            for item in ordens_exclusao
        }

        with st.form("form_excluir_os"):
            os_exclusao = st.selectbox(
                "Selecione a OS para excluir",
                list(opcoes_exclusao.keys())
            )

            dados_exclusao = opcoes_exclusao[os_exclusao]

            st.warning(
                f"A OS {dados_exclusao['id']} será excluída "
                "permanentemente do banco de dados."
            )

            confirmar = st.checkbox(
                "Confirmo que desejo excluir esta ordem de serviço."
            )

            excluir = st.form_submit_button(
                "Excluir OS",
                type="primary"
            )

        if excluir:
            if not confirmar:
                st.error(
                    "Marque a confirmação antes de excluir."
                )
            else:
                resultado_exclusao = (
                    banco.table("ordens_servico")
                    .delete()
                    .eq("id", dados_exclusao["id"])
                    .select("id")
                    .execute()
                )

                if resultado_exclusao.data:
                    st.success(
                        f"OS {dados_exclusao['id']} excluída com sucesso!"
                    )
                    st.rerun()
                else:
                    st.error(
                        "A OS não foi excluída. "
                        "Verifique se o registro ainda existe."
                    )
    else:
        st.info("Nenhuma ordem de serviço disponível.")

except Exception:
    st.error("Não foi possível excluir a ordem de serviço.")
