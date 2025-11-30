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
from google.adk.tools import google_search, load_memory, FunctionTool, ToolContext
from google.adk.agents.invocation_context import InvocationContext
from .config import get_model, get_gemini_model
from .tools import batch_tool, adaptive_tool, save_context_tool, retrieve_context_tool, submit_queries_tool, validate_tool, retrieve_memory_tool
from .utils import logger
import uuid
from .config import get_session_service
from google.adk.agents.run_config import RunConfig


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
        Return ONLY a raw JSON list of URLs. Do not include any markdown formatting, headings, or conversational text.
        Example: ["https://docs.python.org/3/", "https://pypi.org/project/requests/"]
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
        Return ONLY a raw JSON list of URLs. Do not include any markdown formatting, headings, or conversational text.
        Example: ["https://stackoverflow.com/questions/12345", "https://github.com/issues/6789"]
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
        Return ONLY a raw JSON list of URLs. Do not include any markdown formatting, headings, or conversational text.
        Example: ["https://numpy.org", "https://pypi.org/project/numpy/"]
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
        import re
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', str(input_str))
        
        if not urls:
            return "No URLs found to crawl."
            
        # 1. Try Batch Crawl
        logger.info(f"🕷️ Attempting Batch Crawl for {len(urls)} URLs")
        try:
            batch_result = await batch_tool.func(urls)
            
            # 2. Analyze Result (Simple Heuristic)
            content = batch_result.get("combined_content", "")
            
            # If result contains many "Error" or is very short, we might need adaptive
            if "Error" not in content and len(content) > 500:
                 return f"**Model: Custom Logic**\n## Crawled Content Analysis\n\n{content}"
            
            # 3. Fallback to Adaptive
            logger.info("⚠️ Batch crawl had issues. Falling back to Adaptive Crawl for first URL...")
            adaptive_result = await adaptive_tool.func(urls[0], query="dependency conflicts version requirements")
            formatted_adaptive = json.dumps(adaptive_result, indent=2) if isinstance(adaptive_result, dict) else str(adaptive_result)
            return f"**Model: Custom Logic (Adaptive Fallback)**\n## Crawled Content Analysis\n\n{formatted_adaptive}"
            
        except Exception as e:
            logger.error(f"❌ WebCrawlAgent Error: {e}")
            return f"Error during crawling: {str(e)}"

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
        2. Use `retrieve_memory` ONCE to search for similar past resolved sessions.
        3. Summarize any relevant findings.
        
        CRITICAL INSTRUCTION:
        - Call `retrieve_memory` ONLY ONCE.
        - If the tool returns "No relevant memories found", DO NOT RETRY. Immediately report "No relevant past issues found." and stop.
        - Do not attempt to rephrase the query and search again.
        
        OUTPUT:
        - If relevant memory found: "Found similar past issue: [Summary]. Solution was: [Solution]"
        - If NO relevant memory found: "No relevant past issues found."
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
    
    logger.info("✅ Root agent created (Resolution Pipeline)")
    return resolution_pipeline


# ===== MODULE-LEVEL INITIALIZATION FOR ADK WEB =====
root_agent = create_root_agent()

# Removed App definition to avoid ImportError. 
# Memory is handled via global_memory_service in callback.
agent = root_agent
