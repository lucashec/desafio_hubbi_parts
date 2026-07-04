# Desafio Técnico - Hubbi Parts

Este projeto consiste em uma API de uma plataforma simplificada para o gerenciamento de peças automotivas, com funcionalidades
de busca com auxílio de RAG e interação com IA via LLM.

## Setup
Para rodar o projeto utilize o docker, que subirá toda a infraestrutura necessária (Postgres, Redis, API com Django REST e Celery).

<h4> Variáveis de Ambiente </h4>
Todo a configuração declarada no .env.example pode ser copiada para o .env, necessitando apenas de uma chave para a API do Gemini e uma secret key para a assinatura do JWT.

```
GEMINI_API_KEY=your_gemini_secret_here
SECRET_API_KEY=TVlTRUNVUkVLRVk (exemplo em base64) 
```

<b>Por se tratar de um projeto com dependência de modelos de IA, a imagem final possui cerca de 9GB, é necessário ter esse espaço disponível em disco para um build correto.</b>


Entre no diretório raiz e rode:
```
docker compose up
```

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

## Teste de Requests
Há duas alternativas para testar requests, a primeira é via Swagger gerado pela própria API, a segunda é via extensão REST Client do VSCode. O arquivo de referência para utilização no VSCode está disponível na raiz do projeto como <b>test_request.http</b>.

Caso opte pelo Swagger, ele estará disponível no endpoint:
```
http://localhost:8000/api/docs/#/
```

Para autenticar com JWT ou X_API_KEY, utilize o botão Authorize, disponível no canto superior direito.

## Modelagem

### Integrations - Api Key
Entidade que modela o registro de integração de clientes via API Key. A chave é gerada através de uma função randômica na api. Sendo retornada no GET da entidade.
Além disso, é possível desabilitar ou habilitar uma chave.

### Integrations - Integration Log
Entidade que registra toda a atividade do cliente integrado via API Key. Para métricas e/ou auditoria posterior.

### Parts
Modela uma peça, que pode ser criada, listada, alterada e removida via arquivo csv ou endpoint.

