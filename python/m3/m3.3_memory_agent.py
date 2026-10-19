# Recap
# - Memory is not thread history; checkpointers preserve thread history
# - Memory is persistent knowledge stored as files
# - memory=[...] activates MemoryMiddleware for those files
# - Loaded memory is injected into the system prompt inside <agent_memory>
# - Agents update memory by editing memory files
# - The /memories/ backend route determines persistence; the StoreBackend
#   namespace determines scope

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

from models import model

store = InMemoryStore()
memory_path = "/memories/AGENTS.md"
store_memory_path = "/AGENTS.md"
demo_context = {"workspace_id": "acme", "user_id": "u_alex"}


def namespace_from_context(context):
    return (
        "memory",
        context["workspace_id"],
        context["user_id"],
    )


def memory_namespace(runtime):
    return namespace_from_context(runtime.context)


store.put(
    namespace_from_context(demo_context),
    store_memory_path,
    create_file_data("""\
# Project Guidelines

## Code Style
- All functions must have type annotations
- Use f-strings for string formatting
- Maximum line length is 88 characters
- Use `pathlib.Path` for file operations, not `os.path`

## Workflow
- Run tests with: `uv run pytest`
- The CI pipeline runs on every push to `main`
- Open a draft PR early so reviewers can follow along
"""),
)

# StateBackend vs StoreBackend:
# - StateBackend keeps files in the agent's graph state. They live only inside
#   one thread (conversation) and are gone when a new thread starts. Good for
#   scratch / working files.
#   Saving state between invokes is the checkpointer's job, and
#   create_deep_agent's default is checkpointer=None (not in-memory). With
#   no checkpointer, StateBackend files last for a single invoke only, even
#   on the same thread_id. Pass checkpointer=InMemorySaver() (or a durable
#   one) to keep them across invokes. `langgraph dev` / LangGraph Platform
#   add a checkpointer for you.
# - StoreBackend keeps files in the LangGraph Store passed as `store=`. They
#   survive across threads. `namespace` decides whose files they are (here: per
#   workspace + user, taken from the `context` passed to invoke).
#   StoreBackend itself is only an adapter: it turns file operations into
#   store.get/put calls. Where the data really lives depends on the store.
#   Here that is InMemoryStore, so "persistent" memory still lives in this
#   Python process and is lost when the script exits. Swap in a durable
#   store (e.g. PostgresStore) to keep it across restarts.
# CompositeBackend picks a backend by path prefix: anything under /memories/
# goes to the StoreBackend, everything else falls back to the StateBackend.
# The route prefix is stripped before saving, so the agent's
# "/memories/AGENTS.md" is stored under the key "/AGENTS.md".
agent = create_deep_agent(
    model=model,
    name="Memory_Agent",
    backend=CompositeBackend(
        default=StateBackend(),
        routes={"/memories/": StoreBackend(namespace=memory_namespace)},
    ),
    store=store,
    memory=[memory_path],
    system_prompt="You are a helpful coding assistant for this project.",
)

# First invoke: agent answers using memory content
result = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "What tool should I use for file paths in this project?"}
        ]
    },
    context=demo_context,
)
print("--- Question 1 ---")
print(result["messages"][-1].content)

# Second invoke: agent writes to memory
result2 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Remember: the team switched to ruff for linting. Update your memory.",
            }
        ]
    },
    context=demo_context,
)
print("\n--- Question 2 ---")
print(result2["messages"][-1].content)

print("\n--- AGENTS.md after write ---")
stored_memory = store.get(namespace_from_context(demo_context), store_memory_path)
print(stored_memory.value["content"])

