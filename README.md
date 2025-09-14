# TxtMyJournal API (TMJ-API)

An AI-powered journaling platform that enables users to journal via SMS text messages and receive intelligent, empathetic responses powered by advanced language models.


## 🎥 Demo

[![Watch the demo](https://github.com/user-attachments/assets/5d10f1d8-5f4e-45ec-a5ba-39d8a6539f94)](https://x.com/i/status/1810358545982034152)

> Click the image above to watch the full demo on X.

## 🌟 Features

- **Whats-App & Imessage based journaling**: Journal by simply texting your thoughts and experiences
- **AI-powered responses**: Get personalized, empathetic responses from an AI companion
- **Emotion analysis**: Automatic emotion classification of journal entries
- **Memory & reflection**: AI can help you reflect on past experiences using semantic search
- **Dual response modes**: 
  - Reflection mode: Helps you revisit and reflect on past journal entries
  - Current thoughts mode: Responds to your immediate feelings and experiences
- **Multimodal Input**: Works with images of written and voice entires
- **Vector similarity search**: Find related past entries using advanced embeddings
- **User management**: Phone number-based user accounts

## 🏗️ Technical Architecture

### Core Technologies
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL with pgvector**: Vector database for storing embeddings and journal entries
- **SQLAlchemy**: Python SQL toolkit and Object Relational Mapping (ORM)
- **Alembic**: Database migration tool

### AI & ML Stack
- **OpenAI GPT-4o**: Primary conversational AI model
- **HuggingFace Transformers**: Text embeddings using GTE-base model
- **RoBERTa**: Emotion classification (go_emotions model)
- **LlamaIndex**: Retrieval-Augmented Generation (RAG) framework
- **LangChain**: Chat memory and conversation management
- **Cohere**: Re-ranking for improved search results

### External Integrations
- **SendBlue API**: SMS messaging service for text-based interactions

## 🧭 Architecture Diagrams

### End-to-end Message Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant SB as SendBlue (SMS)
    participant API as FastAPI /entries
    participant CRUD as CRUD/Models
    participant DB as PostgreSQL + pgvector
    participant H as helpers (AI pipeline)
    participant LLM as OpenAI (ChatOpenAI)
    participant RAG as LlamaIndex + CustomSQLRetriever
    participant CH as Cohere (Re-rank)

    U->>SB: Send SMS
    SB->>API: POST /entries (from_number, content, date_sent, …)
    API->>CRUD: get_user_by_phone_number(from_number)
    CRUD->>DB: SELECT users WHERE phone_number=…
    DB-->>CRUD: user or none
    CRUD-->>API: user found
    API->>API: tokenizer.embed(content), tokenizer.emotion(content)
    API->>CRUD: query_embeddings(user.id, embedding)  // warms cache
    API->>H: generate_response(user_phone, content, date_sent, settings, db)

    rect rgb(245,245,245)
      note over H,LLM: AI Response Pipeline (two modes)
      H->>RAG: CustomSQLRetriever.retrieve(query)
      RAG->>DB: Vector similarity search (entries.embedding <=> query)
      DB-->>RAG: Top-k entries with similarity
      RAG->>CH: Rerank top candidates
      CH-->>H: Reranked nodes
      H->>LLM: Prompt + context (reflection) OR conversational prompt (current thoughts)
      LLM-->>H: Generated response
    end

    H-->>API: response
    API->>CRUD: create_user_entry(EntryCreate{content, embedding, emotions}, author_id)
    CRUD->>DB: INSERT INTO entries …
    DB-->>CRUD: inserted row
    API->>H: send_message(user_phone, response)
    H->>H: split_paragraph_into_sentences (emoji-aware)
    loop For each sentence
      H->>SB: POST /api/send-message {number, content}
    end
    SB-->>U: SMS message(s)
    API-->>SB: 200 OK (returns response text)
```

### Components and Data Flow

```mermaid
flowchart LR
  subgraph Client
    U[User (SMS)]
  end

  subgraph Messaging
    SB[SendBlue SMS Webhook]
  end

  subgraph API[FastAPI Application]
    EP1[/POST /entries/ (MessagePayload)/]
    EP2[/POST /users/ (UserCreate)/]
    HLP[helpers.py]
    CR[crud.py]
    TOK[tokenizer (embed, emotion)]
  end

  subgraph AI[AI Layer]
    LC[LangChain ChatOpenAI (gpt-4o)]
    LI[LlamaIndex Query/RAG]
    CSR[CustomSQLRetriever (utils.py)]
    RR[Cohere Re-rank]
  end

  subgraph Data[PostgreSQL + pgvector]
    USERS[(users)]
    ENTRIES[(entries: content, emotions, embedding Vector(768))]
  end

  U --> SB --> EP1
  EP2 --> CR --> USERS
  EP1 --> CR --> USERS
  EP1 --> TOK
  EP1 --> HLP
  HLP --> CSR --> ENTRIES
  CSR --> RR --> HLP
  HLP --> LC --> HLP
  HLP --> CR --> ENTRIES
  HLP --> SB
```

### Data Model (ER Diagram)

```mermaid
erDiagram
    USERS ||--o{ ENTRIES : "has many"
    USERS {
        int id PK
        string phone_number "length 12"
        datetime created_at
        string hashed_password
    }
    ENTRIES {
        int id PK
        datetime created_at
        date date
        string emotions "nullable"
        text content
        vector[768] embedding "pgvector"
        int author_id FK "-> users.id"
    }
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- API keys for:
  - OpenAI
  - Cohere
  - LangChain (for tracing)
  - SendBlue (for imessage)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vkodithala/tmj-api.git
   cd tmj-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Cohere Configuration
   COHERE_API_KEY=your_cohere_api_key_here
   
   # LangChain Configuration (for tracing)
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   
   # SendBlue SMS Configuration
   SENDBLUE_APIURL=https://api.sendblue.co/api/send-message
   SENDBLUE_APIKEY=your_sendblue_api_key_here
   SENDBLUE_APISECRET=your_sendblue_api_secret_here
   ```

4. **Set up PostgreSQL with pgvector**
   ```sql
   -- Install pgvector extension
   CREATE EXTENSION vector;
   
   -- Update your database connection string in app/database.py
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the API server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Endpoints

#### Create User
```http
POST /users/
```
Creates a new user account and sends a welcome message.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "password": "user_password"
}
```

**Response:**
```json
{
  "id": 1,
  "phone_number": "+1234567890",
  "created_at": "2024-01-01T00:00:00",
  "entries": []
}
```

#### Create Journal Entry
```http
POST /entries/
```
Processes incoming journal entries from SMS webhook, analyzes content, and sends AI-generated response.

**Request Body (SendBlue Webhook Format):**
```json
{
  "accountEmail": "user@example.com",
  "content": "I had a really tough day at work today...",
  "media_url": "",
  "is_outbound": false,
  "status": "delivered",
  "message_handle": "msg_123",
  "date_sent": "2024-01-01T12:00:00Z",
  "date_updated": "2024-01-01T12:00:00Z",
  "from_number": "+1234567890",
  "number": "+1234567890",
  "plan": "blue"
}
```

**Response:** AI-generated empathetic response text

## 🤖 AI Response System

The system uses a sophisticated AI pipeline:

1. **Input Processing**: Incoming text is analyzed for emotional content
2. **Intent Classification**: AI determines if user wants to reflect on past experiences or discuss current thoughts
3. **Retrieval**: For reflection mode, similar past entries are retrieved using vector similarity
4. **Response Generation**: AI generates contextual, empathetic responses
5. **Message Splitting**: Long responses are intelligently split into multiple SMS messages

### Response Modes

#### Reflection Mode
Triggered by queries like:
- "Tell me about a time when I felt sad"
- "Give me a time when I went on an adventure with friends"
- "Describe a moment when I felt lost"

#### Current Thoughts Mode
Handles present-moment journaling:
- "I'm feeling anxious today"
- "Had a great day at the park with friends"
- "Feeling overwhelmed with work"

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `phone_number`: User's phone number (12 chars)
- `created_at`: Account creation timestamp
- `hashed_password`: Encrypted password

### Entries Table
- `id`: Primary key
- `content`: Journal entry text
- `embedding`: 768-dimensional vector embedding
- `emotions`: Classified emotion from the entry
- `created_at`: Entry creation timestamp
- `date`: Entry date
- `author_id`: Foreign key to users table

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Yes |
| `COHERE_API_KEY` | Cohere API key for re-ranking | Yes |
| `LANGCHAIN_API_KEY` | LangChain API key for tracing | Yes |
| `SENDBLUE_APIURL` | SendBlue API endpoint | Yes |
| `SENDBLUE_APIKEY` | SendBlue API key | Yes |
| `SENDBLUE_APISECRET` | SendBlue API secret | Yes |

### Database Configuration

Update the database connection string in `app/database.py`:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/tmj_db"
```

## 🧪 Testing

Run the test suite:
```bash
pytest app/test_main.py
```

## 📝 Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Adding New Features

1. Update database models in `app/models.py`
2. Create corresponding Pydantic schemas in `app/schemas.py`
3. Implement CRUD operations in `app/crud.py`
4. Add API endpoints in `app/main.py`
5. Update tests in `app/test_main.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please contact the development team or create an issue in the GitHub repository.
