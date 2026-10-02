# Trabalho Prático 2 — Escalonador SSTF

## GrupoF

Integrantes:
- Caetano Marasca
- João Francisco Schnur Dallanora
- Luiz Augusto Guerra

## Descrição

Implementação de um escalonador de E/S de disco baseado no algoritmo
SSTF (Shortest Seek Time First) para o Linux kernel 4.13.9.

## Código-fonte

O código principal está em:

- `modules/sstf/sstf-iosched.c` — módulo do escalonador SSTF
- `modules/sstf/sector_read.c` — gerador de requisições de leitura
- `modules/sstf/Makefile` — compilação e integração com a distribuição

## Compilação

A partir do diretório `linuxdistro`:

```bash
cd modules/sstf
make
