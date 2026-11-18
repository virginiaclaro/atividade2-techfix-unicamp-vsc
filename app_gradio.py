import os
import re
import gradio as gr
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
CHAVE = os.getenv("SUPABASE_KEY")

if not URL or not CHAVE:
    raise RuntimeError("Configure SUPABASE_URL e SUPABASE_KEY no .env")


def abrir_os(email_login, senha, nome, endereco,
             email_cliente, celular, modelo, problema):

    # Validar os campos antes de acessar o banco.
    campos = [email_login, senha, nome, endereco,
              email_cliente, celular, modelo, problema]

    if any(not str(c or "").strip() for c in campos):
        return "Preencha todos os campos obrigatórios."

    email_cliente = email_cliente.strip().lower()
    celular = re.sub(r"\D", "", celular)

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_cliente):
        return "Informe um e-mail válido para o cliente."

    if not re.fullmatch(r"[0-9]{10,13}", celular):
        return "Informe um celular com 10 a 13 dígitos."

    try:
        # Cada operação usa um cliente Supabase próprio.
        # Isso evita compartilhar sessões entre atendentes.
        banco = create_client(URL, CHAVE)

        login = banco.auth.sign_in_with_password({
            "email": email_login.strip(),
            "password": senha
        })

        if not login.session:
            return "Não foi possível autenticar o atendente."

        # Verificar o perfil autenticado.
        perfil = banco.rpc("meu_perfil").execute().data

        if perfil not in ("atendente", "gerente"):
            return "Usuário sem permissão para abrir OS."

        # Chamar a função PostgreSQL.
        resposta = banco.rpc("abrir_ordem_servico", {
            "p_nome": nome.strip(),
            "p_endereco": endereco.strip(),
            "p_email": email_cliente,
            "p_celular": celular,
            "p_modelo": modelo.strip(),
            "p_problema": problema.strip()
        }).execute()

        return f"Ordem de serviço nº {resposta.data} criada com sucesso! Status: Aberto."

    except Exception:
        return (
            "Não foi possível concluir o cadastro. "
            "Confira os dados e as credenciais e tente novamente."
        )


with gr.Blocks(title="TechFix Informática") as demo:

    gr.Markdown("# TechFix Informática")
    gr.Markdown("### Abertura de Ordem de Serviço")

    with gr.Group():
        gr.Markdown("#### Identificação do atendente")

        email_login = gr.Textbox(
            label="E-mail do atendente",
            placeholder="atendente@exemplo.com"
        )

        senha = gr.Textbox(
            label="Senha",
            type="password"
        )

    with gr.Group():
        gr.Markdown("#### Dados do cliente")

        nome = gr.Textbox(label="Nome completo")
        endereco = gr.Textbox(label="Endereço")
        email_cliente = gr.Textbox(label="E-mail do cliente")
        celular = gr.Textbox(label="Celular / WhatsApp")

    with gr.Group():
        gr.Markdown("#### Equipamento e problema")

        modelo = gr.Textbox(label="Modelo do computador")
        problema = gr.Textbox(
            label="Problema relatado",
            lines=3
        )

    cadastrar = gr.Button(
        "Cadastrar ordem de serviço",
        variant="primary"
    )

    resultado = gr.Textbox(
        label="Resultado do cadastro",
        interactive=False
    )

    cadastrar.click(
        fn=abrir_os,
        inputs=[
            email_login, senha, nome, endereco,
            email_cliente, celular, modelo, problema
        ],
        outputs=resultado
    )


if __name__ == "__main__":
    demo.launch()