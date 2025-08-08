# main_app.py

import streamlit as st
from langchain_openai import OpenAI
from langchain.agents import AgentExecutor, create_react_agent, load_tools
from langchain_core.prompts import PromptTemplate
import os

# --- PAGE CONFIGURATION ---
# Set the page title and icon for a more professional look.
st.set_page_config(
    page_title="Agentic AI Web Researcher",
    page_icon="🤖",
    layout="centered",
)

# --- STYLES ---
# Custom CSS for a cleaner and more modern UI.
st.markdown("""
<style>
    /* General body styles */
    body {
        font-family: 'Inter', sans-serif;
    }
    /* Style for the main container */
    .main {
        background-color: #f0f2f6;
    }
    /* Chat message styling */
    .stChatMessage {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Button styling */
    .stButton>button {
        border-radius: 0.5rem;
        border: 1px solid #007bff;
        background-color: #007bff;
        color: white;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# --- AGENT SETUP ---
@st.cache_resource
def setup_agent():
    """
    Initializes and configures the LangChain agent with tools and an LLM.
    Returns:
        AgentExecutor: The configured agent executor object.
    """
    # 1. Initialize the Language Model (LLM)
    # We use OpenAI's model. An API key is required.
    # The temperature is set to 0 to make the model's responses more deterministic.
    llm = OpenAI(temperature=0)

    # 2. Load the necessary tools
    # The agent will use these tools to perform actions.
    # 'ddg-search': DuckDuckGo search for accessing real-time web information.
    # 'llm-math': A tool that uses the LLM itself to solve mathematical problems.
    tools = load_tools(["ddg-search", "llm-math"], llm=llm)

    # 3. Define the prompt template
    # This template guides the agent on how to behave, how to use tools,
    # and how to format its thought process and final answer.
    template = """
    Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(template)

    # 4. Create the agent
    # This function creates the core agent logic, binding the LLM and tools
    # together with the defined prompt.
    agent = create_react_agent(llm, tools, prompt)

    # 5. Create the Agent Executor
    # The executor is the runtime for the agent. It takes user input,
    # orchestrates the agent's thinking and tool usage, and returns the final response.
    # `handle_parsing_errors=True` makes it more robust to occasional LLM formatting mistakes.
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # Set to True to see the agent's thought process in the console
        handle_parsing_errors=True,
        max_iterations=5 # Prevents the agent from getting stuck in long loops
    )

    return agent_executor


# --- STREAMLIT UI ---

# --- Header and Introduction ---
st.title("🤖 Agentic AI Web Researcher")
st.markdown("""
Welcome! This is a simple AI agent that can browse the web to answer your questions.
It uses **LangChain** to orchestrate its actions and **DuckDuckGo Search** as its tool for finding information.

To get started, you'll need an **OpenAI API key**.
""")

# --- API Key Input ---
# Use a sidebar for the API key input to keep the main interface clean.
with st.sidebar:
    st.header("Configuration")
    openai_api_key = st.text_input(
        "Enter your OpenAI API Key",
        type="password",
        key="api_key_input"
    )
    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")

# --- Main Application Logic ---
if not openai_api_key:
    st.info("Please add your OpenAI API key in the sidebar to continue.")
    st.stop()

# Set the API key for LangChain to use.
os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize the agent.
try:
    agent_executor = setup_agent()
except Exception as e:
    st.error(f"Failed to initialize the agent. Please check your API key and dependencies. Error: {e}")
    st.stop()


# --- Chat History Management ---
# `st.session_state` is used to persist data across user interactions.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input and Response Handling ---
if prompt := st.chat_input("Ask me anything..."):
    # Add user's message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display agent's response
    with st.chat_message("assistant"):
        # Use a spinner to indicate that the agent is working.
        with st.spinner("Thinking..."):
            try:
                # The main call to the agent executor.
                response = agent_executor.invoke({"input": prompt})
                # Extract the final answer from the agent's output.
                final_answer = response.get("output", "Sorry, I encountered an error.")
                st.markdown(final_answer)
                # Add agent's response to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_answer})

            except Exception as e:
                error_message = f"An error occurred: {e}. Please try again."
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# How to run?
# pip install streamlit langchain langchain-openai duckduckgo-search
# streamlit run app.py