# Desafio Técnico - Hubbi Parts

Este projeto consiste em uma API de uma plataforma simplificada para o gerenciamento de peças automotivas, com funcionalidades
de busca com auxílio de RAG e interação com IA via LLM.

---

# Requisitos

- Docker
- Docker Compose


---

# Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Configure as variáveis:

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_API_KEY=TVlTRUNVUkVLRVk
```

Onde:

| Variável | Descrição |
|----------|-----------|
| GEMINI_API_KEY | Chave da API do Google Gemini |
| SECRET_API_KEY | Chave utilizada para assinatura do JWT |

---

# Executando o projeto

Na raiz do projeto:

```bash
docker compose up --build
```

Na primeira execução poderá levar alguns minutos devido ao download do modelo de embeddings.

---

Crie um superuser do Django para performar as operações que só podem ser feitas por admins:
````
docker exec -it hubbi_web make create-superuser
````

Esse comando criará o um usuário admin com as seguintes credenciais:
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "admin123",
}
```

Para avaliar a cobertura de testes, rode:
```
docker exec -it hubbi_web make test
```

# Fluxos de utilização

## Usuário comum

1. Registrar usuário

```http
POST /auth/register
```

2. Autenticar

```http
POST /token
```

3. Consultar peças

```http
GET /parts
```

---

## Administrador

1. Autenticar utilizando o superusuário

```http
POST /token
```

2. Utilizar o CRUD completo

```text
/parts
```

---

## Cliente externo

1. Criar API Key

```http
POST /api-keys
```

2. Recuperar a chave

```http
GET /api-keys/{id}
```

3. Enviar CSV

```http
POST /external/csv-uploads
```

---

## Atualização em lote

```http
POST /external/inventory/update
```

---

# Modelagem

## Parts

Representa uma peça automotiva.

Possui informações como:

- nome
- descrição
- preço
- quantidade
- embedding vetorial

Operações:

- criação
- edição
- exclusão
- listagem
- importação via CSV

---

## API Keys

Representa clientes integrados.

Características:

- geração automática da chave
- habilitar/desabilitar
- autenticação via header

---

## Integration Logs

Responsável por registrar todas as chamadas realizadas por clientes externos.

Objetivos:

- auditoria
- métricas
- rastreabilidade

---
