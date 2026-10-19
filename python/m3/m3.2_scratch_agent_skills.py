from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from models import model
import uuid

m3_dir = Path(__file__).parent
backend = FilesystemBackend(root_dir=str(m3_dir), virtual_mode=True)

agent = create_deep_agent(
    model=model,
    name="Sales_Assistant",
    backend=backend,
    skills=["/skills"],
    system_prompt="You are a sales assistant.",
)

THREAD = {"configurable": {"thread_id": "demo"}}

# Passing our own run_id lets us find this run in LangSmith afterwards.
# This is the top-level (root) run, so LangSmith reuses it as the trace ID:
# in the GUI, filter by `trace_id` (not run ID) and paste the printed value.
run_id = uuid.uuid4()
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Qualify this lead: Acme Corp, 200-person logistics company. I spoke with Sarah Chen, VP of Sales: she's the decision maker. They have $45k budgeted for CRM this year. Main pain: deals are slipping through the cracks due to poor pipeline visibility. They want a solution live by end of Q3."}]},
    config={**THREAD, "run_id": run_id}
    )
print(result["messages"][-1].content)
print(f"Run ID: {run_id}")