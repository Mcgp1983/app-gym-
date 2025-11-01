# app-gym-

Aplicação FastAPI para gestão automática de um ginásio 24h com compras de planos de acesso e validação por QR Code.

## Funcionalidades

- Gestão de sócios (criação e listagem)
- Gestão de planos de adesão com duração e preço
- Compras de planos com geração de tokens únicos e QR Code
- Registo de entradas com validação em tempo real do estado do plano
- Consulta do histórico de acessos

## Requisitos

- Python 3.11+
- Ambiente virtual recomendado

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Como executar

1. Inicialize a base de dados (tabelas criadas automaticamente no primeiro arranque).
2. Inicie o servidor FastAPI com Uvicorn:

```bash
uvicorn app.main:app --reload
```

O serviço ficará disponível em `http://127.0.0.1:8000`. A documentação automática pode ser consultada em `http://127.0.0.1:8000/docs`.

## Fluxo típico

1. **Criar sócio** – `POST /members`
2. **Criar plano** – `POST /plans`
3. **Comprar plano** – `POST /purchases`
4. **Obter QR Code** – `GET /purchases/{id}/qr`
5. **Validar entrada** – `POST /access/scan`

Os QR Codes devolvidos estão codificados em base64 (imagem PNG) e podem ser exibidos em qualquer aplicação móvel.

## Testes

Execute a suite de testes automatizados com:

```bash
pytest
```

Os testes utilizam uma base de dados SQLite temporária para simular o fluxo completo desde o registo do sócio até à validação do acesso por QR Code.
