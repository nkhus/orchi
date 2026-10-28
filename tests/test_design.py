"""The design track's wording agrees across planning, readiness, the forms, and the skills; text, not behavior."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_planning_sets_design_depth_and_only_the_user_chooses_a_direction():
    planning, plan = prose("orchi-core/references/planning.md"), prose("orchi-plan/SKILL.md")
    for depth in ("| None |", "| Brief |", "| Epic |"):
        assert depth in planning
    assert "Plan a standalone `design` Epic (labels `Epic` and `design`) for a designer crew, outside any Initiative" in planning
    assert "`Deferred until #<design Epic>`" in planning and "blocked by the design Epic" in planning
    assert "Only the user names references, chooses the engine and a direction, and approves a comp or a generated asset, or Orchi in autonomous mode." in planning
    assert "a new product picks it in its exploration's design session, and a project without either picks it in its first design Epic" in planning
    assert "planning.md#user-interface-design" in plan
    assert "agree the references and the surface brief with the user now" in plan
    assert "a design Epic leaves references, the engine, and the direction to its designer" in plan


def test_ui_readiness_items_have_form_fields():
    readiness = prose("orchi-core/references/readiness.md")
    assert readiness.count("planning.md#user-interface-design") == 2
    for form in ("orchi-task.yml", "orchi-epic.yml"):
        text = (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE" / form).read_text()
        assert "id: ui" in text and "label: UI design" in text


def test_designer_crew_role_routing_and_mode_agree():
    pool, entry, design = prose("orchi-core/references/pool.md"), prose("orchi/SKILL.md"), prose("orchi-design/SKILL.md")
    assert "| Designer | `orchi-design` | One standalone `design` Epic, with the user |" in pool
    assert '"Take #n" on a `delivery-ready` Epic labelled `design` | Designer | `orchi-design`' in pool
    assert "a designer's references,\nengine, direction, and comps".replace("\n", " ") in pool
    assert "asks the user directly while autonomous mode is off" in pool and "while it is on, Orchi decides them" in pool
    assert "A `design` Epic stays standalone" in pool
    assert "(researcher, prototyper, planner, designer, dev lead)" in entry and "while autonomous mode is off, and for a question marked `(user)`" in entry
    assert "Only the user\nnames references, chooses the engine and a direction, and approves a comp or a generated asset, or Orchi in\nautonomous mode".replace("\n", " ") in design
    assert "Continue with [orchi-deliver](../orchi-deliver/SKILL.md)" in design
    assert "Ask the user directly while autonomous mode is off, and Orchi while it is on" in design and "Adopt Orchi's claim" in design
    assert "asks for orchi-design by name" in design


def test_exploration_records_product_truth_and_references():
    exploration, design = prose("orchi-core/references/exploration.md"), prose("orchi-design/SKILL.md")
    assert "| Product | For a product with a user interface" in exploration
    assert "The first design Epic writes `PRODUCT.md` from it and asks only what is missing" in exploration
    assert "How screens should look is not settled here" not in exploration
    assert "id: product" in (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE/orchi-exploration.yml").read_text()
    assert "write it with the user from the Product section of the Exploration" in design


def test_delivery_routes_ui_tasks_to_the_designer_and_audits_ui_changes():
    readme = " ".join((SKILLS / "orchi-core/roles/README.md").read_text().split())
    review, deliver = prose("orchi-core/references/review-delivery.md"), prose("orchi-deliver/SKILL.md")
    assert "every Task that builds against a surface brief or an approved comp" in readme
    assert "a direction, a comp, or a generated asset goes to the user whatever they delegated" in readme
    assert "start `orchi-designer` in Audit mode on it beside the reviewer" in review
    assert "`orchi-designer` in Audit mode" in deliver


def test_design_outputs_that_bind_later_work_pass_the_user():
    designer, readme = prose("orchi-core/roles/orchi-designer.md"), " ".join((SKILLS / "orchi-core/roles/README.md").read_text().split())
    design, planning = prose("orchi-design/SKILL.md"), prose("orchi-core/references/planning.md")
    assert "Never write or replace `DESIGN.md`" in designer
    assert "Commit a generated asset only when the Issue links that asset as approved" in designer
    assert "the `DESIGN.md` sections it follows when `DESIGN.md` exists" in designer
    assert "**Recheck (Audit mode):**" in designer
    assert "write or replace `DESIGN.md` from the built surfaces with the user and commit it" in design
    assert "`Design engine: <Hallmark | prototype>`" in design
    assert "| `PRODUCT.md`, references, surface briefs, the engine and direction rounds, comp and asset approval, `DESIGN.md` | The session that talks to the user" in readme
    assert "Commit the brief on the work's branch, which planning creates now" in planning
    assert "impeccable" not in planning.lower()
    assert "the branch of work at design depth brief" in prose("orchi-plan/SKILL.md")
    assert "for a `decision` `ESCALATE`" in prose("orchi-work/SKILL.md")
    assert "surface briefs and approved comps in `docs/design/surfaces/`" in prose("orchi-core/references/knowledge.md")


def test_first_design_epic_runs_both_engines_and_the_user_picks_one():
    design, designer = prose("orchi-design/SKILL.md"), prose("orchi-core/roles/orchi-designer.md")
    assert "start two `orchi-designer` subagents in Variant mode at once, one per engine" in design
    assert "each labelled by its idea, never by the skill that made it" in design
    assert "The variant the user picks sets the design engine for the project" in design
    assert "propose three to five of your own that fit the product" in design
    assert "`docs/design/references/`" in design and "`docs/design/surfaces/<surface>/`" in design
    assert "## Variant mode" in designer and "Name no favourite: the user chooses." in designer
    assert "build one variant on each of the three dealt themes" in designer
    assert "follow its workflow for a project without a stack (Phases 1 to 5)" in designer


def test_no_skill_or_reference_still_names_impeccable():
    for path in sorted(SKILLS.rglob("*")):
        if path.is_file() and path.suffix in {".md", ".yml", ".html"} and "scripts" not in path.parts:
            assert "impeccable" not in path.read_text().lower(), path


def test_exploration_runs_a_design_session_before_converging():
    exploration, explore = prose("orchi-core/references/exploration.md"), prose("orchi-explore/SKILL.md")
    assert exploration.index("4. **Design.**") < exploration.index("5. **Converge.**") < exploration.index("6. **Shape.**")
    for step in ("1. **Structure.**", "2. **Style.**", "3. **Engine round.**", "4. **The whole system.**"):
        assert step in exploration
    assert "`orchi-designer` in Wireframe mode builds three or four grey layouts of the screen" in exploration
    assert "propose five to seven strong references that fit the product's category" in exploration
    assert "start two `orchi-designer` subagents in Variant mode at once, one per design skill" in exploration
    assert "Start `orchi-designer` in Mockup mode" in exploration
    assert "Commit and push only what the user approved" in exploration
    assert "| Design | For a product with a user interface" in exploration
    assert "Research, Diverge, Design (the [design session](../orchi-core/references/exploration.md#design-session)" in explore
    assert "`orchi-designer` subagents in Wireframe, Variant, and Mockup modes for the design session" in explore
    assert "id: design" in (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE/orchi-exploration.yml").read_text()


def test_design_epic_and_planning_reuse_the_design_session():
    design, planning = prose("orchi-design/SKILL.md"), prose("orchi-core/references/planning.md")
    assert "ran a design session (its Design section), copy what the user approved" in design
    assert "step 2 covers only the surfaces the session left out" in design
    assert "the design Epic names its Design section as its source" in planning
    assert "A design Epic without a design session behind it then agrees references with the user" in planning


def test_designer_wireframes_with_prototype_and_mocks_the_whole_system():
    designer = prose("orchi-core/roles/orchi-designer.md")
    for mode in ("## Wireframe mode", "## Variant mode", "## Mockup mode", "## Task mode", "## Audit mode"):
        assert mode in designer
    assert "Follow prototype's workflow for a project without a stack (Phases 1 to 5) at wireframe fidelity: greys only" in designer
    assert "linked by the system's navigation, with an `index.html`" in designer
    assert "Wireframe, Variant, and Mockup modes write only in the output folder: no edits in the repository, no commits." in designer


def test_design_board_template_reads_rounds_and_saves_ratings():
    board = (SKILLS / "orchi-core/assets/design-board.html").read_text()
    exploration = prose("orchi-core/references/exploration.md")
    assert board.startswith("<title>{{PRODUCT}} design board</title>")
    assert 'db.doc("board/items").onSnapshot' in board and 'db.collection("ratings").onSnapshot' in board
    assert 'db.doc("ratings/" + id).set' in board
    for field in ("score", "note", "pick", "label", "notes", "file", "question"):
        assert field in board
    assert "blind" not in board and "Reveal names" not in board
    assert "blind" not in exploration
    assert "`capabilities` `{\"db\": {}}`" in exploration and "`board/items`" in exploration
    assert "read the collection `ratings` with `ArtifactData` (`list`)" in exploration
    assert "[`assets/design-board.html`](../assets/design-board.html)" in exploration


def test_fast_route_interviews_then_grows_a_living_prototype():
    exploration, explore = prose("orchi-core/references/exploration.md"), prose("orchi-explore/SKILL.md")
    pool, designer = prose("orchi-core/references/pool.md"), prose("orchi-core/roles/orchi-designer.md")
    route = exploration[exploration.index("## Fast prototyping"):exploration.index("## Prototypes")]
    steps = ("1. **Interview.**", "2. **Variants.**", "3. **Living prototype.**", "4. **Before showing a change,**",
             "5. **Build it.**")
    assert [route.index(step) for step in steps] == sorted(route.index(step) for step in steps)
    assert "Ask how many variants to build (three unless the user says otherwise)." in route
    assert "ask whether to run another" in route and "never by the skill that made it" in route
    assert "read them with `ArtifactComments`" in route and "keep asking while it works" in route
    assert "After two failed repairs of the same thing, change the approach or ask the user" in route
    assert "every idea the user raised and parked" in route and "The prototype's code is never product code" in route
    assert "plausible sample data" in route
    assert "A request for a prototype takes the [fast route](#fast-prototyping) instead of phases 2 to 4." in exploration
    assert "| Ideas | Every idea the user raised and parked" in exploration
    assert "id: ideas" in (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE/orchi-exploration.yml").read_text()
    assert "`Route: fast prototyping`" in explore and "keep interviewing while it works" in explore
    assert "| Prototyper | `orchi-explore` with `--prototype` |" in pool
    assert "`Fast prototype` and `Full exploration`" in pool and "`prototyper`" in pool
    assert "on the fast route, a direction in one line instead" in designer
    assert "To change a mockup, copy it into the output folder and change only what the remarks name." in designer
    assert "'prototyper': 'Prototyper'" in (SKILLS / "orchi-core/scripts/dashboard.py").read_text()
