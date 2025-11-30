"""
Agent definitions for the AI-Powered Package Conflict Resolver.
Defines Query Creator, Web Search, Web Crawl, and CodeSurgeon agents.
"""
import sys
import asyncio
import json
from typing import Any

# Fix for Playwright on Windows (NotImplementedError in subprocess)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from google.adk import Agent
from google.adk.agents import SequentialAgent, ParallelAgent
# from google.adk.events import Event, EventActions # Unused after removing loop
from google.adk.tools import google_search, load_memory, FunctionTool
from .config import get_model, get_gemini_model
from .tools import batch_tool, adaptive_tool, save_context_tool, retrieve_context_tool, submit_queries_tool, validate_tool, retrieve_memory_tool
from .utils import logger


def create_query_creator_agent():
    """
    Creates the Query Creator agent (Dependency Detective).
    Generates search queries based on the user's problem.
    """
    agent = Agent(
        name="Query_Creator_Agent",
        model=get_gemini_model(),
        tools=[google_search], # used google_search to avoid conflict with custom tools
        description="Dependency Detective specialized in diagnosing software environment conflicts",
        instruction="""
        You are the "Dependency Detective," an expert AI agent specialized in diagnosing software environment conflicts, legacy code rot, and version mismatch errors.
        Use Google Search Tool if You don't Know about those issue or packages.
        Use `retrieve_memory` to recall details from previous conversations if the user refers to "last time" or "previous error".

        YOUR GOAL:
        1. Analyze the input to identify the specific packages involved (e.g., "tensorflow", "react", "spring-boot").
        2. Save these package names to the session state using `save_context('packages', 'package1, package2')`.
        3. Generate a list of targeted, technical search queries that will help a downstream "Web Crawler" find the exact solution.

        INPUT YOU WILL RECEIVE:
        1. A list of packages (e.g., "tensorflow, keras" or "react, next.js").
        2. An error log or description.

        YOUR ANALYSIS PROCESS:
        1. Extract the package names and versions from the input.
        2. Call `save_context('packages', 'extracted_package_list')`.
        3. Analyze the Error: Is it a syntax error or a compatibility error? Look for keywords like "deprecated", "mismatch", "attribute error".
        4. Analyze the Stack: Look at the libraries involved.
        5. Hypothesize Conflicts: Generate search queries that target:
           - "Breaking changes" in the libraries mentioned.
           - "Migration guides" for the specific error.
           - "Compatibility matrices" for the package combinations.

        OUTPUT FORMAT:
        Start your response with:
        **Model: Gemini 2.0 Flash Lite**
        ## Search Queries
        
        Return a raw JSON list of strings in your text response.
        Return a raw JSON list of strings in your text response.
        Example: ["numpy.float deprecated version", "react hook dependency warning"]
        """
    )
    logger.info("✅ Query Creator agent created")
    return agent


def create_docs_search_agent():
    """
    Creates the Docs Search agent (Official Documentation).
    """
    agent = Agent(
        name="Docs_Search_Agent",
        model=get_gemini_model(),
        tools=[google_search],
        description="Search agent focused on official documentation",
        instruction="""
        You are the "Official Docs Researcher".
        
        YOUR GOAL:
        Search for official documentation, API references, and migration guides.
        Focus on domains like *.org, *.io, *.dev, and official GitHub repositories.
        
        INPUT: List of search queries.
        OUTPUT: Top 4 most relevant OFFICIAL URLs.
        
        OUTPUT FORMAT:
        **Model: Gemini 2.5 Pro**
        ## Official Docs Results
        {"top_urls": ["url1", "url2", ...]}
        """
    )
    logger.info("✅ Docs Search agent created")
    return agent

def create_community_search_agent():
    """
    Creates the Community Search agent (StackOverflow, GitHub Issues).
    """
    agent = Agent(
        name="Community_Search_Agent",
        model=get_gemini_model(),
        tools=[google_search],
        description="Search agent focused on community discussions",
        instruction="""
        You are the "Community Researcher".
        
        YOUR GOAL:
        Search for community discussions, bug reports, and stackoverflow threads.
        Focus on sites like stackoverflow.com, github.com/issues, reddit.com.
        
        INPUT: List of search queries.
        OUTPUT: Top 4 most relevant COMMUNITY URLs.
        
        OUTPUT FORMAT:
        **Model: Gemini 2.5 Pro**
        ## Community Results
        {"top_urls": ["url1", "url2", ...]}
        """
    )
    logger.info("✅ Community Search agent created")
    return agent

def create_context_search_agent():
    """
    Creates the Context Search agent (General Context).
    """
    agent = Agent(
        name="Context_Search_Agent",
        model=get_gemini_model(),
        tools=[google_search],
        description="Search agent focused on general context and main URL",
        instruction="""
        You are the "Context Researcher".
        
        YOUR GOAL:
        YOUR GOAL:
        1. Analyze the input search queries to identify the "Main Topic" or "Core Library/Framework" (e.g., if input is "numpy float error", main topic is "numpy").
        2. Search for the Home Page, Main Documentation Hub, or Wikipedia page for this Main Topic.
        3. Provide the top 3-4 most authoritative URLs for this topic.
        
        INPUT: List of search queries.
        OUTPUT: Top 3-4 most relevant URLs.
        
        OUTPUT FORMAT:
        **Model: Gemini 2.5 Pro**
        ## Context Results
        {"top_urls": ["url1", "url2", "url3"]}
        """
    )
    logger.info("✅ Context Search agent created")
    return agent


class WebCrawlAgent(Agent):
    """
    Custom Agent for Web Crawling that deterministically tries batch crawl first,
    then falls back to adaptive crawl if needed.
    """
    def __init__(self, model, tools, **kwargs):
        super().__init__(model=model, tools=tools, **kwargs)
        
    async def run(self, input_str: str, **kwargs):
        """
        Custom run logic:
        1. Parse input to get URLs.
        2. Try batch_crawl_tool.
        3. Check results.
        4. If poor results, try adaptive_crawl_tool.
        """
        logger.info(f"🕷️ WebCrawlAgent received input: {input_str}")
        
        # Simple heuristic to extract URLs (assuming input is JSON or list-like string)
        # In a real scenario, we might use the LLM to parse it first if it's unstructured.
        # For now, we'll assume the previous agent passed a list of URLs or we can regex them.
        import re
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', input_str)
        
        if not urls:
            return "No URLs found to crawl."
            
        # 1. Try Batch Crawl
        logger.info(f"🕷️ Attempting Batch Crawl for {len(urls)} URLs")
        batch_result = await batch_tool.func(urls)
        
        # 2. Analyze Result (Simple Heuristic)
        # Check if we got valid content
        content = batch_result.get("combined_content", "")
        
        # If result contains many "Error" or is very short, we might need adaptive
        if "Error" not in content and len(content) > 500:
             return f"**Model: Custom Logic**\n## Crawled Content Analysis\n\n{content}"
             
        # 3. Fallback to Adaptive (if batch failed significantly)
        logger.info("⚠️ Batch crawl had issues. Falling back to Adaptive Crawl for first URL...")
        # For simplicity in this custom agent, we just try the first URL adaptively as a fallback
        adaptive_result = await adaptive_tool.func(urls[0], query="dependency conflicts version requirements")
        
        # Format adaptive result (it's a dict)
        formatted_adaptive = json.dumps(adaptive_result, indent=2) if isinstance(adaptive_result, dict) else str(adaptive_result)
        
        return f"**Model: Custom Logic (Adaptive Fallback)**\n## Crawled Content Analysis\n\n{formatted_adaptive}"

def create_web_crawl_agent():
    """
    Creates the Web Crawl agent (Content Extractor).
    Now uses the Custom WebCrawlAgent class.
    """
    # We pass tools=[] to the parent Agent so the LLM doesn't see them and try to call them.
    # The custom run() method will use the tools directly.
    agent = WebCrawlAgent(
        name="Web_Crawl_Agent",
        model=get_model(),
        tools=[], # HIDE TOOLS FROM LLM to prevent hallucinated/parallel calls
        description="Technical Content Extractor using Deterministic Logic",
        instruction="""
        You are the "Technical Content Extractor".
        
        (Note: This instruction is less critical now as the custom run method handles the logic,
        but kept for metadata purposes).
        """
    )
    logger.info("✅ Web Crawl agent created (Custom Class)")
    return agent


def create_code_surgeon_agent():
    """
    Creates the CodeSurgeon agent that fixes dependency issues.
    """
    agent = Agent(
        name="Code_Surgeon_Agent",
        model=get_model(),
        tools=[retrieve_context_tool, save_context_tool],
        description="Expert Software Developer specialized in dependency resolution",
        instruction="""
        You are the "Code Surgeon".

        YOUR TASK:
        1. Use 'retrieve_context' to get the 'packages' and 'versions' stored by the Query Creator.
        2. Analyze the dependency conflicts provided by the user.
        3. Based on the research findings from the Web Crawl Agent, determine the correct versions.
        3. Generate a clean dependency configuration file (e.g., requirements.txt, package.json, pom.xml) with resolved dependencies.
        4. Provide an explanation of what was fixed and why.

        OUTPUT FORMAT:
        - Clear explanation of the issue
        - Updated dependency file content
        - Migration notes (if breaking changes exist)
        
        IMPORTANT:
        - Call `save_context('solution', 'YOUR_SOLUTION_SUMMARY')` to store the final resolution.
        - Call `save_context('requirements', 'YOUR_REQUIREMENTS_CONTENT')` to store the file content.
        """
    )
    logger.info("✅ Code Surgeon agent created")
    return agent


# ===== MEMORY SERVICE =====
from .config import get_memory_service
global_memory_service = get_memory_service()

# ===== MEMORY CALLBACK =====
async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    try:
        # Use global memory service instead of context-bound one
        await global_memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )
        logger.info("💾 Session automatically saved to memory (Global Service).")
    except Exception as e:
        logger.error(f"❌ Failed to auto-save session: {e}")


def create_memory_retrieval_agent():
    """
    Creates the Memory Retrieval agent.
    Checks past sessions for similar issues.
    """
    agent = Agent(
        name="Memory_Retrieval_Agent",
        model=get_model(), # Use Grok or Gemini (Grok is fine for retrieval)
        tools=[retrieve_memory_tool],
        description="Agent that searches long-term memory for past solutions",
        instruction="""
        You are the "Memory Specialist".
        
        YOUR GOAL:
        1. Analyze the user's input (error logs, package names).
        2. Use `retrieve_memory` to search for similar past resolved sessions.
        3. Summarize any relevant findings.
        
        OUTPUT:
        - If relevant memory found: "Found similar past issue: [Summary]. Solution was: [Solution]"
        - If no memory found: "No relevant past issues found."
        """
    )
    logger.info("✅ Memory Retrieval agent created")
    return agent



def create_root_agent():
    """
    Creates the root agent (Manager Agent).
    Uses the Resolution Pipeline as a TOOL to handle technical requests.
    """
    # 1. Memory Retrieval
    memory_agent = create_memory_retrieval_agent()

    # 2. Research Team
    query_creator = create_query_creator_agent()
    
    docs_search = create_docs_search_agent()
    community_search = create_community_search_agent()
    context_search = create_context_search_agent()
    
    # Parallel Research
    parallel_search = ParallelAgent(
        name="Parallel_Search_Team",
        sub_agents=[docs_search, community_search, context_search],
        description="Parallel search for official, community, and general context resources"
    )
    
    # Group Research Team
    web_research_team = SequentialAgent(
        name="Web_Research_Team",
        sub_agents=[query_creator, parallel_search],
        description="Team responsible for researching dependency issues"
    )
    
    web_crawl = create_web_crawl_agent()
    
    # Code Surgeon
    code_surgeon = create_code_surgeon_agent()
    
    # Create the sequential pipeline (The "Heavy" Lifters)
    resolution_pipeline = SequentialAgent(
        name="Resolution_Pipeline",
        sub_agents=[memory_agent, web_research_team, web_crawl, code_surgeon],
        description="Sequential pipeline for resolving dependency issues",
        after_agent_callback=auto_save_to_memory # Auto-save history
    )
    
    # --- NEW: Wrap Pipeline as a Tool ---
    async def run_resolution_job(problem_description: str) -> str:
        """
        Triggers the full dependency resolution pipeline.
        Use this tool when the user describes a technical issue, error, or package conflict.
        """
        logger.info(f"🔧 Manager triggering Resolution Pipeline for: {problem_description}")
        return await resolution_pipeline.run_async(problem_description)

    resolution_tool = FunctionTool(run_resolution_job)

    # --- NEW: Manager Agent (The Doctor) ---
    manager_agent = Agent(
        name="Package_Doctor_Manager",
        model=get_gemini_model(), # Smart model for decision making
        tools=[resolution_tool],
        description="The main interface for the Package Doctor.",
        instruction="""
        You are the **Package Doctor**, an expert AI assistant for Python dependency issues.

        YOUR BEHAVIOR:
        1. **Small Talk**: If the user says "Hello", "Hi", or asks general questions, reply politely and briefly. DO NOT call any tools.
           - Example: "Hello! I'm ready to help you fix your dependency conflicts. Please share your error log or requirements file."

        2. **Technical Issues**: If the user describes a problem, provides an error log, or mentions package conflicts, **IMMEDIATELY** call the `run_resolution_job` tool.
           - Pass the user's full description to the tool.
           - Do not try to solve it yourself without the tool.

        3. **After Tool Execution**: The tool will return the solution. Present it clearly to the user.
        """
    )
    
    logger.info("✅ Root agent created (Manager with Pipeline Tool)")
    return manager_agent


# ===== MODULE-LEVEL INITIALIZATION FOR ADK WEB =====
root_agent = create_root_agent()

# Removed App definition to avoid ImportError. 
# Memory is handled via global_memory_service in callback.
agent = root_agent
