# Monkey Typing — Cross-Read PTY Validado (macOS)

**Data da validação:** 2026-09-04
**Host:** Miami2-5.local
**Kernel:** 21.6.0
**Arquitetura:** x86_64
**Ambiente:** macOS

---

## Objetivo

Validar se a injeção de caracteres via `write(2)` no **mestre** de um PTY funciona em macOS, e se um processo **worker** consegue ler os dados injetados no **slave** do mesmo PTY — completando o caminho cross-read necessário para o Monkey Typing.

---

## Arquivo executado

- `pty_cross_test_v2.py` (98 linhas, 3319 bytes)

### O que o script faz

1. Abre um PTY real via `pty.openpty()` → retorna **mestre** e **slave** (com path como `/dev/ttysNNN`).
2. Inicia um **processo worker** via `multiprocessing.Process`, passando apenas o **caminho do slave** (ex: `/dev/ttys003`).
3. O worker **re-abre** o slave por path com `os.open(path, O_RDONLY | O_NONBLOCK)` — evita o problema de fd herdado via `fork` que causou falha no teste anterior (`pty_cross_test.py`).
4. Após 0.5s, o processo principal injeta uma string de teste no **mestre** via `os.write(master_fd, b"MONKEY_TEST_STRING_12345\n")`.
5. O worker faz `select` + `read` no slave até encontrar o `TEST_MESSAGE` ou timeout.
6. Verifica se o worker leu a string corretamente.

### String de teste

```
MONKEY_TEST_STRING_12345
```

---

## Resultado obtido

```
=== Teste PTY v2: worker re-abre slave por caminho ===
kernel=21.6.0, arch=x86_64, pid=83094
stderr é tty: False
pty.openpty() OK: master_fd=3, slave_fd=4, slave=/dev/ttys003
[worker] iniciando processo que re-abre o slave por caminho...
[worker] abrindo slave por caminho: /dev/ttys003
[worker] slave aberto: fd=5
[worker] lido 25 bytes, total 25: b'MONKEY_TEST_STRING_12345\n'
[worker] ACHOU TEST_MESSAGE no slave!
[worker] FIM: total lido=25, buf=b'MONKEY_TEST_STRING_12345\n'
[worker] fd=5 fechado
[inj] injetando 25 bytes no mestre via write(2)...
[inj] write() OK: 25 bytes escritos no fd=3
[rd] worker terminado com exitcode=0
[cl] descritores fechados
RESULTADO FINAL:
  Se worker leu TEST_MESSAGE no slave -> injeção via write(2) no mestre FUNCIONOU com worker que re-abre slave por caminho.
  Se worker não leu -> problema persiste mesmo com re-abertura por caminho.
exit_code=0
```

**Resultado: sucesso — cross-read validado.**

- Injeção via `write(2)` no master: OK (25 bytes escritos no fd=3).
- Worker re-abriu slave por path: OK (`/dev/ttys003`, fd=5).
- Worker leu e confirmou a string de teste: `b'MONKEY_TEST_STRING_12345\n'` (25 bytes).
- Worker terminou com `exitcode=0`.

---

## Caminho anterior (falha / insuficiente)

### `pty_cross_test.py` (versão 1 — fd herdado)

- Usou `multiprocessing.Process` passando o **fd** do slave diretamente (herança via fork).
- Resultado: `write()` no master OK, mas o worker **não leu** antes do timeout e foi terminado (exitcode -15 / SIGTERM).
- **Hipótese confirmada pela versão 2:** o problema era a herança do fd via fork em macOS — re-abrir o slave por path resolveu o cross-read.

### `pty_test.py`

- `pty.openpty()` OK, mas `os.write()` falhou com `OSError: [Errno 5] Input/output error` (EIO) porque o slave_fd foi fechado logo após a descoberta do path (`os.ttyname`).
- Serviu para isolar o problema: o EIO era causado pelo fechamento prematuro do slave, não por falha na injeção.

### `openpty_tester.sh`

- Falhou com `OSError: [Errno 34] Result too large` — alocação de PTY não disponível naquele contexto.
- Posteriormente, `pty.openpty()` funcionou em `pty_test.py` e em ambos os `pty_cross_test*.py` em `/dev/ttys003` e `/dev/ttys004`.

---

## Conclusão da validação

1. **Injeção via `write(2)` no PTY master funciona em macOS** neste host.
2. **Worker que re-abre o slave por path consegue ler os dados injetados** — o cross-read está validado.
3. A abordagem do Monkey Typing (injeção crua via `write(2)`, bypass de stdio/line discipline, `/dev/shm` para coordenação) é **viável no ambiente macOS deste host**.
4. O heap de shm (`/monkey_shm`, 4096 bytes) já foi validado separadamente: `monkey` cria shm com status (`status:running, fd:3, delay:50000us`) e `monkey_ctrl` lê com sucesso.
5. **Integração monkey.c + PTY real: CONCLUÍDA em 2026-09-04T15:09:48Z.** O `monkey.c` (auto-contido, openpty() via `<util.h>` macOS) injeta com sucesso TEST_MESSAGE no mestre; o worker cross-read re-abre o slave por path (via `ttyname(slave_fd)` + shm) e confirma a leitura em `/dev/ttys004` — exit 0, TEST_MESSAGE encontrado. Validação completa via `test_monkey_pty_integration.py` + `run_monkey_validation.sh` (exit 0, log salvo em `/Users/miami2/zion.app/automation/logs/monkey_validation_20260904_150948.log`).

---

## Próximos passos

### 1. Documentar (feito — este arquivo)

Registrar o resultado validado para referência futura.

### 2. Integração `monkey.c` com PTY real (FEITO — 2026-09-04)

O `monkey.c` (176 linhas, 5670 bytes) foi atualizado para ser auto-contido:
- Usa `openpty()` via `<util.h>` no macOS (sem depender de `/dev/null`).
- `shm_unlink` antes do `shm_open` para garantir shm limpo.
- `ttyname(slave_fd)` para fallback quando o path não é exposto diretamente.
- `shm_write_status` separado preserva a linha `slave=...` inicial.

O worker cross-read re-abre o slave pelo path lido do shm via `monkey_ctrl`. TEST_MESSAGE = `b"MONKEY_INTEGRATION_TEST_STRING_12345\n"`. Delay 200000µs, worker timeout 5s. Validação: `test_monkey_pty_integration.py` (monkey auto-contido + worker cross-read em `/dev/ttys004`, exit 0, TEST_MESSAGE encontrado) + `run_monkey_validation.sh` (exit 0, log em `/Users/miami2/zion.app/automation/logs/monkey_validation_20260904_150948.log`).

### 3. Definir alvo PTY + consumer para teste (FEITO — 2026-09-04)

O próprio `monkey.c` agora cria o PTY via `openpty()` e atua como injetor; o worker cross-read validado em `pty_cross_test_v2.py` e integrado via `test_monkey_pty_integration.py` consume os dados injetados. Nenhuma ação adicional de criação de PTY external é necessária — o pipeline monkey.c → shm → worker cross-read está operante.

---

## Arquivos relacionados

- `monkey.c` — injetor via `write(2)` + shm (compilado em `monkey`)
- `monkey_ctrl.c` — controlador shm (compilado em `monkey_ctrl`)
- `pty_cross_test.py` — versão 1 (fd herdado — cross-read não validado)
- `pty_cross_test_v2.py` — versão 2 (re-abertura por path — cross-read validado)
- `pty_test.py` — teste preliminar (EIO por fechamento prematuro)

---

**Status:** cross-read validado ✅ — integração monkey.c + PTY real concluída ✅ (2026-09-04). Pipeline monkey.c → /dev/shm → worker cross-read operante: monkey injeta via write(2) no master, worker re-abre slave por path (shm + ttyname), TEST_MESSAGE confirmado em /dev/ttys004, exit 0.
