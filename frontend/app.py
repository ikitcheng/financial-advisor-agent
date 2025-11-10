import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta
import requests 
import json     
import uuid

# --- 1. Configuration and Initialization ---
FASTAPI_BASE_URL = "http://localhost:8000/api/v1" 

# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Credit Card Spending Analysis", 
    initial_sidebar_state="expanded"
)

# --- Persistence and Initialization Helper ---

def initialize_persistence_and_state():
    """Initializes user_id (simulated persistence) and session state."""
    
    # 1. User ID Initialization (Simulated Cookie Persistence)
    # The 'user_id' acts as the primary key for all saved data across sessions.
    # We use st.session_state as a simple persistence mechanism across reruns.
    if 'user_id' not in st.session_state:
        # In a real app, this would read from a cookie or localStorage.
        # Here we generate a unique ID and treat st.session_state as persistent across one user's reruns.
        st.session_state.user_id = str(uuid.uuid4())
        
    # 2. Session ID Initialization (Ephemeral per active chat)
    # The 'session_id' is the FastAPI backend chat session ID, which is cleared on 'New Chat'.
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
        
    # 3. Frontend UI State
    if 'page' not in st.session_state:
        st.session_state.page = 'chat'
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I'm your Credit Card Spending Analysis Assistant. Please upload your files or ask any questions about your spending."}
        ]
    if 'saved_chats' not in st.session_state:
        # List to store all previous chat sessions associated with the current user_id
        st.session_state.saved_chats = []
        
    # 4. File Uploader Key (CRITICAL for clearing uploads)
    if 'upload_key' not in st.session_state:
        st.session_state.upload_key = 0

# Run initialization
initialize_persistence_and_state()


# --- 2. API Helper Function ---

def get_new_session_id():
    """Calls FastAPI to generate a new session ID."""
    try:
        # NOTE: If we wanted the backend to use the user_id, we would pass it here.
        response = requests.post(f"{FASTAPI_BASE_URL}/sessions/new")
        if response.status_code == 200:
            return response.json().get("session_id")
        else:
            st.error(f"Failed to get new session ID from backend. Status: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to FastAPI backend at {FASTAPI_BASE_URL}. Ensure the backend is running (e.g., uvicorn backend.main:app --reload).")
        return None

# Initialize session ID on first load if missing
if st.session_state.session_id is None:
    new_id = get_new_session_id()
    if new_id:
        st.session_state.session_id = new_id
        st.toast(f"New session started: {new_id}")

# --- 3. Mock Data Generation Function (Unchanged) ---

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

# --- 4. Chatbot Rendering Function (Updated for API Integration) ---

def render_chatbot():
    st.header("💬 Credit Card Spending Assistant (Chatbot)")
    st.info(f"Connected to Backend. Session ID: **{st.session_state.session_id or 'N/A'}**")
    
    if not st.session_state.session_id:
        st.warning("Cannot start chat without a valid Session ID. Check backend connection.")
        return

    # Display chat history
    for message in st.session_state.chat_history:
        role = "user" if message["role"] == "user" else "assistant"
        # Use Streamlit's built-in chat_message for styling
        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Enter your question (e.g., What was my largest expense last month?"):
        
        # 1. Add user message to frontend history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        
        # Prepare the payload for the backend API
        payload = {
            "session_id": st.session_state.session_id,
            "user_message": prompt
        }
        
        with st.spinner("Assistant is thinking and calling the backend LLM service..."):
            try:
                # 2. Call the FastAPI backend for LLM response
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/{st.session_state.session_id}/send_message",
                    json=payload
                )
                
                if response.status_code == 200:
                    backend_data = response.json()
                    # The backend provides the full response content
                    mock_response = backend_data.get("assistant_response", "Error: No response content from backend.")
                    
                    # 3. Add assistant message and display
                    st.session_state.chat_history.append({"role": "assistant", "content": mock_response})
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(mock_response)
                        
                else:
                    error_msg = response.json().get("detail", f"Backend failed with status code {response.status_code}")
                    st.session_state.chat_history.append({"role": "assistant", "content": f"ERROR: Backend API failed. {error_msg}"})
                    st.error(f"API Error: {error_msg}")
                    st.rerun() # Rerun to display error instantly
                    
            except requests.exceptions.ConnectionError:
                error_msg = f"Cannot connect to FastAPI backend at {FASTAPI_BASE_URL}. Ensure it is running."
                st.session_state.chat_history.append({"role": "assistant", "content": f"CONNECTION ERROR: {error_msg}"})
                st.error(error_msg)
                st.rerun() # Rerun to display error instantly

# --- 5. Dashboard Rendering Function (Unchanged) ---

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

# --- 6. Chat History List Rendering Function (Unchanged in logic) ---

def render_chat_history_list():
    st.header("🕰️ Chat History List")
    st.info(f"Showing saved chats for User ID: **{st.session_state.user_id}**")

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
                # The ID here is the internal saved_chats index, not the backend session_id
                st.markdown(f"**Chat Ref ID:** {chat_session['id']}") 
                st.markdown(f"**Topic:** {chat_session['topic']}")
                st.markdown(f"**Backend Session ID:** {chat_session['backend_session_id'][:8]}...")
                st.markdown(f"**Messages:** {len(chat_session['history']) - 1} (excluding greeting)")
                st.caption(f"Saved: {chat_session['timestamp']}")
                
                # Button to load the chat
                if st.button("Load Chat", key=f"load_{chat_session['id']}", use_container_width=True):
                    # Load the selected chat into the active session
                    st.session_state.chat_history = chat_session['history']
                    st.session_state.session_id = chat_session['backend_session_id'] # Important: Re-use the backend session ID (if still valid)
                    st.session_state.page = 'chat'
                    st.toast(f"Loaded chat: {chat_session['topic']}")
                    st.rerun()

# --- 7. Sidebar (Updated for New Chat and Persistence) ---

with st.sidebar:
    st.title("💳 Smart Spending Analysis")
    st.markdown("---")
    
    # Display user and session IDs for debugging
    st.caption(f"App User ID: **{st.session_state.user_id}**")
    st.caption(f"Current Session ID: **{st.session_state.session_id or 'N/A'}**")

    # 1. New Chat (Updated to clear file uploader and handle topic extraction)
    if st.button("✨ New Chat", use_container_width=True, type="primary", help="Start a brand new conversation and clear the file uploader."):
        if st.session_state.session_id: # Only proceed if connected/initialized
            
            # --- 1. Save Old Chat Logic ---
            # Condition: Save if history length > 1 (meaning, there was user chat OR file upload confirmation)
            if len(st.session_state.chat_history) > 1:
                
                # Try to find the first user prompt (only messages with role 'user')
                first_user_msg = next((msg['content'] for msg in st.session_state.chat_history if msg['role'] == 'user'), None)
                
                if first_user_msg:
                    # Case 1: User message exists, generate topic from it
                    topic = first_user_msg.split('?')[0].split('.')[0][:50].strip()
                    if len(topic) >= 50:
                        topic += "..."
                    # Ensure topic is not empty if prompt was just symbols
                    topic = topic or "General Inquiry"
                else:
                    # Case 2: Only file uploads, no user chat (Topic = "No Topic Title")
                    topic = "No Topic Title"

                new_session = {
                    'user_id': st.session_state.user_id, # Link to the persistent user ID
                    'id': str(len(st.session_state.saved_chats) + 1).zfill(3),
                    'topic': topic, # Use the determined topic
                    'backend_session_id': st.session_state.session_id, # Store the backend ID
                    'history': st.session_state.chat_history,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.saved_chats.append(new_session)
                st.toast(f"Current chat saved as: '{new_session['topic']}'")
            
            # --- 2. Request New Backend Session ID ---
            new_id = get_new_session_id()
            if new_id:
                st.session_state.session_id = new_id
                
                # --- 3. CRITICAL: Reset File Uploader and Chat State ---
                st.session_state.upload_key += 1 # Reset Uploader
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "Hello! I'm your Credit Card Spending Analysis Assistant. Please upload your files or ask any questions about your spending."}
                ]
                st.session_state.page = 'chat'
                st.toast(f"New session started: {new_id}")
                st.rerun() 
        else:
             st.warning("Cannot start new chat. Please check if the FastAPI backend is running.")

    st.markdown("---")
    
    # 2. Upload Files (Updated key logic)
    uploaded_files = st.file_uploader(
        "📂 Upload Files (PDF, JPG, TXT)",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt'],
        accept_multiple_files=True,
        # IMPORTANT: Use the session state key to enable resetting
        key=f"file_uploader_{st.session_state.upload_key}", 
        help="Upload your spending records, bill screenshots, etc., for analysis."
    )
    
    if uploaded_files and st.session_state.session_id:
        
        successful_uploads = []
        
        for file in uploaded_files:
            with st.spinner(f"Uploading and processing **{file.name}**..."):
                try:
                    # Prepare file for multipart form data submission
                    files = {'file': (file.name, file.getvalue(), file.type)}
                    
                    response = requests.post(
                        f"{FASTAPI_BASE_URL}/{st.session_state.session_id}/upload_file",
                        files=files # Use files argument for file uploads
                    )
                    
                    if response.status_code == 200:
                        backend_data = response.json()
                        successful_uploads.append(file.name)
                        
                        # Add a system message to chat history confirming the upload
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"Successfully processed file **{file.name}**!"
                        })

                    else:
                        error_msg = response.json().get("detail", f"Upload failed with status code {response.status_code}")
                        st.error(f"Failed to process **{file.name}**: {error_msg}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"ERROR: File upload failed for **{file.name}**. {error_msg}"
                        })

                except requests.exceptions.ConnectionError:
                    st.error(f"Cannot connect to FastAPI backend at {FASTAPI_BASE_URL} for upload.")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "CONNECTION ERROR: Cannot connect to FastAPI backend for file upload."
                    })
                    break # Stop processing if connection fails

        if successful_uploads:
            st.toast(f"Successfully processed {len(successful_uploads)}/{len(uploaded_files)} files.")
            
            # CRITICAL FIX: Increment the key to force Streamlit to render an empty file uploader 
            # on the next rerun, preventing the infinite loop.
            st.session_state.upload_key += 1
            
            st.rerun() # Rerun to update chat history with success message and use new key
            
    elif uploaded_files and not st.session_state.session_id:
        st.warning("Cannot upload files. Please ensure the FastAPI backend is running and a session ID is generated.")


    st.markdown("---")

    # 3. Navigation
    st.subheader("Navigation")
    
    # Navigation Buttons
    
    if st.button("💬 Chatbot", use_container_width=True, disabled=st.session_state.page == 'chat'):
        st.session_state.page = 'chat'
        st.rerun()
    
    if st.button("🕰️ Chat History", use_container_width=True, disabled=st.session_state.page == 'history'):
        st.session_state.page = 'history'
        st.rerun()

    if st.button("📊 Dashboard", use_container_width=True, disabled=st.session_state.page == 'dashboard'):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    st.caption("LLM + Landing.AI Application Frontend Simulation")

# --- 8. Main Content Rendering ---

if st.session_state.page == 'chat':
    render_chatbot()
elif st.session_state.page == 'dashboard':
    render_dashboard()
elif st.session_state.page == 'history':
    render_chat_history_list()

# To run this app locally, you would execute:
# cd frontend
# streamlit run app.py