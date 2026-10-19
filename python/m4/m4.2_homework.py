# python/m4/m4.2_homework.py
"""M4.2 Homework: Give Each Subagent Its Own Scoped Scratch Folder.

THE IDEA
The lab's genre-researcher subagents each wrote raw search notes to their own
assigned /research/<genre>/ folder, kept out of the editor's context by
FilesystemPermission scoping: researchers could write under /research/**, the
editor could not.

This homework asks you to build a small team of 2 subagent types for
a domain YOU pick (e.g., trip planning, home renovation), each with
its own private, permission-scoped folder under /scratch/<name>/ to
stash raw notes in before answering. The harness below wires up the scratch
folder, the permissions, and the write-before-answering instruction for you;
you just decide who your two subagents are.

WHAT YOU FILL IN
  TODO 1: for each of the two entries in SUBAGENT_SPECS, fill in "name",
    "description" (when the main agent should call it), and "role_prompt"
    (who this subagent is and what its job is). Everything else -- the
    scratch folder, the permissions, the instruction to save raw notes
    before answering -- is handled for you.
  TODO 2: write the main agent's system prompt, telling it which subagent
    to call for which part of the job, and a user request that should
    trigger delegation to BOTH subagents.

RUN
  cd python
  uv run ./m4/m4.2_homework.py
"""
import uuid
from deepagents import FilesystemPermission, create_deep_agent

from models import model, strong_model

SCRATCH_ROOT = "/scratch"


def scratch_path(subagent_name: str) -> str:
    return f"{SCRATCH_ROOT}/{subagent_name}/notes.md"


def scratch_permissions(subagent_name: str) -> list:
    """Scope a subagent to write only under its own scratch folder -- the same
    first-match-wins allow-then-deny pattern the lab used for
    research_permissions/editor_permissions."""
    return [
        FilesystemPermission(operations=["read", "write"], paths=[f"{SCRATCH_ROOT}/{subagent_name}/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]


def scratch_instruction(subagent_name: str) -> str:
    return (
        f'Before you answer, call write_file on "{scratch_path(subagent_name)}" '
        "with your raw notes or reasoning. Then give your final answer using "
        "only the polished result -- do not repeat those raw notes in your reply."
    )


def build_subagents(specs: list[dict]) -> list[dict]:
    team = []
    for spec in specs:
        name = spec["name"]
        team.append(
            {
                "name": name,
                "description": spec["description"],
                "system_prompt": spec["role_prompt"] + "\n\n" + scratch_instruction(name),
                "permissions": scratch_permissions(name),
            }
        )
    return team


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Fill in your two subagents.
#
# For each entry: "name" is the handle the main agent calls it by, kebab-
# case (e.g. "flight-finder"). "description" is how the main agent decides
# which one to use. "role_prompt" is that subagent's own job description --
# don't mention scratch files or write_file here, that's added for you.
# ════════════════════════════════════════════════════════════════════════

SUBAGENT_SPECS = [
    {
        "name": "climate-researcher",
        "description": (
            "Research the climate and seasonal weather for a destination and "
            "travel window. Delegate one destination per call; returns what "
            "to expect, what to pack, and which outdoor activities are viable "
            "in those dates."
        ),
        "role_prompt": (
            "You are a climate researcher on a travel planning team. You will "
            "be given a destination, the travel dates or season, and who is "
            "traveling. Draw on your knowledge of that place's weather: "
            "typical day and night temperatures in that window, rain or "
            "heat, and notable seasonal events (e.g., cherry-blossom timing, "
            "typhoon season). If the exact dates are missing, assume the "
            "season the request most likely refers to and state the "
            "assumption. Return ONLY a polished summary of 4-6 short "
            "bullets: what the weather will feel like, what to pack, and "
            "which outdoor activities are viable or risky in that window. "
            "Do not return raw notes, and do not ask questions."
        ),
    },
    {
        "name": "attraction-researcher",
        "description": (
            "Research the best places of interest in a given city for a "
            "stated group and number of days. Delegate one city per call; "
            "returns a shortlist grouped for day-by-day planning."
        ),
        "role_prompt": (
            "You are a travel guide on a travel planning team. You will be "
            "given a city, the number of days, the size and make-up of the "
            "group (e.g., a family with children), and any interests they "
            "mention. Draw on your knowledge of the city and return ONLY a "
            "polished shortlist of 8-12 places that fit this group, each "
            "with a one-line reason it fits, grouped roughly by area or day "
            "so an itinerary can be built around them. Flag anything that "
            "needs advance booking or has long queues. Do not return raw "
            "notes, and do not ask questions."
        ),
    },
    {
        "name": "route-planner",
        "description": (
            "Plan realistic transport in a destination: airport to hotel and "
            "day-to-day movement between areas, for a stated group and "
            "budget. Delegate one destination per call; returns routes with "
            "durations and rough costs."
        ),
        "role_prompt": (
            "You are a transit planner on a travel planning team. You will "
            "be given a destination city, the group size, and any time or "
            "budget constraints. Draw on your knowledge of how people "
            "actually get around there and return ONLY a polished transit "
            "plan: the best way from the main airport into the city, how to "
            "move between the city's main areas day to day (recommended "
            "mode, approximate duration, rough cost per leg), and one or "
            "two tips on passes or first-day logistics. Do not return raw "
            "notes, and do not ask questions."
        ),
    },
]


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write the main agent's system prompt and a triggering request.
#
# MAIN_PROMPT should tell the main agent about each subagent by name and
# when to call it (mirror how EDITOR_PROMPT in the lab named
# genre-researcher and explained the job).
# USER_REQUEST should be a task that should make the main agent delegate to
# BOTH of your subagents.
# ════════════════════════════════════════════════════════════════════════

MAIN_PROMPT = """You are Trip Planner, the lead of a small travel research team.
You coordinate and assemble — you never do the research yourself.

Your team (delegate to them with the task tool):
- climate-researcher: what the weather will be like at the destination and
  dates, and what to pack.
- attraction-researcher: the best places of interest in the destination for
  this particular group.
- route-planner: how to get around — airport to hotel and day-to-day transit
  between areas — with durations and rough costs.

Your job:
1. Extract the trip facts from the request: destination, dates or season,
   number of days, who is traveling, interests, and budget.
2. Fire ALL THREE subagents in parallel with the task tool — one task call
   each, without waiting for one to finish before starting the next. The
   subagents cannot see this conversation, so each task description must
   contain every trip fact that specialist needs.
3. Collect their three responses. Do NOT research anything yourself.
4. Assemble one final plan for the family: a day-by-day itinerary for the
   stated number of days (attractions per day in a sensible geographic
   order), a short "what to bring" section from the climate notes, and the
   transit plan. Present it as a single, readable plan — no raw research
   dumps."""
USER_REQUEST = (
    "I want to bring my family of 4 (two adults, kids aged 8 and 11) to Tokyo "
    "for 5 days in early April. We're on a moderate budget, the kids love "
    "anime and animals, and we land at Haneda on a Tuesday morning. Plan the "
    "whole trip: what to do each day, what to pack, and how to get around."
)

for _spec in SUBAGENT_SPECS:
    if _spec["name"].startswith("TODO-1"):
        raise NotImplementedError("TODO 1: see the comment block above")
if MAIN_PROMPT.startswith("TODO 2") or USER_REQUEST.startswith("TODO 2"):
    raise NotImplementedError("TODO 2: see the comment block above")

_team = build_subagents(SUBAGENT_SPECS)

# The main agent must never write into any subagent's scratch folder either.
MAIN_PERMISSIONS = [
    FilesystemPermission(operations=["write"], paths=[f"{SCRATCH_ROOT}/**"], mode="deny"),
]

THREAD = {"configurable": {"thread_id": "subagents_demo"}}
run_id = uuid.uuid4()

agent = create_deep_agent(
    model=strong_model,
    name="Homework_Team_Agent",
    system_prompt=MAIN_PROMPT,
    subagents=_team,
    permissions=MAIN_PERMISSIONS,
)

print(f"Run with run_id: {run_id}")

result = agent.invoke(
    {"messages": [{"role": "user", "content": USER_REQUEST}]},
    config={"recursion_limit": 50, **THREAD, "run_id": run_id},
)
print(result["messages"][-1].content)

files = result.get("files", {})
print("\n--- Scratch folder isolation check ---")
for spec in SUBAGENT_SPECS:
    path = scratch_path(spec["name"])
    print(f"  {path}: {'found' if path in files else 'not written (subagent may not have been called)'}")

scratch_files = [p for p in files if p.startswith(SCRATCH_ROOT + "/")]
expected = {scratch_path(spec["name"]) for spec in SUBAGENT_SPECS}
stray = [p for p in scratch_files if p not in expected]
if stray:
    print(f"  Unexpected scratch files (isolation may have failed): {stray}")
else:
    print("  No stray scratch files -- each subagent wrote only to its own folder.")
