
import asyncio
import inspect
from google.adk import Agent
from google.adk.agents import SequentialAgent

print(f"Agent.run is async gen: {inspect.isasyncgenfunction(Agent.run)}")
print(f"SequentialAgent.run is async gen: {inspect.isasyncgenfunction(SequentialAgent.run)}")

async def test():
    # Create a dummy agent
    agent = SequentialAgent(name="test", sub_agents=[], description="test")
    # Check what run returns (mocking if needed, but static analysis is safer first)
    pass

if __name__ == "__main__":
    pass
