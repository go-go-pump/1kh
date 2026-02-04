"""
Report Generator - Creates HTML reports for cycles.

Generates beautiful, interactive reports showing:
- North Star progress
- System completeness
- Trajectory analysis
- Recommendations
- Hypothesis and task details
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("1kh.report")


class ReportGenerator:
    """
    Generates HTML reports from cycle data.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.template_path = Path(__file__).parent / "templates" / "cycle_report.html"
        self.reports_dir = self.project_path / ".1kh" / "reports"

    def generate(
        self,
        cycle_number: int,
        cycle_result: dict,
        reflection_result: dict = None,
        hypotheses: list[dict] = None,
        tasks: list[dict] = None,
        north_star_name: str = "$1M ARR",
        north_star_target: float = 1_000_000,
        north_star_current: float = 0,
    ) -> Path:
        """
        Generate an HTML report for a cycle.

        Returns path to generated report.
        """
        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template = self._load_template()

        # Calculate progress
        progress = (north_star_current / north_star_target * 100) if north_star_target > 0 else 0

        # Prepare data
        data = {
            "cycle_number": cycle_number,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "status": reflection_result.get("status", "healthy") if reflection_result else "healthy",

            "north_star": {
                "name": north_star_name,
                "target": north_star_target,
                "current": north_star_current,
                "progress": progress,
            },

            "cycle_metrics": {
                "hypotheses_generated": cycle_result.get("hypotheses_generated", 0),
                "hypotheses_approved": cycle_result.get("hypotheses_approved", 0),
                "hypotheses_escalated": cycle_result.get("hypotheses_escalated", 0),
                "tasks_executed": cycle_result.get("tasks_executed", 0),
                "tasks_succeeded": cycle_result.get("tasks_succeeded", 0),
                "tasks_failed": cycle_result.get("tasks_failed", 0),
                "revenue_delta": cycle_result.get("revenue_delta", 0),
                "signups_delta": cycle_result.get("signups_delta", 0),
            },

            "completeness": {
                "score": reflection_result.get("completeness", {}).get("score", 0) if reflection_result else 0,
                "can_generate_revenue": reflection_result.get("completeness", {}).get("can_generate_revenue", False) if reflection_result else False,
                "blockers": reflection_result.get("completeness", {}).get("blockers", []) if reflection_result else [],
            },

            "trajectory": reflection_result.get("trajectory", {}) if reflection_result else {},

            "components": self._get_components(reflection_result),
            "recommendations": reflection_result.get("recommendations", []) if reflection_result else [],
            "hypotheses": hypotheses or [],
            "tasks": self._format_tasks(tasks or []),
        }

        # Render template
        html = self._render_template(template, data)

        # Save report
        report_path = self.reports_dir / f"cycle_{cycle_number:03d}.html"
        report_path.write_text(html)

        logger.info(f"Generated report: {report_path}")

        return report_path

    def _load_template(self) -> str:
        """Load the HTML template."""
        if self.template_path.exists():
            return self.template_path.read_text()
        else:
            # Fallback to basic template
            return self._get_fallback_template()

    def _render_template(self, template: str, data: dict) -> str:
        """
        Simple template rendering using Jinja2-like syntax.

        For now, we use basic string replacement.
        In production, you'd use Jinja2.
        """
        try:
            from jinja2 import Template
            t = Template(template)
            return t.render(**data)
        except ImportError:
            # Fallback to simple rendering
            return self._simple_render(template, data)

    def _simple_render(self, template: str, data: dict) -> str:
        """Simple template rendering without Jinja2."""
        # This is a basic fallback - in practice you'd have Jinja2 installed
        html = template

        # Replace simple variables
        html = html.replace("{{ cycle_number }}", str(data["cycle_number"]))
        html = html.replace("{{ timestamp }}", data["timestamp"])
        html = html.replace("{{ status }}", data["status"])

        # North Star
        ns = data["north_star"]
        html = html.replace("{{ north_star.name }}", ns["name"])
        html = html.replace("{{ north_star.current }}", f"{ns['current']:,.0f}")
        html = html.replace("{{ north_star.target }}", f"{ns['target']:,.0f}")
        html = html.replace("{{ north_star.progress }}", f"{ns['progress']:.1f}")

        # This is getting complex - let's just return a simplified version
        return self._generate_simple_html(data)

    def _generate_simple_html(self, data: dict) -> str:
        """Generate a simple HTML report without Jinja2."""
        ns = data["north_star"]
        cm = data["cycle_metrics"]
        traj = data.get("trajectory", {})
        comp = data.get("completeness", {})

        components_html = ""
        for c in data.get("components", []):
            status_class = f"status-{c['status']}"
            icon = {"product": "📦", "payment": "💳", "channel": "📢", "fulfillment": "📬"}.get(c["category"], "📋")
            components_html += f"""
            <div class="component-card">
                <div class="component-icon {c['category']}">{icon}</div>
                <div class="component-info">
                    <div class="component-name">{c['name']}</div>
                    <div class="component-desc">{c['description']}</div>
                </div>
                <span class="status {status_class}">{c['status']}</span>
            </div>
            """

        recommendations_html = ""
        for rec in data.get("recommendations", []):
            rec_type = rec.get("type", "continue")
            icon = {"augment": "🔧", "optimize": "📈", "pivot": "🔄"}.get(rec_type, "➡️")
            recommendations_html += f"""
            <div class="recommendation {rec_type}">
                <div class="recommendation-icon">{icon}</div>
                <div class="recommendation-content">
                    <h4>{rec.get('title', 'Recommendation')}</h4>
                    <p>{rec.get('description', '')}</p>
                    <p style="margin-top: 0.5rem; font-style: italic;">{rec.get('rationale', '')}</p>
                </div>
            </div>
            """

        hypotheses_html = ""
        for i, hyp in enumerate(data.get("hypotheses", [])):
            feas = hyp.get("feasibility", 0)
            align = hyp.get("north_star_alignment", 0)
            score = feas * 0.4 + align * 0.6
            score_class = "score-high" if score >= 0.65 else "score-medium" if score >= 0.4 else "score-low"
            full_desc = hyp.get("description", "")
            short_desc = full_desc[:60]
            has_more = len(full_desc) > 60
            hyp_id = hyp.get('id', f'hyp-{i}')
            priority = hyp.get("priority", "normal")
            priority_badge = f'<span class="priority-badge priority-{priority}">{priority}</span>' if priority != "normal" else ""
            hypotheses_html += f"""
            <tr class="expandable-row" onclick="toggleRow(this)" id="hyp-row-{i}">
                <td><code>{hyp_id}</code> {priority_badge}</td>
                <td>
                    <span class="short-text">{short_desc}{'...' if has_more else ''}</span>
                    <span class="full-text" style="display:none;">{full_desc}</span>
                    {f'<span class="expand-hint">(click to expand)</span>' if has_more else ''}
                </td>
                <td>{feas*100:.0f}%</td>
                <td>{align*100:.0f}%</td>
                <td><span class="score {score_class}">{score*100:.0f}%</span></td>
                <td><span class="status status-building">{hyp.get('status', 'pending')}</span></td>
            </tr>
            """

        tasks_html = ""
        for i, task in enumerate(data.get("tasks", [])):
            full_desc = task.get("description", "")
            short_desc = full_desc[:60]
            has_more = len(full_desc) > 60
            signups = task.get("signups", 0)
            revenue = task.get("revenue", 0)
            success = task.get("success", True)
            task_id = task.get('id', f'task-{i}')
            tasks_html += f"""
            <tr class="expandable-row" onclick="toggleRow(this)" id="task-row-{i}">
                <td><code>{task_id}</code></td>
                <td>
                    <span class="short-text">{short_desc}{'...' if has_more else ''}</span>
                    <span class="full-text" style="display:none;">{full_desc}</span>
                    {f'<span class="expand-hint">(click to expand)</span>' if has_more else ''}
                </td>
                <td><span class="delta delta-{'positive' if signups > 0 else 'neutral'}">+{signups}</span></td>
                <td><span class="delta delta-{'positive' if revenue > 0 else 'neutral'}">+${revenue}</span></td>
                <td><span class="status status-{'live' if success else 'missing'}">{'✓ Done' if success else '✗ Failed'}</span></td>
            </tr>
            """

        blockers_html = ""
        if not comp.get("can_generate_revenue", True):
            blockers = comp.get("blockers", [])
            blockers_list = "".join(f"<li>{b}</li>" for b in blockers)
            blockers_html = f"""
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 0.5rem;">
                <strong style="color: var(--danger);">⚠️ Cannot generate revenue</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: var(--text-muted);">
                    {blockers_list}
                </ul>
            </div>
            """

        trajectory_warning = ""
        if traj.get("warning"):
            trajectory_warning = f"""
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(234, 179, 8, 0.1); border-radius: 0.5rem; color: var(--warning);">
                ⚠️ {traj['warning']}
            </div>
            """

        status = data["status"]
        status_text = "✓ Healthy" if status == "healthy" else "⚡ Warning" if status == "warning" else "⚠️ Critical"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>1KH Cycle Report - Cycle {data['cycle_number']}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #22c55e;
            --warning: #eab308;
            --danger: #ef4444;
            --muted: #64748b;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --border: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }}
        header h1 {{ font-size: 1.5rem; }}
        header .meta {{ color: var(--text-muted); font-size: 0.875rem; }}
        .grid {{ display: grid; gap: 1.5rem; }}
        .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        @media (max-width: 768px) {{ .grid-4 {{ grid-template-columns: 1fr 1fr; }} }}
        .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; }}
        .card-title {{ font-size: 0.875rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        .card-value {{ font-size: 2rem; font-weight: 700; }}
        .card-subtitle {{ font-size: 0.875rem; color: var(--text-muted); }}
        .north-star {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border: none; }}
        .progress-bar {{ height: 12px; background: rgba(255, 255, 255, 0.2); border-radius: 6px; overflow: hidden; margin: 1rem 0; }}
        .progress-fill {{ height: 100%; background: white; border-radius: 6px; }}
        .status {{ display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }}
        .status-healthy {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .status-warning {{ background: rgba(234, 179, 8, 0.2); color: var(--warning); }}
        .status-critical {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .status-live {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .status-building {{ background: rgba(99, 102, 241, 0.2); color: var(--primary); }}
        .status-missing {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .component-card {{ display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 0.5rem; margin-bottom: 0.75rem; }}
        .component-icon {{ width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 0.5rem; font-size: 1.25rem; }}
        .component-icon.product {{ background: rgba(99, 102, 241, 0.2); }}
        .component-icon.payment {{ background: rgba(34, 197, 94, 0.2); }}
        .component-icon.channel {{ background: rgba(234, 179, 8, 0.2); }}
        .component-icon.fulfillment {{ background: rgba(239, 68, 68, 0.2); }}
        .component-info {{ flex: 1; }}
        .component-name {{ font-weight: 600; }}
        .component-desc {{ font-size: 0.875rem; color: var(--text-muted); }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
        .table th {{ font-size: 0.75rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; }}
        .recommendation {{ display: flex; gap: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 0.5rem; margin-bottom: 0.75rem; border-left: 3px solid var(--primary); }}
        .recommendation.augment {{ border-left-color: var(--success); }}
        .recommendation.optimize {{ border-left-color: var(--warning); }}
        .recommendation.pivot {{ border-left-color: var(--danger); }}
        .recommendation-icon {{ font-size: 1.5rem; }}
        .recommendation-content h4 {{ font-weight: 600; margin-bottom: 0.25rem; }}
        .recommendation-content p {{ font-size: 0.875rem; color: var(--text-muted); }}
        .trajectory-stat {{ text-align: center; padding: 1rem; }}
        .trajectory-value {{ font-size: 1.5rem; font-weight: 700; }}
        .trajectory-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }}
        .section-header {{ display: flex; justify-content: space-between; align-items: center; margin: 2rem 0 1rem; }}
        .section-title {{ font-size: 1.25rem; font-weight: 600; }}
        .score {{ display: inline-flex; align-items: center; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem; font-weight: 500; }}
        .score-high {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .score-medium {{ background: rgba(234, 179, 8, 0.2); color: var(--warning); }}
        .score-low {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .delta {{ display: inline-flex; align-items: center; font-size: 0.875rem; }}
        .delta-positive {{ color: var(--success); }}
        .delta-neutral {{ color: var(--text-muted); }}
        footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 0.875rem; }}

        /* Expandable rows */
        .expandable-row {{ cursor: pointer; transition: background 0.2s; }}
        .expandable-row:hover {{ background: rgba(255, 255, 255, 0.05); }}
        .expandable-row.expanded {{ background: rgba(99, 102, 241, 0.1); }}
        .expandable-row.expanded .short-text {{ display: none; }}
        .expandable-row.expanded .full-text {{ display: inline !important; }}
        .expandable-row.expanded .expand-hint {{ display: none; }}
        .expand-hint {{ font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem; }}

        /* Priority badges */
        .priority-badge {{ font-size: 0.625rem; padding: 0.125rem 0.375rem; border-radius: 0.25rem; margin-left: 0.5rem; text-transform: uppercase; font-weight: 600; }}
        .priority-critical {{ background: rgba(239, 68, 68, 0.3); color: var(--danger); }}
        .priority-high {{ background: rgba(234, 179, 8, 0.3); color: var(--warning); }}

        /* Quick nav */
        .quick-nav {{ position: fixed; top: 50%; right: 1rem; transform: translateY(-50%); display: flex; flex-direction: column; gap: 0.5rem; z-index: 100; }}
        .quick-nav a {{ display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 0.5rem; color: var(--text-muted); text-decoration: none; font-size: 1.25rem; transition: all 0.2s; }}
        .quick-nav a:hover {{ background: var(--primary); color: white; border-color: var(--primary); }}
        .quick-nav a .tooltip {{ position: absolute; right: 50px; background: var(--card-bg); border: 1px solid var(--border); padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .quick-nav a:hover .tooltip {{ opacity: 1; }}
    </style>
</head>
<body>
    <!-- Quick Navigation -->
    <nav class="quick-nav">
        <a href="#north-star" title="North Star">🎯<span class="tooltip">North Star</span></a>
        <a href="#components" title="Components">🧩<span class="tooltip">Components</span></a>
        <a href="#trajectory" title="Trajectory">📈<span class="tooltip">Trajectory</span></a>
        <a href="#recommendations" title="Recommendations">💡<span class="tooltip">Recommendations</span></a>
        <a href="#hypotheses" title="Hypotheses">🧠<span class="tooltip">Hypotheses</span></a>
        <a href="#tasks" title="Tasks">✅<span class="tooltip">Tasks</span></a>
    </nav>

    <script>
        function toggleRow(row) {{
            row.classList.toggle('expanded');
        }}

        // Smooth scroll to sections when clicking on quick nav or component cards
        document.addEventListener('DOMContentLoaded', function() {{
            // Add smooth scrolling
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}
                }});
            }});

            // Make component cards clickable to scroll to related hypotheses
            document.querySelectorAll('.component-card').forEach(card => {{
                card.style.cursor = 'pointer';
                card.addEventListener('click', function() {{
                    document.querySelector('#hypotheses')?.scrollIntoView({{ behavior: 'smooth' }});
                }});
            }});
        }});
    </script>
    <div class="container">
        <header>
            <div>
                <h1>ThousandHand Cycle Report</h1>
                <div class="meta">Cycle {data['cycle_number']} | {data['timestamp']}</div>
            </div>
            <span class="status status-{status}">{status_text}</span>
        </header>

        <div id="north-star" class="card north-star">
            <div style="display: flex; justify-content: space-between;">
                <span class="card-title">North Star</span>
                <span>{ns['name']}</span>
            </div>
            <div class="card-value">${ns['current']:,.0f}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {ns['progress']:.1f}%"></div>
            </div>
            <div class="card-subtitle">{ns['progress']:.1f}% toward ${ns['target']:,.0f}</div>
        </div>

        <div id="cycle" class="section-header">
            <h2 class="section-title">This Cycle</h2>
        </div>
        <div class="grid grid-4">
            <div class="card">
                <div class="card-title">Hypotheses</div>
                <div class="card-value">{cm['hypotheses_generated']}</div>
                <div class="card-subtitle">{cm['hypotheses_approved']} approved</div>
            </div>
            <div class="card">
                <div class="card-title">Tasks</div>
                <div class="card-value">{cm['tasks_executed']}</div>
                <div class="card-subtitle">{cm['tasks_succeeded']} succeeded</div>
            </div>
            <div class="card">
                <div class="card-title">Revenue</div>
                <div class="card-value"><span class="delta delta-positive">+${cm['revenue_delta']}</span></div>
                <div class="card-subtitle">This cycle</div>
            </div>
            <div class="card">
                <div class="card-title">Signups</div>
                <div class="card-value"><span class="delta delta-positive">+{cm['signups_delta']}</span></div>
                <div class="card-subtitle">This cycle</div>
            </div>
        </div>

        <div id="components" class="section-header">
            <h2 class="section-title">System Components</h2>
            <span class="card-subtitle">{comp.get('score', 0)*100:.0f}% complete</span>
        </div>
        <div class="card">
            {components_html}
            {blockers_html}
        </div>

        <div id="trajectory" class="section-header">
            <h2 class="section-title">Trajectory</h2>
        </div>
        <div class="card">
            <div class="grid grid-4">
                <div class="trajectory-stat">
                    <div class="trajectory-value">${traj.get('velocity_per_cycle', 0):,.0f}</div>
                    <div class="trajectory-label">Per Cycle</div>
                </div>
                <div class="trajectory-stat">
                    <div class="trajectory-value">{traj.get('velocity_trend', 'N/A')}</div>
                    <div class="trajectory-label">Trend</div>
                </div>
                <div class="trajectory-stat">
                    <div class="trajectory-value">{traj.get('cycles_to_goal', '∞') or '∞'}</div>
                    <div class="trajectory-label">Cycles to Goal</div>
                </div>
                <div class="trajectory-stat">
                    <div class="trajectory-value">{traj.get('time_to_goal', 'N/A')}</div>
                    <div class="trajectory-label">Time Estimate</div>
                </div>
            </div>
            {trajectory_warning}
        </div>

        {'<div id="recommendations" class="section-header"><h2 class="section-title">Recommendations</h2></div><div class="card">' + recommendations_html + '</div>' if recommendations_html else ''}

        {'<div id="hypotheses" class="section-header"><h2 class="section-title">Hypotheses</h2><span class="card-subtitle">Click row to expand</span></div><div class="card"><table class="table"><thead><tr><th>ID</th><th>Description</th><th>Feasibility</th><th>Alignment</th><th>Score</th><th>Status</th></tr></thead><tbody>' + hypotheses_html + '</tbody></table></div>' if hypotheses_html else ''}

        {'<div id="tasks" class="section-header"><h2 class="section-title">Tasks</h2><span class="card-subtitle">Click row to expand</span></div><div class="card"><table class="table"><thead><tr><th>ID</th><th>Description</th><th>Signups</th><th>Revenue</th><th>Status</th></tr></thead><tbody>' + tasks_html + '</tbody></table></div>' if tasks_html else ''}

        <footer>
            <p>Generated by ThousandHand | {data['timestamp']}</p>
        </footer>
    </div>
</body>
</html>"""

    def _get_components(self, reflection_result: dict) -> list[dict]:
        """Extract component data from reflection result."""
        if not reflection_result:
            return [
                {"name": "Product", "category": "product", "status": "missing", "description": "The thing you sell"},
                {"name": "Payment", "category": "payment", "status": "missing", "description": "How customers pay you"},
                {"name": "Channel", "category": "channel", "status": "missing", "description": "How customers find you"},
                {"name": "Fulfillment", "category": "fulfillment", "status": "missing", "description": "How customers receive value"},
            ]

        comp = reflection_result.get("completeness", {})
        missing = comp.get("missing_components", [])
        building = comp.get("building_components", [])
        live = comp.get("live_components", [])

        components = []
        for name in ["Product", "Payment", "Channel", "Fulfillment"]:
            if name in live:
                status = "live"
            elif name in building:
                status = "building"
            else:
                status = "missing"

            category = name.lower()
            desc = {
                "product": "The thing you sell",
                "payment": "How customers pay you",
                "channel": "How customers find you",
                "fulfillment": "How customers receive value",
            }.get(category, "")

            components.append({
                "name": name,
                "category": category,
                "status": status,
                "description": desc,
            })

        return components

    def _format_tasks(self, tasks: list[dict]) -> list[dict]:
        """Format tasks for display."""
        formatted = []
        for task in tasks:
            result = task.get("result", {})
            formatted.append({
                "id": task.get("id", ""),
                "description": task.get("description", ""),
                "signups": result.get("signups", 0) if isinstance(result, dict) else 0,
                "revenue": result.get("revenue", 0) if isinstance(result, dict) else 0,
                "success": task.get("success", True),
            })
        return formatted

    def _get_fallback_template(self) -> str:
        """Return a basic fallback template."""
        return "<html><body><h1>Cycle Report</h1><p>Template not found.</p></body></html>"
