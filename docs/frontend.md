💳 Credit Card Spending Analysis Frontend (Streamlit Simulation)

This is a single-file application built using the Python Streamlit framework. Its purpose is to simulate the frontend interface for a credit card spending analysis tool driven by an LLM and a data analysis backend (Landing.AI).

This frontend includes a chatbot, file upload capability, and a data dashboard, with the architecture designed to be integrated with a backend FastAPI service.

⚙️ Setup and Installation

To run this application, you need Python 3.7+ and the following libraries:

# Install Streamlit, Pandas, and Plotly
pip install streamlit pandas plotly


🚀 How to Run

After saving the provided code as credit_card_analysis_app.py, run the following command in your terminal:

streamlit run credit_card_analysis_app.py


The application will automatically open in your web browser.

✨ Application Features

The application provides the following core functions (all data is mock-generated):

1. Sidebar

Note on Sidebar Toggle: The native Streamlit hamburger icon (☰) in the top-left corner already provides the hide/unhide functionality for the sidebar.

New Chat (✨ New Chat): Saves the current conversation to the history log, generates a topic, and starts a new, blank analysis session.

Upload Files (📂 Upload Files): Supports uploading files like PDF, JPG, and TXT, simulating the import of spending records or bills.

Navigation: Allows quick switching between the Chatbot, Chat History, and Dashboard interfaces.

2. Chat History

This page manages and displays all historical conversation sessions.

Canvas View: History records are presented as summary cards in a grid layout, detailing the chat's Topic, ID, message count, and save time.

Automatic Topic Generation: When a chat is saved, a topic is automatically extracted from the first user prompt.

Load Conversation: The "Load Chat" button reloads the selected history into the main Chatbot interface, allowing the user to review or continue the discussion.

3. AI Assistant (Chatbot)

Located on the right side of the main screen, allowing natural language conversation with the LLM assistant.

Memory Functionality: Conversation history is simulated using Streamlit's st.session_state.

Simulated Backend Call: After user input, a mock analysis response is returned, indicating where the actual FastAPI backend call should be implemented.

4. Data Dashboard

The dashboard provides comprehensive visual analysis and allows selection of three time dimensions: Weekly, Monthly, and Quarterly:

Chart Type

Visualization Content

Pie Chart

Displays the Proportion of Spending Categories.

Bar Chart

Displays the Spending Ranking by category.

Line Chart

Displays the Spending Trend Over Time for each category within the selected time dimension.

💻 Architectural Notes

This file serves only as the frontend interface. In a complete LLM + Analysis architecture, the backend should handle the following responsibilities:

FastAPI Backend: Receives requests from the frontend, manages the LLM's memory state, and calls the model.

Landing.AI/Analysis Module: Responsible for parsing uploaded files, extracting transaction data, and performing real-time spending pattern analysis.