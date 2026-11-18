-- =====================================================
-- TECHFIX INFORMÁTICA
-- Atividade 2 - Aplicações em Data Science - UNICAMP
-- Banco de dados: PostgreSQL / Supabase
-- =====================================================

-- 1. TABELA DE CLIENTES

CREATE TABLE public.clientes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    endereco TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    celular_whatsapp TEXT NOT NULL,
    data_cadastro TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_email
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    CONSTRAINT chk_celular
        CHECK (celular_whatsapp ~ '^[0-9]{10,13}$')
);


-- 2. TABELA DE ORDENS DE SERVIÇO

CREATE TABLE public.ordens_servico (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    cliente_id BIGINT NOT NULL
        REFERENCES public.clientes(id)
        ON DELETE RESTRICT,

    modelo_computador TEXT NOT NULL,
    problema_relatado TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'Aberto'
        CHECK (
            status IN (
                'Aberto',
                'Em análise',
                'Aguardando peça',
                'Concluído',
                'Entregue'
            )
        ),

    data_abertura TIMESTAMPTZ DEFAULT NOW(),
    data_atualizacao TIMESTAMPTZ DEFAULT NOW()
);


-- 3. ÍNDICES PARA MELHORAR CONSULTAS

CREATE INDEX idx_os_cliente
    ON public.ordens_servico(cliente_id);

CREATE INDEX idx_os_status
    ON public.ordens_servico(status);


-- 4. TABELA DE PERFIS DOS USUÁRIOS

CREATE TABLE public.perfis_usuarios (
    usuario_id UUID PRIMARY KEY
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    perfil TEXT NOT NULL
        CHECK (perfil IN ('atendente', 'gerente')),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);


-- 5. HABILITAR SEGURANÇA POR LINHA (RLS)

ALTER TABLE public.clientes
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.ordens_servico
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.perfis_usuarios
    ENABLE ROW LEVEL SECURITY;


-- 6. FUNÇÃO PARA IDENTIFICAR O PERFIL DO USUÁRIO

CREATE OR REPLACE FUNCTION public.meu_perfil()
RETURNS TEXT
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT perfil
    FROM public.perfis_usuarios
    WHERE usuario_id = auth.uid();
$$;


-- 7. PERMISSÕES DE ACESSO À FUNÇÃO

REVOKE ALL ON FUNCTION public.meu_perfil()
    FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.meu_perfil()
    TO authenticated;


-- 8. POLÍTICAS DE ACESSO DOS GERENTES

CREATE POLICY gerente_consulta_clientes
ON public.clientes
FOR SELECT TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_insere_clientes
ON public.clientes
FOR INSERT TO authenticated
WITH CHECK ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_atualiza_clientes
ON public.clientes
FOR UPDATE TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente')
WITH CHECK ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_exclui_clientes
ON public.clientes
FOR DELETE TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente');


-- 9. POLÍTICAS DAS ORDENS DE SERVIÇO

CREATE POLICY gerente_consulta_os
ON public.ordens_servico
FOR SELECT TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_insere_os
ON public.ordens_servico
FOR INSERT TO authenticated
WITH CHECK ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_atualiza_os
ON public.ordens_servico
FOR UPDATE TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente')
WITH CHECK ((SELECT public.meu_perfil()) = 'gerente');

CREATE POLICY gerente_exclui_os
ON public.ordens_servico
FOR DELETE TO authenticated
USING ((SELECT public.meu_perfil()) = 'gerente');


-- 10. PERMISSÕES SOBRE AS TABELAS

GRANT SELECT, INSERT, UPDATE, DELETE
ON public.clientes, public.ordens_servico
TO authenticated;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA public
TO authenticated;

REVOKE ALL ON public.perfis_usuarios
FROM PUBLIC, anon, authenticated;


-- 11. FUNÇÃO PARA ABERTURA DE ORDEM DE SERVIÇO
-- Utilizada pelo aplicativo Gradio.
-- Reaproveita clientes existentes pelo e-mail.

CREATE OR REPLACE FUNCTION public.abrir_ordem_servico(
    p_nome TEXT,
    p_endereco TEXT,
    p_email TEXT,
    p_celular TEXT,
    p_modelo TEXT,
    p_problema TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_cliente_id BIGINT;
    v_os_id BIGINT;
    v_email TEXT;
BEGIN

    IF public.meu_perfil()
        NOT IN ('atendente', 'gerente')
        OR public.meu_perfil() IS NULL
    THEN
        RAISE EXCEPTION 'Usuário não autorizado';
    END IF;

    IF NULLIF(TRIM(p_nome), '') IS NULL
       OR NULLIF(TRIM(p_endereco), '') IS NULL
       OR NULLIF(TRIM(p_email), '') IS NULL
       OR NULLIF(TRIM(p_celular), '') IS NULL
       OR NULLIF(TRIM(p_modelo), '') IS NULL
       OR NULLIF(TRIM(p_problema), '') IS NULL
    THEN
        RAISE EXCEPTION 'Todos os campos são obrigatórios';
    END IF;

    v_email := LOWER(TRIM(p_email));

    SELECT id INTO v_cliente_id
    FROM public.clientes
    WHERE LOWER(email) = v_email
    LIMIT 1;

    IF v_cliente_id IS NULL THEN

        INSERT INTO public.clientes (
            nome, endereco, email, celular_whatsapp
        )
        VALUES (
            TRIM(p_nome),
            TRIM(p_endereco),
            v_email,
            TRIM(p_celular)
        )
        RETURNING id INTO v_cliente_id;

    END IF;

    INSERT INTO public.ordens_servico (
        cliente_id,
        modelo_computador,
        problema_relatado,
        status
    )
    VALUES (
        v_cliente_id,
        TRIM(p_modelo),
        TRIM(p_problema),
        'Aberto'
    )
    RETURNING id INTO v_os_id;

    RETURN v_os_id;

END;
$$;


-- 12. PERMISSÃO PARA ABERTURA DE OS

REVOKE ALL ON FUNCTION public.abrir_ordem_servico(
    TEXT, TEXT, TEXT, TEXT, TEXT, TEXT
)
FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.abrir_ordem_servico(
    TEXT, TEXT, TEXT, TEXT, TEXT, TEXT
)
TO authenticated;


-- 13. ATUALIZAÇÃO AUTOMÁTICA DA DATA DA OS

CREATE OR REPLACE FUNCTION public.atualizar_data_os()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.data_atualizacao = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_atualizar_data_os
BEFORE UPDATE ON public.ordens_servico
FOR EACH ROW
EXECUTE FUNCTION public.atualizar_data_os();


-- =====================================================
-- CONFIGURAÇÃO ADICIONAL
-- =====================================================
-- Os usuários atendente e gerente devem ser criados
-- no Supabase Authentication.
--
-- Seus UUIDs devem ser associados aos respectivos
-- perfis na tabela public.perfis_usuarios.
--
-- As senhas e chaves privadas não fazem parte
-- deste script.
--
-- Este script destina-se à criação de um banco novo.
-- Não deve ser executado novamente no banco atual.
-- =====================================================