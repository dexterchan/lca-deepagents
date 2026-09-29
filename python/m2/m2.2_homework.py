# python/m2/m2.2_homework.py
"""M2.2 Homework: Configure Your Own Filesystem Backend.

THE IDEA
The lab wired up one fixed setup: a CompositeBackend routing a single
reference file to local disk with a permission rule denying all writes
to it. This homework asks you to pick your own small file-based task and
configure a backend for it however you like: StateBackend,
FilesystemBackend, or a CompositeBackend mixing both. There's no single
right backend or topic here, that's the point. Two students doing this
homework could end up with completely different setups.

WHAT YOU FILL IN
  TODO 1: pick a topic for a small text file (a packing list, a journal,
    a recipe box, meeting notes, whatever), seed it with some starting
    content the same way the lab pre-populates reference/chinook-sales.md,
    and configure ANY backend you like for the agent to use.
  TODO 2: write a task message that has the agent read your file and then
    write or edit it in some way, and (optionally) add one or more
    FilesystemPermission rules that change what the agent is allowed to
    do to it.

RUN
  cd python
  uv run ./m2/m2.2_homework.py
"""

from pathlib import Path

from deepagents import FilesystemMiddleware, FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from models import model

# ════════════════════════════════════════════════════════════════════════
# TODO 1: Configure a backend for a topic of your choosing.
#
# Requirements:
#   - Pick a small file-based task: a packing list, a journal, a recipe
#     box, meeting notes, whatever fits your topic.
#   - Create a seed file (or files) with some starting content, the same
#     way the lab pre-populates reference/chinook-sales.md.
#   - Configure ANY backend you like: StateBackend(), FilesystemBackend(),
#     or a CompositeBackend() routing between them. It does not need to
#     match the lab's setup.
#
# Example shape (delete this and write your own):
#   my_dir = Path(__file__).parent / "my_files"
#   my_dir.mkdir(exist_ok=True)
#   (my_dir / "notes.md").write_text("...")
#   backend = FilesystemBackend(root_dir=str(my_dir), virtual_mode=True)
# ════════════════════════════════════════════════════════════════════════
reference_dir:str = Path(__file__).parent / "reference"
reference_dir.mkdir(exist_ok=True)

backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/reference/": FilesystemBackend(
                root_dir=str(reference_dir),
                virtual_mode=True,
            ),
        },
    )  # TODO 1: replace with a StateBackend, FilesystemBackend, or CompositeBackend

with open(reference_dir / "my_file.txt", "w") as f:
    f.write("This is my initial content for the file-based task.\n")  
    f.write("You can add more lines or edit this content as needed.\n")
    f.write("Feel free to customize this file for your specific task.\n")
    f.write("This is a sample line to demonstrate the file's content.\n")

# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write the task, and optionally a permission rule.
#
# Write a user message that has the agent read your file, then write or
# edit it. If you want to demonstrate permissions, add one or more
# FilesystemPermission rules to the permissions list below. Leaving it
# empty and skipping permissions entirely is also a valid choice.
# ════════════════════════════════════════════════════════════════════════

TASK = """
       Search for file "/reference/my_file.txt"
       Read the file /reference/my_file.txt.
       then write a child bed time story in 100 words and append to the same file. 
       The story should be about a brave little rabbit who goes on an adventure in the forest and learns an important lesson about friendship and courage. Make sure the story is engaging, age-appropriate, and has a positive message for young readers.
       """

permissions: list[FilesystemPermission] = [
    FilesystemPermission(
                operations=["write"],
                paths=["/reference/**"],
                mode="allow",
            )
]  # TODO 2 (optional): add rules here

if backend is None:
    raise NotImplementedError("TODO 1: see the comment block above")
if TASK is None:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    backend=backend,
    #middleware=[FilesystemMiddleware(tools=["read_file", "write_file", "edit_file", "grep", "ls", "glob", "grep"])],
    permissions=permissions,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": TASK}]},
    config={"configurable": {"thread_id": "homework-m2.2"}},
)

print(result["messages"][-1].content)
