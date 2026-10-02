# Desafio Técnico - AI Engineer Artefact
## Agente de Atendimento — Empório da Música

Protótipo de um agente de atendimento para uma loja fictícia de instrumentos
musicais Empório da Música. O agente responde perguntas sobre catálogo, preços, estoque, promoções,
pedidos e políticas da loja usando apenas modelos locais.

O projeto foi desenvolvido em Python com LangChain e Ollama.

## Funcionalidades

- busca produtos por nome, marca, categoria, preço e disponibilidade;
- consulta preço, estoque, especificações e promoções de um produto;
- consulta pedidos após validar o número do pedido e o e-mail do cliente;
- responde perguntas sobre trocas, devoluções, pagamentos, horários, endereço e
  entregas usando RAG sobre o manual de políticas;
- mantém o contexto da conversa enquanto a aplicação está aberta;
- recusa educadamente perguntas fora do escopo da loja.

## Decisões técnicas

| Decisão | Escolha | Justificativa |
|---|---|---|
| Framework/abordagem do agente | LangChain | Fornece tools, agente, histórico em memória e integração com Ollama. |
| Modelo de chat | `llama3.1:8b` | Modelo local, gratuito e com suporte a chamadas de tools. |
| Provedor | Ollama | Permite executar o modelo e os embeddings localmente. |
| Modelo de embeddings | `embeddinggemma` | Modelo pequeno e local adequado para recuperação semântica em português. |
| Dados estruturados | CSVs em memória | Por simplicidade, dado que o volume de dados é pequeno, o projeto mantém os CSVs em memória. Os CSVs são lidos com `csv.DictReader` e armazenados em cache durante a execução. As tools fazem as junções necessárias em memória.|
| Abordagem do agente para política da loja | RAG em memória | Mantém as respostas fundamentadas no PDF na cache sem adicionar banco vetorial persistente. |
| Interface de interação| CLI | É simples, mas suficiente para demonstrar o funcionamento do agente com pouca complexidade. |
| Histórico de conversa| `InMemorySaver` | Mantém o contexto durante a sessão sem exigir persistência externa. |

### RAG das políticas

O arquivo `data/politicas_da_loja.pdf` é processado apenas na primeira pergunta sobre políticas de cada execução:

1. o texto é extraído com `pypdf`;
2. espaços e quebras de linha são normalizados;
3. o texto é dividido em chunks de 800 caracteres, com sobreposição de 120;
4. os embeddings são gerados pelo `embeddinggemma`;
5. os vetores são mantidos em `InMemoryVectorStore`;
6. os quatro trechos mais relacionados à pergunta são enviados ao agente.

### Estratégia de prompt

O prompt de sistema define o agente como atendente do Empório da Música e exige
que ele:

- consulte as tools para preços, estoque, pedidos e políticas;
- não invente informações;
- solicite número e e-mail antes de consultar um pedido;
- não exponha dados pessoais nem detalhes internos da implementação;
- responda em português; 
- recuse assuntos fora do escopo da loja.

## Pré Requisitos

- Python 3.11 ou superior;
- [Ollama](https://ollama.com/) instalado e em execução;
- aproximadamente 6 GB livres para os modelos locais.

O projeto foi desenvolvido e testado com Python 3.14.5.

## Instalação
Após garantir os pré requisitos, comece a instalação. 

Clone o repositório e entre na pasta:

```bash
git clone https://github.com/g-abilio/desafio-artefact.git
cd desafio-artefact
```

Crie e ative o ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows, a ativação pode ser feita com:

```powershell
.venv\Scripts\activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Baixe os modelos usados pelo projeto:

```bash
ollama pull llama3.1:8b
ollama pull embeddinggemma
```

Confira se eles estão disponíveis:

```bash
ollama list
```

Se o comando não conseguir se conectar ao Ollama, inicie o serviço:

```bash
ollama serve
```

## Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Variáveis disponíveis:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=embeddinggemma
DATA_DIR=data
POLICIES_PATH=data/politicas_da_loja.pdf
```

Os valores padrão já funcionam para uma instalação local do Ollama.

## Execução

Com o Ollama em execução e o ambiente virtual ativado:

```bash
python main.py
```

Use `sair` para encerrar. 

## Testes

Execute a suíte a partir da raiz do projeto:

```bash
python -m pytest -q
```

## Exemplos de interação

### 1. Consulta de produto

```text
Usuário: Quanto custa o Takamine GD20?
Assistente: O preço do Takamine GD20 é de R$ 2.199,00.
```

### 2. Consulta de política

```text
Usuário: Fiz uma compra e me arrependi. Eu posso devolver?
Assistente: Lamento ouvir que você se arrependeu da compra. De acordo com nossas políticas de trocas e devoluções, você tem direito a devolver o produto em até 7 dias corridos após o recebimento, sem necessidade de justificativa. O produto deve estar em sua embalagem original, sem sinais de uso, com todos os acessórios e manuais.
 
Para iniciar o processo de devolução, por favor entre em contato conosco pelo telefone ou e-mail, fornecendo o número do pedido e o produto que deseja devolver. Nós iremos orientá-lo sobre os próximos passos e garantir que o processo seja realizado de forma eficiente e transparente.
 
Lembre-se de que o frete de devolução é por conta da loja em caso de arrependimento. Além disso, é importante verificar se o produto ainda está dentro do prazo de devolução e se atende às condições estabelecidas em nossa política de devoluções.
 
Se tiver alguma dúvida ou precisar de mais informações, por favor não hesite em entrar em contato conosco. Estamos aqui para ajudar!

```

### 3. Consulta de pedido

```text
Usuário: Qual é o status do pedido 1? Meu e-mail é pedro.oliveira@jmail.com.
Assistente: O status do seu pedido 1 é "delivered". O seu pedido foi entregue no dia 25/10/2025. O valor total do pedido foi de R$ 11.499,00, pago pelo método Pix. O código de rastreamento da entrega é BRAB1234567BR.
```

### 4. Pergunta fora do escopo

```text
Usuário: Qual é a previsão do tempo para amanhã?
Assistente: Desculpe, mas não posso fornecer informações sobre a previsão do tempo. Posso ajudar com alguma outra coisa?
```

## Estrutura do projeto

```text
.
├── app/
│   ├── agent.py          # configuração do agente e prompt de sistema
│   ├── config.py         # variáveis de ambiente
│   ├── data_store.py     # leitura e cache dos CSVs
│   ├── rag.py            # recuperação das políticas do PDF
│   └── tools.py          # tools disponibilizadas ao agente
├── data/                 # CSVs e manual de políticas
├── tests/                # testes automatizados
├── main.py               # CLI
├── requirements.txt
└── .env.example
```

## Limitações e possíveis melhorias com mais tempo

- A suíte de testes ainda é pouco abrangente. Com mais tempo, o ideal seria ampliar os testes das tools, do RAG e das conversas em múltiplos turnos, cobrindo também seleção de ferramentas, argumentos incorretos e perguntas fora do escopo;
- O sistema atual não funciona bem com pequenas diferenças de escrita. Com mais tempo, um grande avanço seria melhorar a busca do catálogo com sinônimos, tolerância às pequenas diferenças
  de escrita citadas, além de ordenação dos resultados por relevância;
- Com mais tempo, uma melhoria seria avaliar diferentes tamanhos de chunk, sobreposição e quantidade de documentos recuperados para melhorar a precisão do RAG sobre o mesmo PDF;
- Existem informações conflitantes no manual, como os números de WhatsApp divergentes. Com mais tempo, tratar esses conflitos seria interessante, informando a ambiguidade em vez de escolher um valor;
- O assistente atual demora um certo tempo para responder às perguntas. Com mais tempo, seria interessante testar outros modelos locais e também modelos acessados via API, comparando a velocidade das respostas, a qualidade do atendimento e o desempenho na seleção e no uso das tools, visando uma interação mais rápida e eficiente;
- Com mais tempo, para melhorar as condições de manutenção e desenvolvimento do assistente, adicionar logs locais para facilitar a investigação de falhas sem expor detalhes técnicos ao cliente poderia melhorar a qualidade do sistema.

## Uso de assistente de código

Durante o projeto, utilizei o Codex como apoio ao desenvolvimento, principalmente para explorar alternativas de arquitetura, simplificar a implementação da leitura dos CSVs e do pipeline de RAG, acelerar implementações pontuais das tools, investigar erros de importação e tipagem, revisar o código, auxiliar na criação de documentação e sugerir casos de teste.

Meu workflow foi iterativo: primeiro entendia e decompunha cada etapa do desafio e, em seguida, utilizava o Codex em tarefas bem delimitadas. As sugestões eram revisadas, adaptadas ao escopo do projeto e validadas por mim por meio de testes e análise de casos de borda, como produtos sem estoque, promoções, pedidos com e-mail incorreto e consultas às políticas da loja.

As decisões de arquitetura e implementação permaneceram sob minha responsabilidade, garantindo que todo código incorporado à solução fosse compreendido e justificável por mim.
