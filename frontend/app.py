import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta

# --- 1. Configuration and Initialization ---
# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Credit Card Spending Analysis", 
    initial_sidebar_state="expanded"
)

# Initialize session state for navigation, chat history, and saved history
if 'page' not in st.session_state:
    st.session_state.page = 'chat'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I'm your Credit Card Spending Analysis Assistant. Please upload your files or ask any questions about your spending."}
    ]
if 'saved_chats' not in st.session_state:
    # List to store all previous chat sessions
    st.session_state.saved_chats = []

# --- 2. Mock Data Generation Function ---

def generate_mock_data(time_dimension):
    """
    Generate mock spending data based on the selected time dimension.
    """
    categories = ['Dining', 'Transportation', 'Entertainment', 'Housing', 'Others']
    
    # 1. Pie Chart/Bar Chart Data (Total Spending)
    data = {
        'Category': categories,
        'Total Spending': [random.randint(8000, 35000) for _ in categories] # Mock total spending
    }
    df_spending = pd.DataFrame(data)

    # 2. Line Chart Data (Time Trend)
    if time_dimension == 'Weekly':
        time_points = 7
        freq = 'D'
        title_suffix = 'Last 7 Days'
    elif time_dimension == 'Monthly':
        time_points = 30
        freq = 'D'
        title_suffix = 'Last 30 Days'
    else: # Quarterly
        time_points = 12
        freq = 'W'
        title_suffix = 'Last 12 Weeks'

    end_date = datetime.now()
    if freq == 'D':
        date_range = pd.date_range(end=end_date, periods=time_points, freq=freq).date
    else:
        date_range = pd.date_range(end=end_date, periods=time_points, freq=freq).strftime('%m/%d')
    
    trend_data = []
    base_amount = 1000
    for i, date in enumerate(date_range):
        for category in categories:
            # Simulate random fluctuations and set different base spending
            amount = base_amount + random.randint(-500, 500)
            if category == 'Housing':
                 amount += 5000 + (i * 50 if time_dimension == 'Quarterly' else 0) # Simulate stable and high housing cost
            elif category == 'Dining':
                 amount += 2000 + (random.randint(0, 300) if time_dimension == 'Monthly' else 0)
            
            trend_data.append({
                'Date': date,
                'Category': category,
                'Spending Amount': max(100, amount) # Ensure amount is positive
            })
    
    df_trend = pd.DataFrame(trend_data)
    
    return df_spending, df_trend, title_suffix

# --- 3. Chatbot Rendering Function ---

def render_chatbot():
    st.header("💬 Credit Card Spending Assistant (Chatbot)")
    st.info("The conversation here simulates the LLM+Memory function. Actual memory and model calls should be implemented via the FastAPI backend.")

    # Display chat history
    for message in st.session_state.chat_history:
        role = "user" if message["role"] == "user" else "assistant"
        # Use Streamlit's built-in chat_message for styling
        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
            st.markdown(message["content"])

    # User input (Simulate interaction)
    if prompt := st.chat_input("Enter your question (e.g., What was my largest expense last month?"):
        # 1. Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # 2. Simulate AI response (This is where FastAPI backend call would go)
        # Simulate LLM response based on memory and data analysis
        mock_response = (
            f"Based on the credit card spending records you uploaded, I have analyzed your question: **{prompt}**.\n\n"
            "This involves your historical transaction data and category analysis. As we are simulating, my answer is:\n\n"
            "Your largest expense last month was in the **Housing** category, totaling approximately **NT$32,500**. This expense occurred at the beginning of the month.\n\n"
            "If you want to view the overall trends, please switch to the **Data Dashboard**."
        )
        
        # 3. Add assistant message and display
        st.session_history.chat_history.append({"role": "assistant", "content": mock_response})
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(mock_response)

# --- 4. Dashboard Rendering Function ---

def render_dashboard():
    st.header("📊 Spending Analysis Dashboard")
    st.info("The data in this dashboard is mock data generated for visualization purposes.")

    # Time dimension selection
    time_dimension = st.radio(
        "Select Time Dimension",
        ('Weekly', 'Monthly', 'Quarterly'),
        index=1,
        horizontal=True,
    )
    
    # Generate data
    df_spending, df_trend, title_suffix = generate_mock_data(time_dimension)

    st.subheader(f"📈 {time_dimension} Spending Analysis Overview ({title_suffix})")

    # --- Pie Chart and Bar Chart ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Pie Chart: Proportion of Spending Categories")
        # Pie Chart (Proportion of spending categories)
        fig_pie = px.pie(
            df_spending, 
            values='Total Spending', 
            names='Category', 
            title='Spending Category Proportion',
            hole=.4, # Add center hole
            color_discrete_sequence=px.colors.sequential.Agsunset,
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown(f"#### Bar Chart: {time_dimension} Spending Ranking")
        # Bar Chart (Spending ranking by category)
        df_sorted = df_spending.sort_values('Total Spending', ascending=False)
        fig_bar = px.bar(
            df_sorted, 
            x='Category', 
            y='Total Spending', 
            title='Total Spending Rank by Category',
            text=df_sorted['Total Spending'].apply(lambda x: f'NT$ {x:,}'), # Format text
            color='Category',
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            yaxis_title="Total Spending Amount (NT$)", 
            xaxis_title="Spending Category",
            uniformtext_minsize=8, 
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig_bar, use_container_width=True)


    # --- Line Chart ---
    st.markdown("#### Line Chart: Spending Trend Over Time for Each Category")
    # Line Chart (Spending trend over time for each category)
    fig_line = px.line(
        df_trend, 
        x='Date', 
        y='Spending Amount', 
        color='Category', 
        title=f'Spending Trend by Category for {time_dimension}',
        markers=True,
        line_shape='spline', # Increase curve smoothness
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_line.update_layout(
        xaxis_title="Time",
        yaxis_title="Spending Amount (NT$)",
        hovermode="x unified",
        legend_title="Spending Category"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# --- 5. Chat History List Rendering Function ---

def render_chat_history_list():
    st.header("🕰️ Chat History List")
    st.info("Click on a chat summary card to load and resume the conversation.")

    if not st.session_state.saved_chats:
        st.warning("No previous chat history saved yet.")
        return

    # Display saved chats as cards (use columns for a grid layout)
    # Reverse order to show latest first
    reversed_chats = st.session_state.saved_chats[::-1]
    
    # Use columns to create a canvas/card layout (3 cards per row)
    cols = st.columns(3)
    
    for i, chat_session in enumerate(reversed_chats):
        # Determine which column to place the card in
        with cols[i % 3]: 
            with st.container(border=True):
                st.markdown(f"**Chat ID:** {chat_session['id']}")
                st.markdown(f"**Topic:** {chat_session['topic']}")
                st.markdown(f"**Messages:** {len(chat_session['history']) - 1} (excluding greeting)")
                st.caption(f"Saved: {chat_session['timestamp']}")
                
                # Button to load the chat
                if st.button("Load Chat", key=f"load_{chat_session['id']}", use_container_width=True):
                    # Load the selected chat into the active session
                    st.session_state.chat_history = chat_session['history']
                    st.session_state.page = 'chat'
                    st.toast(f"Loaded chat: {chat_session['topic']}")
                    st.rerun()

# --- 6. Sidebar ---

with st.sidebar:
    st.title("💳 Smart Spending Analysis")
    st.markdown("---")
    # Note on Sidebar Toggle: The native Streamlit hamburger icon (☰) in the top-left corner
    # already provides the hide/unhide functionality for the sidebar.

    # 1. New Chat (Now includes saving logic)
    if st.button("✨ New Chat", use_container_width=True, type="primary", help="Start a brand new conversation"):
        # Check if the current chat has content (more than just the initial greeting)
        if len(st.session_state.chat_history) > 1:
            
            # Determine topic: Use the first user prompt or a default title
            first_user_prompt = next((msg['content'] for msg in st.session_state.chat_history if msg['role'] == 'user'), "Untitled Chat")
            
            # Simple Topic Extraction (limit length)
            topic = first_user_prompt.split('?')[0].split('.')[0][:50].strip()
            if len(topic) >= 50:
                topic += "..."

            # Save current chat history
            new_session = {
                'id': str(len(st.session_state.saved_chats) + 1).zfill(3),
                'topic': topic or "General Spending Inquiry",
                'history': st.session_state.chat_history,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.saved_chats.append(new_session)
            st.toast(f"Current chat saved as: '{new_session['topic']}'")
            
        # Reset active chat
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I'm your Credit Card Spending Analysis Assistant. Please upload your files or ask any questions about your spending."}
        ]
        st.session_state.page = 'chat'
        st.rerun() # Rerun to clear interface

    st.markdown("---")
    
    # 2. Upload Files
    uploaded_files = st.file_uploader(
        "📂 Upload Files (PDF, JPG, TXT)",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt'],
        accept_multiple_files=True,
        help="Upload your spending records, bill screenshots, etc., for analysis."
    )
    if uploaded_files:
        st.success(f"Successfully uploaded **{len(uploaded_files)}** files. Ready for analysis!")

    st.markdown("---")

    # 3. Navigation
    st.subheader("Navigation")
    
    # Navigation Buttons
    
    # Chatbot Button
    if st.button("💬 Chatbot", use_container_width=True, disabled=st.session_state.page == 'chat'):
        st.session_state.page = 'chat'
        st.rerun()
    
    # Chat History Button (New Feature)
    if st.button("🕰️ Chat History", use_container_width=True, disabled=st.session_state.page == 'history'):
        st.session_state.page = 'history'
        st.rerun()

    # Dashboard Button
    if st.button("📊 Dashboard", use_container_width=True, disabled=st.session_state.page == 'dashboard'):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    st.caption("LLM + Landing.AI Application Frontend Simulation")

# --- 7. Main Content Rendering ---

if st.session_state.page == 'chat':
    render_chatbot()
elif st.session_state.page == 'dashboard':
    render_dashboard()
elif st.session_state.page == 'history':
    render_chat_history_list()