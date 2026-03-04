import asyncio
from orchestrator import Orchestrator

async def run_test():
    print("Starting manual intel collection test...")
    orc = Orchestrator()
    res = await orc.run_intel_collection_once()
    print("Final Result:", res)

if __name__ == '__main__':
    asyncio.run(run_test())
