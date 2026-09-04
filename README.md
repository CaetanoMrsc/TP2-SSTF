# SystemInfo

Aplicação Python 3 executada automaticamente no Buildroot.

## Execução

Após o boot do sistema, o servidor é iniciado automaticamente na porta 8080.

Endpoint:

    http://192.168.1.10:8080/status

## Informações retornadas

O endpoint `/status` retorna um JSON com:

- `datetime`: data e hora do sistema.
- `uptime_seconds`: tempo de funcionamento do sistema.
- `cpu.model`: modelo do processador.
- `cpu.speed_mhz`: frequência do processador.
- `cpu.usage_percent`: percentual de uso da CPU.
- `memory.total_mb`: memória total.
- `memory.used_mb`: memória utilizada.
- `os_version`: versão do sistema operacional.
- `processes`: PID e nome dos processos em execução.
- `disks`: dispositivos de armazenamento e seus tamanhos.
- `usb_devices`: dispositivos USB detectados.
- `network_adapters`: interfaces de rede e seus endereços IP.

## Origem das informações

As informações são obtidas diretamente dos sistemas de arquivos virtuais do Linux:

| Informação | Fonte |
|---|---|
| Data/hora | `/proc/stat` e `/proc/uptime` |
| Uptime | `/proc/uptime` |
| CPU | `/proc/cpuinfo` e `/proc/stat` |
| Memória | `/proc/meminfo` |
| Sistema operacional | `/proc/version` |
| Processos | `/proc/<pid>/comm` |
| Discos | `/sys/block/<device>/size` |
| USB | `/sys/bus/usb/devices/` |
| Rede | `/sys/class/net`, `/proc/net/fib_trie` e `/proc/net/route` |

Os dados são coletados novamente a cada requisição ao endpoint `/status`.

## Resposta HTTP

A aplicação retorna:

- `200 OK` para `/status`, com conteúdo JSON.
- `404 Not Found` para outras URLs.
