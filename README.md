# SecureSchool Lab

Projeto pedagógico para a **UFCD 10795 — Segurança no Desenvolvimento de Software** (12.º ano, Técnico/a de Desenvolvimento de Software — Nível IV).

O projeto é uma pequena plataforma escolar, deliberadamente simples, criada para permitir ao professor demonstrar **boas práticas primeiro** e, depois, introduzir vulnerabilidades isoladas em ambiente local para comparação **Vulnerável → Corrigir → Testar novamente**.

> **Regra de segurança:** execute apenas em `127.0.0.1`/localhost, com dados fictícios. Não publique uma versão deliberadamente vulnerável na Internet ou na rede escolar.

## Funcionalidades incluídas

- login/logout e sessões com expiração;
- três funções: `student`, `teacher`, `admin`;
- perfil de aluno e controlo de acesso por ID;
- consulta e registo de avaliações;
- comentários (úteis para o laboratório de XSS);
- upload/download de trabalhos;
- área de professor;
- área administrativa;
- logs de auditoria;
- queries SQLite parametrizadas;
- hashes de passwords com Werkzeug;
- CSRF básico por token de sessão;
- headers de segurança e CSP;
- debug desativado;
- uploads com allowlist, limite de tamanho, UUID e armazenamento fora de `static/`.

## 1. Abrir no VS Code

Abra a pasta `SecureSchool_Lab`.

## 2. Criar ambiente virtual

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Executar

```bash
python app.py
```

Na primeira execução, a base de dados de demonstração é criada automaticamente.

Abra: `http://127.0.0.1:5000`

## Contas de demonstração

| Perfil | Utilizador | Palavra-passe |
|---|---|---|
| Aluno | `ana` | `AlunoAna!2026` |
| Aluno | `joao` | `AlunoJoao!2026` |
| Professor | `prof1` | `Professor!2026` |
| Administrador | `admin` | `Admin!2026Lab` |

Estas credenciais são **apenas para este laboratório local**.

## Repor a base de dados

```bash
python init_db.py
```

Isto apaga a base local e recria todos os dados fictícios.

## Percurso pedagógico sugerido

1. Executar a aplicação segura e compreender a arquitetura.
2. Mapear: **Ativo → Ameaça → Vulnerabilidade → Impacto → Controlo**.
3. Criar uma cópia/branch antes de cada experiência.
4. Introduzir uma única fraqueza de cada vez.
5. Demonstrar o efeito em localhost.
6. Restaurar a versão segura e justificar o controlo.
7. Registar a descoberta num pequeno relatório de segurança.

Consulte `docs/TEACHING_GUIDE.md` para o mapa dos laboratórios.
