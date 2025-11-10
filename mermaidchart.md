# Financial Advisor Agent - Application Workflow

This diagram shows the complete workflow of the Financial Advisor Agent, from document upload to answer generation and dashboard visualization.

---
config:
  layout: elk
---
flowchart TD
    Start([User Starts Session]) --> Upload[Upload Credit Card Statement]
    
    Upload --> ADE[LandingAI ADE]
    ADE --> Parse[Parse Document to Markdown]
    Parse --> Extract[Extract Structured Data]
    Extract --> Store[Store in MongoDB]
    
    Store --> Index[Index for RAG]
    Index --> Chunk[Chunk Text]
    Chunk --> Embed[Generate Embeddings]
    Embed --> RAGIndex[(RAG Index)]
    
    Store --> Chat{User Asks Question}
    RAGIndex --> Chat
    
    Chat --> HybridSearch[Hybrid Search]
    HybridSearch --> Semantic[Semantic Search 70%]
    HybridSearch --> Keyword[Keyword Search 30%]
    
    Semantic --> Retrieve[Retrieve Top Chunks]
    Keyword --> Retrieve
    
    Retrieve --> LLM[ZhipuAI Synthesis]
    Store --> LLM
    
    LLM --> Answer[Generate Answer with Citations]
    Answer --> Display[Display in Chat Interface]
    
    Store --> Analysis[Financial Analysis]
    Analysis --> Trends[Spending Trends]
    Analysis --> Health[Health Score]
    Analysis --> Categories[Category Analysis]
    
    Trends --> Dashboard[Dashboard Visualizations]
    Health --> Dashboard
    Categories --> Dashboard
    
    style Start fill:#e1f5ff
    style Upload fill:#fff4e1
    style ADE fill:#ffe1f5
    style Store fill:#e1ffe1
    style Chat fill:#f5e1ff
    style LLM fill:#ffe1f5
    style Answer fill:#e1f5ff
    style Dashboard fill:#fff4e1
