[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/Vc7tL63f)
# Projeto de Protocolos

## Membros

<a href="https://github.com/andreyadriano">
    <img style="border-radius: 50%;" src="https://avatars.githubusercontent.com/u/55251806?v=4" width="100px;" alt=""/><br />
    <sub><b>Andrey Adriano da Rosa</b></sub></a><br />

&nbsp;

<a href="https://github.com/faustocristiano">
    <img style="border-radius: 50%;" src="https://avatars.githubusercontent.com/u/86061017?v=4" width="100px;" alt=""/><br />
    <sub><b>Fausto Cristiano</b></sub></a><br />

&nbsp;

<a href="https://github.com/lucascraupp">
    <img style="border-radius: 50%;" src="https://avatars.githubusercontent.com/u/86060864?v=4" width="100px;" alt=""/><br />
    <sub><b>Lucas Coelho Raupp</b></sub></a><br />

&nbsp;

Esse repositório contém a implementação de um protocolo real da disciplina Projeto de Protocolos (PTC029008).

## Especificação do protocolo TFTP2

### Serviço

O TFTP é um protocolo simples para transferência de arquivos, entre hosts em diferentes redes. Ele possui o serviço de leitura e gravação de arquivos de/para um servidor remoto. A versão 2 do protocolo permite a listagem de diretórios e arquivos do servidor, além da criação de diretórios e renomeação/remoção de arquivos.

### Vocabulário e Regras de Procedimento

#### RRQ: Read Request

Formato do pacote (é o mesmo para o WRQ):

    2 bytes | string   | 1 byte | string | 1 byte
    Opcode  | Filename |    0   |  Mode  |   0

O cliente envia uma solicitação de leitura de arquivo para o servidor. O servidor responde com um pacote de dados contendo o arquivo solicitado.

#### WRQ: Write Request

O cliente envia uma solicitação de escrita de arquivo para o servidor. O servidor responde com um ACK para que o cliente inicie a transferência do arquivo.

#### DATA: Dados

Formato do pacote:

    2 bytes | 2 bytes  | n bytes
    Opcode  | Block #  |  Data

É o pacote de dados transferido entre o cliente e o servidor nas operações de leitura e escrita. O pacote deve conter no máximo 512 bytes de dados. Caso o arquivo exceda este tamanho, múltiplos pacotes devem ser enviados até que a transferência se complete.

#### ACK: Acknowledgement

Formato do pacote:

    2 bytes | 2 bytes
    Opcode  | Block #

O pacote de ACK é enviado confirmando a recepção de uma mensagem. O campo Block # deve conter o número do bloco recebido.

#### ERROR: Erro

Formato do pacote:

    2 bytes |  2 bytes  | string | 1 byte   
    Opcode  | ErrorCode | ErrMsg |   0  

O pacote de erro é enviado pelo servidor quando ocorre algum erro durante alguma operação. O campo ErrorCode deve conter o código do erro e ErrMsg deve conter uma mensagem de erro.

#### LIST: Listar diretórios e arquivos

O cliente solicita ao servidor a listagem de diretórios e arquivos em um determinado diretório. O servidor responde com um pacote de dados contendo a listagem no seguinte formato:

    list_resp {
        items {
            file {
                nome: "nomeArquivo"
                tamanho: 1234
            }
        }
        items {
            dir {
                path: "nomeDiretorio"
            }
        }
    }

#### MKDIR: Criar diretórios

O cliente solicita ao servidor que crie um diretório no caminho especificado. O servidor verifica se o diretório já existe. Se não exisir, ele cria. Se existir, ele retorna um erro.

#### MOVE: Renomear/Remover arquivo

O cliente pode escolher renomear ou remover o arquivo. Se o cliente enviar dois nomes, o arquivo será renomeado, se enviar apenas um, o arquivo será apagado. O servidor verifica e retorna um erro se o arquivo original existe ou se já existe um arquivo com o novo nome.

## Máquina de Estados (TFTP 1)

### Cliente

![TFTP](./Documentação/Cliente.png)

### Servidor

![TFTP](./Documentação/Servidor.png)

## Diagrama de Classes (TFTP 2)

### Cliente

```mermaid
classDiagram
  class Cliente {
    - __ip: str
    - __timeoutGeral: int
    - __porta: int
    - __operacao: str
    - __nomeArq: str
    - __novoNome: str
    - __modo: str
    - __timeout: int
    - __tratador: function
    - __socket: socket
    - __estado: function
    
    + __init__(ip: str, porta: int, operacao: str, nomeArq: str, novoNome: str)
    + rrq() void
    + wrq() void
    + handle_LEITURA(data: Data) void
    + handle_RECEBENDO(data: Data) void
    + handle_ESCRITA(ack: Ack) void
    + handle_TRANSMITINDO(ack: Ack) void
    + handle_ULTIMO_TX(mensagem: (Ack, Error)) void
    + handle_FIM(mensagem: (Ack, Error)) void
    + list() void
    + mkdir() void
    + move() void
    + handle_NOVO(mensagem: bytes) void
    + handle_PADRAO(mensagem: bytes) void
    + handle_INICIO() void
    + handle() void
    + handle_timeout() void
  }

  class Ack {
    - __block: int
    - __op: int
    + __init__(block: int)
    + get_opcode() int
    + get_block() int
    + monta_cabecalho() bytes
    + desmembra_cabecalho(cabecalho: bytes) void
  }

  class Data {
    - __block: int
    - __data: bytes
    - __op: int
    + __init__(block: int, data: bytes)
    + get_block() int
    + get_data() bytes
    + desmembra_cabecalho(cabecalho: bytes) void
    + monta_cabecalho() bytes
  }

  class Error {
    - __codigos_erro: int[]
    - __op: int
    - __errorCode: int
    - __errMsg: string
    + __init__()
    + desmembra_cabecalho(cabecalho: bytearray) void
    + retorna_erro() : (int, string)
    + get_opcode() int
    }

  class RrqWrq {
    - __op: int
    - __file: string
    - __mode: string
    + __init__(op: int, file: string, mode: string)
    + monta_cabecalho() bytearray
    }

  class tftp2_Mensagem {
    + ack: tftp2_ACK
    + error: tftp2_Error
    + list: tftp2_Path
    + list_resp: tftp2_ListResponse
    + mkdir: tftp2_Path
    + move: tftp2_MOVE
    +
  }

  class tftp2_ACK {
    - block_n: int
  }

  class tftp2_Error {
    - errorcode: str
  }

  class tftp2_Path {
    - path: string
  }

  class tftp2_ListResponse {
    - file: tftp2_FILE
    - dir: tftp2_Path
  }

  class tftp2_FILE {
    - nome: string
    - tamanho: int
  }

  class tftp2_MOVE {
    - nome_orig: string
    - nome_novo: string
  }

Cliente *-- Ack
Cliente *-- Data
Cliente *-- Error
Cliente *-- RrqWrq
Cliente *-- tftp2_Mensagem

tftp2_Mensagem *-- tftp2_ACK
tftp2_Mensagem *-- tftp2_Error
tftp2_Mensagem *-- tftp2_Path
tftp2_Mensagem *-- tftp2_ListResponse
tftp2_Mensagem *-- tftp2_MOVE
tftp2_ListResponse *-- tftp2_FILE

```

### Servidor

```mermaid
classDiagram
    class Servidor {
    - __diretorio: str
    - __ip: str
    - __porta: int
    - __n: int
    - __timeout: int
    - __timeoutGeral: int
    - __socket: socket
    - __nova_mensagem : str
    + __init__(diretorio: str, porta: int)
    + handle_ULTIMO_TX(mensagem: Ack) void
    + handle_TRANSMITINDO(mensagem: Ack) void
    + handle_RECEBENDO(mensagem: Data) void
    + handle_ESPERA(mensagem: bytes) void
    + handle_LIST() void
    + handle_MKDIR() void
    + handle_MOVE() void
    + handle() void
    + handle_timeout() void
  }

  class Ack {
    - __block: int
    - __op: int
    + __init__(block: int)
    + get_opcode() int
    + get_block() int
    + monta_cabecalho() bytes
    + desmembra_cabecalho(cabecalho: bytes) void
  }

  class Data {
    - __block: int
    - __data: bytes
    - __op: int
    + __init__(block: int, data: bytes)
    + get_block() int
    + get_data() bytes
    + desmembra_cabecalho(cabecalho: bytes) void
    + monta_cabecalho() bytes
  }

  class Error {
    - __codigos_erro: int[]
    - __op: int
    - __errorCode: int
    - __errMsg: string
    + __init__()
    + desmembra_cabecalho(cabecalho: bytearray) void
    + retorna_erro() : (int, string)
    + get_opcode() int
    }

  class RrqWrq {
    - __op: int
    - __filename: string
    + desmembra_cabecalho(cabecalho: bytearray): void
    + get_opcode(): int
    + get_filename(): string
  }

  class tftp2_Mensagem {
    + ack: tftp2_ACK
    + error: tftp2_Error
    + list: tftp2_Path
    + list_resp: tftp2_ListResponse
    + mkdir: tftp2_Path
    + move: tftp2_MOVE
    +
  }

  class tftp2_ACK {
    - block_n: int
  }

  class tftp2_Error {
    - errorcode: str
  }

  class tftp2_Path {
    - path: string
  }

  class tftp2_ListResponse {
    - file: tftp2_FILE
    - dir: tftp2_Path
  }

  class tftp2_FILE {
    - nome: string
    - tamanho: int
  }

  class tftp2_MOVE {
    - nome_orig: string
    - nome_novo: string
  }

Servidor *-- Ack
Servidor *-- Data
Servidor *-- Error
Servidor *-- RrqWrq
Servidor *-- tftp2_Mensagem

tftp2_Mensagem *-- tftp2_ACK
tftp2_Mensagem *-- tftp2_Error
tftp2_Mensagem *-- tftp2_Path
tftp2_Mensagem *-- tftp2_ListResponse
tftp2_Mensagem *-- tftp2_MOVE
tftp2_ListResponse *-- tftp2_FILE
```

## Como executar

### Servidor

Para executar o servidor, entre na pasta `Servidor` e execute o comando:

    python3 servidor.py <caminhoAbsoluto> <Porta>
    Exemplo: python3 servidor.py /home/aluno/tftp/Servidor 6969

### Cliente

Para executar o cliente, entre na pasta `Cliente` e execute o comando de acordo com a operação desejada:

#### Solicitação de arquivo do servidor (RRQ):

    python3 cliente.py <IP> <Porta> rrq <nomeArquivo>
    Exemplo: python3 cliente.py 127.0.0.1 6969 rrq Lusíadas.pdf

#### Solicitação de transferência de arquivo pro servidor (WRQ):

    python3 cliente.py <IP> <Porta> wrq <nomeArquivo>
    Exemplo: python3 cliente.py 127.0.0.1 6969 wrq teste.txt

#### Listar diretórios e arquivos (LIST)

    python3 cliente.py <IP> <Porta> list <caminho>
    Exemplo: python3 cliente.py 127.0.0.1 6969 list ./

#### Criar diretórios (MKDIR)

    python3 cliente.py <IP> <Porta> mkdir <nomeDiretorio>
    Exemplo: python3 cliente.py 127.0.0.1 6969 mkdir teste

É possível criar diretórios aninhados, basta passar o caminho absoluto do diretório desejado (exemplo "teste1/teste2/teste3")

#### Renomear/Remover arquivo (MOVE)

Renomear arquivo:

    python3 cliente.py <IP> <Porta> move <nomeArquivo> <novoNomeArquivo>
    Exemplo: cliente.py 127.0.0.1 6969 move teste.txt teste2.txt

Remover arquivo:
    
    python3 cliente.py <IP> <Porta> move <nomeArquivo>
    Exemplo: cliente.py 127.0.0.1 6969 move teste.txt
