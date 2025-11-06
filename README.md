# Financial Advisor Agent

## Tech Stack
- **Database**: SQLite (local, file-based)
- **Document Extraction**: LandingAI ADE
- **Agentic Framework**: LangChain + CrewAI
- **LLM**: AWS Bedrock
- **Backend**: FastAPI (optional - can run locally)
- **Frontend**: Streamlit
- **Processing**: Pandas, NumPy

## Plan

### Phase 1: Core Setup & Document Processing

**A: Database & Backend**
- Set up SQLite schema
- Create tables: users, accounts, transactions, financial_advice
- Set up FastAPI for backend functions

**B: Document Processing**
- Integrate LandingAI ADE for bank statement extraction
- Build data normalization pipeline
- Set up LLM connection

**C: Basic Frontend**
- Design basic user flow
- Create Streamlit file upload interface
- Build data display components
- Implement progress indicators

### Phase 2: Financial Analysis & AI Agents

**A: Analysis Engine**
- Implement spending categorization
- Create basic financial health scoring
- Build simple savings recommendations
- Add monthly trend analysis

**B: Agent System**
- Set up CrewAI agents:
  - Financial Analyst (categorization)
  - Savings Advisor (recommendations)
- Implement basic agent communication
- Create financial advice prompts

**C: Enhanced UI**
- Add transaction visualization charts
- Create personal advice display interface
- Implement basic reporting
- Improve user experience

### Phase 3: Polish & Integration

**All Team Members**
- Integrate all components
- Test with sample bank statements
- Fix bugs and improve accuracy
- Check error handling adequate
- Create demo data

### Phase 4: Final Testing & Demo Prep

**All Team Members**
- End-to-end testing
- Performance optimization
- Prepare presentation
- Create documentation


### Task Allocation
- A: Database, analysis algorithms, backend logic
- B: Document processing and data extraction, agent framework
- C: Frontend, UX, visualization, testing