"""
Agent definitions for the AI-Powered Package Conflict Resolver.
Defines Query Creator, Web Search, Web Crawl, and CodeSurgeon agents.
"""
from google.adk import Agent
from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent, ParallelAgent
from google.adk.events import Event, EventActions
from google.adk.tools import google_search, load_memory
from .config import get_model, get_gemini_model
from .tools import batch_tool, adaptive_tool, save_context_tool, retrieve_context_tool, submit_queries_tool, validate_tool
from .utils import logger


def create_query_creator_agent():
    """
    Creates the Query Creator agent (Dependency Detective).
    Generates search queries based on the user's problem.
    """
    agent = Agent(
        name="Query_Creator_Agent",
        model=get_gemini_model(),
        tools=[google_search, save_context_tool, load_memory], # Added load_memory
        description="Dependency Detective specialized in diagnosing Python environment conflicts",
        instruction="""
        You are the "Dependency Detective," an expert AI agent specialized in diagnosing Python environment conflicts, legacy code rot, and version mismatch errors.
        Use Google Search Tool if You don't Know about those issue or packages.
        Use `load_memory` to recall details from previous conversations if the user refers to "last time" or "previous error".

        YOUR GOAL:
        1. Analyze the input to identify the specific packages involved (e.g., "tensorflow", "numpy").
        2. Save these package names to the session state using `save_context('packages', 'package1, package2')`.
        3. Generate a list of targeted, technical search queries that will help a downstream "Web Crawler" find the exact solution.

        INPUT YOU WILL RECEIVE:
        1. A list of packages (e.g., "tensorflow, keras, numpy").
        2. An error log or description (e.g., "int32 and float mismatch").

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
        Example: ["numpy.float deprecated version", "tensorflow 2.x keras version incompatibility"]
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
        batch_result = await batch_crawl_tool.func(urls)
        
        # 2. Analyze Result (Simple Heuristic)
        # If result contains many "Error" or is very short, we might need adaptive
        if "Error" not in batch_result and len(batch_result) > 500:
             return f"**Model: Custom Logic**\n## Crawled Content Analysis\n\n{batch_result}"
             
        # 3. Fallback to Adaptive (if batch failed significantly)
        logger.info("⚠️ Batch crawl had issues. Falling back to Adaptive Crawl for first URL...")
        # For simplicity in this custom agent, we just try the first URL adaptively as a fallback
        adaptive_result = await adaptive_tool.func(urls[0], query="dependency conflicts version requirements")
        
        return f"**Model: Custom Logic (Adaptive Fallback)**\n## Crawled Content Analysis\n\n{adaptive_result}"

def create_web_crawl_agent():
    """
    Creates the Web Crawl agent (Content Extractor).
    Now uses the Custom WebCrawlAgent class.
    """
    agent = WebCrawlAgent(
        name="Web_Crawl_Agent",
        model=get_model(),
        tools=[batch_tool, adaptive_tool],
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
        description="Expert Python developer specialized in dependency resolution",
        instruction="""
        You are the "Code Surgeon".

        YOUR TASK:
        1. Use 'retrieve_context' to get the 'packages' and 'versions' stored by the Query Creator.
        2. Analyze the dependency conflicts provided by the user.
        3. Based on the research findings from the Web Crawl Agent, determine the correct versions.
        3. Generate a clean requirements.txt with resolved dependencies.
        4. Provide an explanation of what was fixed and why.

        OUTPUT FORMAT:
        - Clear explanation of the issue
        - Updated requirements.txt content
        - Migration notes (if breaking changes exist)
        """
    )
    logger.info("✅ Code Surgeon agent created")
    return agent


def create_verification_agent():
    """
    Creates the Verification agent that checks the Code Surgeon's work.
    """
    agent = Agent(
        name="Verification_Agent",
        model=get_model(),
        tools=[validate_tool, save_context_tool],
        description="Quality Assurance specialist for dependency files",
        instruction="""
        You are the "Quality Assurance Specialist".
        
        YOUR TASK:
        1. Review the 'requirements.txt' content generated by the Code Surgeon.
        2. Use the `validate_requirements` tool to check for syntax errors.
        3. If the tool returns "SUCCESS":
           - Call `save_context('verification_status', 'SUCCESS')`.
           - Respond with "Verification Passed".
        4. If the tool returns errors:
           - Call `save_context('verification_status', 'FAILED')`.
           - Explain the errors to the Code Surgeon so they can fix it.
        """
    )
    logger.info("✅ Verification agent created")
    return agent


class StopCheckerAgent(BaseAgent):
    """
    Agent that checks the verification status and stops the loop if successful.
    """
    async def _run_async_impl(self, ctx):
        # Retrieve status from session state
        status = ctx.session.state.get("verification_status", "FAILED")
        logger.info(f"🛑 StopChecker: Status is {status}")
        
        should_stop = (status == "SUCCESS")
        if should_stop:
            logger.info("🛑 StopChecker: Escalating to stop loop.")
            
        # Yield an event with escalate=True if we should stop
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))


# ===== MEMORY CALLBACK =====
async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    try:
        await callback_context._invocation_context.memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )
        logger.info("💾 Session automatically saved to memory.")
    except Exception as e:
        logger.error(f"❌ Failed to auto-save session: {e}")


def create_root_agent():
    """
    Creates the root agent that orchestrates the sub-agents.
    """
    # Create sub-agents
    query_creator = create_query_creator_agent()
    # load_memory removed due to model limitations
    
    docs_search = create_docs_search_agent()
    community_search = create_community_search_agent()
    
    # Parallel Research
    parallel_search = ParallelAgent(
        name="Parallel_Search_Team",
        sub_agents=[docs_search, community_search],
        description="Parallel search for official and community resources"
    )
    
    # Group Research Team
    web_research_team = SequentialAgent(
        name="Web_Research_Team",
        sub_agents=[query_creator, parallel_search],
        description="Team responsible for researching dependency issues"
    )
    
    web_crawl = create_web_crawl_agent()
    web_crawl = create_web_crawl_agent()
    
    # Code Surgeon Loop
    code_surgeon = create_code_surgeon_agent()
    verification = create_verification_agent()
    stop_checker = StopCheckerAgent(name="Stop_Checker")
    
    code_surgeon_team = LoopAgent(
        name="Code_Surgeon_Team",
        sub_agents=[code_surgeon, verification, stop_checker],
        max_iterations=3,
        description="Self-correcting dependency resolution team"
    )
    
    # Create the sequential agent
    agent = SequentialAgent(
        name="Package_Conflict_Resolver_Root_Agent",
        sub_agents=[web_research_team, web_crawl, code_surgeon_team],
        description="Root agent managing the dependency resolution pipeline",
        after_agent_callback=auto_save_to_memory # Auto-save history
    )
    logger.info("✅ Root agent created with sequential flow (Research Team -> Crawl -> Surgeon)")
    return agent


# ===== MODULE-LEVEL INITIALIZATION FOR ADK WEB =====
root_agent = create_root_agent()
