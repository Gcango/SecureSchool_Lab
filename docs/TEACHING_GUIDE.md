# Guia pedagógico — mapa de laboratórios

## Princípio de utilização

A aplicação fornecida está **segura por omissão**. Antes de cada experiência, crie uma branch Git ou uma cópia. Introduza apenas **uma alteração vulnerável de cada vez**, sempre em localhost e com dados fictícios.

## Mapa por tópico

| Tópico | Zona do projeto | Controlo presente na base | Questão para os alunos |
|---|---|---|---|
| SQL Injection | `login()` em `app.py` | query parametrizada | O que mudaria se o input fosse concatenado na string SQL? |
| Passwords | `db.py` + `login()` | hash e verificação segura | O que aconteceria se a password estivesse em texto simples? |
| XSS | `/comments` + `comments.html` | autoescaping Jinja | O browser apresenta o comentário como texto ou código? |
| Broken Access Control / IDOR | `/students/<id>` | verificação do proprietário/role | Um aluno consegue alterar o ID e ver outro perfil? |
| Upload inseguro | `/uploads` | allowlist + UUID + fora de static | Que risco aparece ao aceitar qualquer extensão? |
| Security Misconfiguration | arranque + headers | debug off + headers | Que informação poderia aparecer se debug estivesse ativo? |
| Sessões | `Config` | expiração a 15 min | O que acontece num PC deixado sem supervisão? |
| CSRF | formulários POST | token de sessão | Porque não basta saber o URL de uma ação? |
| Logging | `audit_logs` | ações principais registadas | Que eventos devem ser auditáveis? |
| Dependências | `requirements.txt` | versão explícita | Como verificar vulnerabilidades conhecidas nas dependências? |

## Estrutura das aulas práticas

**1. Observar** — mostrar o comportamento atual.  
**2. Formular hipótese** — “Que controlo está a impedir o abuso?”  
**3. Alterar de forma controlada** — professor introduz a falha.  
**4. Testar** — alunos verificam a consequência no laboratório local.  
**5. Corrigir** — repor o controlo.  
**6. Explicar** — preencher Ativo/Ameaça/Vulnerabilidade/Impacto/Controlo.  
**7. Retestar** — confirmar que a correção funciona.

## Importante

Não transformar a versão vulnerável numa aplicação pública. O objetivo é compreender decisões de desenvolvimento seguro, não testar sistemas de terceiros.
