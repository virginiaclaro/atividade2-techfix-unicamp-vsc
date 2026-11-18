# TechFix Informática

## Atividade 2 — Aplicações em Data Science

Projeto desenvolvido como atividade acadêmica da
Pós-Graduação em Data Science da UNICAMP.


## Objetivo

Desenvolver um sistema de gerenciamento de ordens
de serviço de uma empresa fictícia de assistência
técnica em informática.

## Tecnologias utilizadas

- Python
- Gradio
- Streamlit
- Supabase
- PostgreSQL
- Pandas

## Funcionalidades

### Aplicativo do atendente — Gradio

- Autenticação do atendente.
- Cadastro de clientes.
- Abertura de ordens de serviço.
- Registro do computador e do problema relatado.
- Geração do número da ordem de serviço.

### Aplicativo do gerente — Streamlit

- Autenticação do gerente.
- Visualização das ordens de serviço.
- Indicadores de acompanhamento.
- Filtro por status.
- Atualização do status das ordens.
- Edição dos dados das ordens de serviço.
- Exclusão de ordens de serviço com confirmação.

## Banco de dados

O sistema utiliza PostgreSQL hospedado no Supabase.

As tabelas principais são:

- clientes
- ordens_servico
- perfis_usuarios

O controle de acesso utiliza autenticação do
Supabase e políticas de segurança (RLS).

## Configuração

1. Instalar as dependências:

   pip install -r requirements.txt

2. Criar um arquivo .env com as variáveis:

   SUPABASE_URL
   SUPABASE_KEY

3. Configurar o banco de dados e os usuários
   no Supabase.

## Execução

Aplicativo do atendente:

    python app_gradio.py

Aplicativo do gerente:

    python -m streamlit run app_streamlit.py

## Segurança

As credenciais de conexão não são armazenadas
diretamente no código-fonte.

O arquivo .env não deve ser publicado no GitHub.

## Contexto acadêmico

UNICAMP — Pós-Graduação em Data Science

Disciplina: Aplicações em Data Science

Módulo 6 — Atividade 2
