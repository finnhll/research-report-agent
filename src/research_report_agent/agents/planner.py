"""Deterministic planner agent."""

from __future__ import annotations

from research_report_agent.contracts import ResearchPlan, ResearchTask


class Planner:
    """Create a 3–6 task dependency-aware research plan."""

    def create_plan(self, goal: str, dimensions: list[str]) -> ResearchPlan:
        clean_dimensions = self._dimensions(dimensions)
        tasks = [
            ResearchTask(
                task_id="task_001",
                question=f"Identify the central entities or technologies for: {goal}",
                success_criteria=[
                    "Identify the relevant entities",
                    "Explain why each entity is relevant",
                    "Use at least two independent sources",
                ],
                required_tools=["web_search", "fetch_page"],
                priority="high",
                dependencies=[],
            )
        ]

        for index, dimension in enumerate(clean_dimensions, start=2):
            tasks.append(
                ResearchTask(
                    task_id=f"task_{index:03d}",
                    question=f"Analyze the {dimension} tradeoffs for: {goal}",
                    success_criteria=[
                        f"Cover {dimension} with specific evidence",
                        "Distinguish observed evidence from projections",
                        "Use at least two independent sources",
                    ],
                    required_tools=["web_search", "fetch_page"],
                    priority="high",
                    dependencies=["task_001"],
                )
            )

        if len(tasks) < 3:
            filler = [
                ResearchTask(
                    task_id="task_002",
                    question=(
                        f"Identify evidence limitations and comparability issues for: {goal}"
                    ),
                    success_criteria=["Identify material limitations", "Cite sources"],
                    required_tools=["web_search"],
                    priority="medium",
                    dependencies=["task_001"],
                ),
                ResearchTask(
                    task_id="task_003",
                    question=f"Compare practical tradeoffs for: {goal}",
                    success_criteria=["Compare at least two options", "Cite sources"],
                    required_tools=["web_search"],
                    priority="high",
                    dependencies=["task_001"],
                ),
            ]
            if len(tasks) == 1:
                tasks.extend(filler)
            else:
                tasks.append(filler[1])

        return ResearchPlan(
            plan_id="plan_001",
            objective=goal,
            tasks=tasks[:6],
        )

    def _dimensions(self, dimensions: list[str]) -> list[str]:
        clean = []
        for dimension in dimensions:
            value = dimension.strip().lower()
            if value and value not in clean:
                clean.append(value)
        return clean[:5]


__all__ = ["Planner"]
