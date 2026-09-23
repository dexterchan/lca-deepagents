import os
from uuid import uuid4

from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from deepagents import create_deep_agent
from langchain_agentcore_codeinterpreter import AgentCoreSandbox

from models import model

region = os.environ.get("AWS_REGION", "us-east-1")
interpreter = CodeInterpreter(region)
session_id = interpreter.start(name=f"lca-deepagents-lab-{uuid4().hex[:8]}")

print(f"Sandbox session: {session_id}  (region: {region})")
backend = AgentCoreSandbox(interpreter=interpreter)

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt=(
        "You are a coding assistant. When asked to run code, write the script "
        "to a file first, then execute it. Show the output in your final answer."
    ),
)

try:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a Python script that prints the first 15 Fibonacci numbers, "
                        "save it to fib.py, and run it."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)
finally:
    interpreter.stop()
