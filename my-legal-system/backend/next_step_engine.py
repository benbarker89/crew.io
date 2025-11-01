"""
Next Step Engine - Intelligent task prioritization and recommendations
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import Case, Task, Milestone, Document, CriticalDate
from datetime import datetime, timedelta
from typing import Dict, List


class NextStepEngine:
    """Analyzes case state and provides prioritized next steps"""

    def __init__(self, db: Session):
        self.db = db

    def get_next_steps(self, case_id: int, limit: int = 10) -> Dict:
        """Generate prioritized next steps for a case"""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "Case not found"}

        recommendations = []

        # Priority 1: URGENT - Overdue tasks
        recommendations.extend(self._get_overdue_tasks(case_id))

        # Priority 2: CRITICAL - Deadlines within 7 days
        recommendations.extend(self._get_upcoming_deadlines(case_id, days=7))

        # Priority 3: CRITICAL - Blocked milestones
        recommendations.extend(self._get_blocking_tasks(case_id))

        # Priority 4: NEXT PRIORITY - Incomplete milestone tasks
        recommendations.extend(self._get_milestone_tasks(case_id))

        # Priority 5: RECOMMENDED - Maintenance tasks
        recommendations.extend(self._get_maintenance_recommendations(case_id))

        # Remove duplicates and limit results
        seen_tasks = set()
        unique_recommendations = []
        for rec in recommendations:
            task_key = (rec.get('task_id'), rec.get('title'))
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        return {
            "case_id": case_id,
            "case_title": case.title,
            "next_steps": unique_recommendations,
            "total_recommendations": len(unique_recommendations)
        }

    def get_all_next_steps(self, limit: int = 15) -> Dict:
        """Get next steps across all active cases"""
        active_cases = self.db.query(Case).filter(Case.status != 'Closed').all()

        all_recommendations = []
        for case in active_cases:
            case_steps = self.get_next_steps(case.id, limit=5)
            for step in case_steps.get("next_steps", []):
                step["case_number"] = case.case_number
                step["case_title"] = case.title
                all_recommendations.append(step)

        # Sort by urgency
        urgency_order = {"URGENT": 0, "CRITICAL": 1, "NEXT PRIORITY": 2, "RECOMMENDED": 3}
        all_recommendations.sort(key=lambda x: urgency_order.get(x.get("urgency", "RECOMMENDED"), 4))

        return {
            "next_steps": all_recommendations[:limit],
            "total_recommendations": len(all_recommendations)
        }

    def _get_overdue_tasks(self, case_id: int) -> List[Dict]:
        """Get all overdue tasks"""
        now = datetime.utcnow()
        overdue_tasks = self.db.query(Task).filter(
            and_(
                Task.case_id == case_id,
                Task.status != 'Completed',
                Task.due_date < now
            )
        ).all()

        recommendations = []
        for task in overdue_tasks:
            days_overdue = (now - task.due_date).days
            recommendations.append({
                "urgency": "URGENT",
                "urgency_icon": "🔴",
                "task_id": task.id,
                "title": task.title,
                "action": task.description or f"Complete overdue task: {task.title}",
                "estimated_time": task.estimated_hours,
                "due_date": task.due_date.isoformat(),
                "days_overdue": days_overdue,
                "context": f"This task is {days_overdue} day(s) overdue",
                "priority_score": 1000 + days_overdue  # Highest priority
            })

        return recommendations

    def _get_upcoming_deadlines(self, case_id: int, days: int = 7) -> List[Dict]:
        """Get tasks with upcoming deadlines"""
        now = datetime.utcnow()
        deadline = now + timedelta(days=days)

        upcoming_tasks = self.db.query(Task).filter(
            and_(
                Task.case_id == case_id,
                Task.status != 'Completed',
                Task.due_date >= now,
                Task.due_date <= deadline
            )
        ).order_by(Task.due_date).all()

        recommendations = []
        for task in upcoming_tasks:
            days_until = (task.due_date - now).days
            recommendations.append({
                "urgency": "CRITICAL" if days_until <= 3 else "NEXT PRIORITY",
                "urgency_icon": "🟠" if days_until <= 3 else "🟡",
                "task_id": task.id,
                "title": task.title,
                "action": task.description or f"Complete task before deadline: {task.title}",
                "estimated_time": task.estimated_hours,
                "due_date": task.due_date.isoformat(),
                "days_until": days_until,
                "context": f"Due in {days_until} day(s)",
                "priority_score": 900 - days_until  # Higher score for sooner deadlines
            })

        return recommendations

    def _get_blocking_tasks(self, case_id: int) -> List[Dict]:
        """Get tasks that are blocking other tasks"""
        # Find incomplete milestones that block other milestones
        milestones = self.db.query(Milestone).filter(
            and_(
                Milestone.case_id == case_id,
                Milestone.is_completed == False
            )
        ).all()

        recommendations = []
        for milestone in milestones:
            # Check if this milestone blocks others
            blocking_count = self.db.query(Milestone).filter(
                Milestone.blocks_milestone_id == milestone.id
            ).count()

            if blocking_count > 0:
                # Find tasks for this milestone
                milestone_tasks = self.db.query(Task).filter(
                    and_(
                        Task.milestone_id == milestone.id,
                        Task.status != 'Completed'
                    )
                ).all()

                for task in milestone_tasks:
                    recommendations.append({
                        "urgency": "CRITICAL",
                        "urgency_icon": "⚠️",
                        "task_id": task.id,
                        "title": task.title,
                        "action": task.description or f"Complete blocking task: {task.title}",
                        "estimated_time": task.estimated_hours,
                        "context": f"Blocks {blocking_count} other milestone(s): {milestone.title}",
                        "priority_score": 800
                    })

        return recommendations

    def _get_milestone_tasks(self, case_id: int) -> List[Dict]:
        """Get next logical tasks from incomplete milestones"""
        # Get incomplete milestones in order
        milestones = self.db.query(Milestone).filter(
            and_(
                Milestone.case_id == case_id,
                Milestone.is_completed == False
            )
        ).order_by(Milestone.order_index).limit(3).all()

        recommendations = []
        for milestone in milestones:
            # Get incomplete tasks for this milestone
            tasks = self.db.query(Task).filter(
                and_(
                    Task.milestone_id == milestone.id,
                    Task.status != 'Completed'
                )
            ).limit(2).all()

            for task in tasks:
                recommendations.append({
                    "urgency": "NEXT PRIORITY",
                    "urgency_icon": "🔵",
                    "task_id": task.id,
                    "title": task.title,
                    "action": task.description or f"Work on: {task.title}",
                    "estimated_time": task.estimated_hours,
                    "context": f"Part of milestone: {milestone.title} ({milestone.completion_percentage}% complete)",
                    "milestone_id": milestone.id,
                    "priority_score": 500
                })

        return recommendations

    def _get_maintenance_recommendations(self, case_id: int) -> List[Dict]:
        """Generate maintenance and organizational recommendations"""
        recommendations = []

        # Check if timeline needs updating
        last_timeline_event = self.db.query(Task).filter(
            Task.case_id == case_id
        ).order_by(Task.created_date.desc()).first()

        if last_timeline_event:
            days_since_update = (datetime.utcnow() - last_timeline_event.created_date).days
            if days_since_update > 7:
                recommendations.append({
                    "urgency": "RECOMMENDED",
                    "urgency_icon": "📝",
                    "title": "Update case timeline",
                    "action": "Review and add recent events to the case timeline",
                    "estimated_time": 0.5,
                    "context": f"Timeline not updated in {days_since_update} days",
                    "priority_score": 200
                })

        # Check for missing evidence
        evidence_count = self.db.query(Document).filter(
            and_(
                Document.case_id == case_id,
                Document.category == 'Evidence'
            )
        ).count()

        if evidence_count < 3:
            recommendations.append({
                "urgency": "RECOMMENDED",
                "urgency_icon": "📎",
                "title": "Gather additional evidence",
                "action": "Review case file and identify missing evidence documents",
                "estimated_time": 1.0,
                "context": f"Only {evidence_count} evidence document(s) on file",
                "priority_score": 300
            })

        # Check for incomplete tasks without deadlines
        no_deadline_tasks = self.db.query(Task).filter(
            and_(
                Task.case_id == case_id,
                Task.status != 'Completed',
                Task.due_date.is_(None)
            )
        ).count()

        if no_deadline_tasks > 0:
            recommendations.append({
                "urgency": "RECOMMENDED",
                "urgency_icon": "⏰",
                "title": "Set deadlines for tasks",
                "action": f"Assign deadlines to {no_deadline_tasks} task(s) without due dates",
                "estimated_time": 0.25,
                "context": "Helps prioritize and track progress",
                "priority_score": 100
            })

        return recommendations

    def create_smart_task(self, case_id: int, recommendation: Dict) -> Dict:
        """Create a task from a recommendation"""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "Case not found"}

        task = Task(
            case_id=case_id,
            title=recommendation.get("title"),
            description=recommendation.get("action"),
            priority=recommendation.get("urgency"),
            estimated_hours=recommendation.get("estimated_time"),
            milestone_id=recommendation.get("milestone_id")
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return {
            "success": True,
            "task_id": task.id,
            "task": {
                "id": task.id,
                "title": task.title,
                "priority": task.priority
            }
        }
