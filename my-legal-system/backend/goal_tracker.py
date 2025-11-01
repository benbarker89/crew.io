"""
Mission Goal System - Track case progress toward objectives
"""
from sqlalchemy.orm import Session
from models import Case, Milestone, Task
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class GoalTracker:
    """Tracks progress toward case mission goals"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_case_progress(self, case_id: int) -> Dict:
        """Calculate overall progress for a case"""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "Case not found"}

        milestones = self.db.query(Milestone).filter(
            Milestone.case_id == case_id
        ).order_by(Milestone.order_index).all()

        if not milestones:
            return {
                "case_id": case_id,
                "case_title": case.title,
                "mission_statement": case.mission_statement,
                "overall_progress": 0.0,
                "milestones_completed": 0,
                "milestones_total": 0,
                "milestones": []
            }

        total_milestones = len(milestones)
        completed_milestones = sum(1 for m in milestones if m.is_completed)

        # Calculate weighted average of milestone completion
        if milestones:
            overall_progress = sum(m.completion_percentage for m in milestones) / total_milestones
        else:
            overall_progress = 0.0

        milestone_data = []
        for milestone in milestones:
            milestone_info = {
                "id": milestone.id,
                "title": milestone.title,
                "type": milestone.milestone_type,
                "progress": milestone.completion_percentage,
                "is_completed": milestone.is_completed,
                "target_date": milestone.target_date.isoformat() if milestone.target_date else None,
                "completed_date": milestone.completed_date.isoformat() if milestone.completed_date else None,
                "status_icon": self._get_status_icon(milestone.completion_percentage, milestone.is_completed),
                "days_until_target": self._days_until(milestone.target_date) if milestone.target_date else None
            }
            milestone_data.append(milestone_info)

        return {
            "case_id": case_id,
            "case_title": case.title,
            "mission_statement": case.mission_statement,
            "overall_progress": round(overall_progress, 1),
            "milestones_completed": completed_milestones,
            "milestones_total": total_milestones,
            "milestones": milestone_data,
            "estimated_completion": self._estimate_completion_date(milestones)
        }

    def update_milestone_progress(self, milestone_id: int, completion_percentage: float) -> Dict:
        """Update milestone completion percentage"""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            return {"error": "Milestone not found"}

        milestone.completion_percentage = min(100.0, max(0.0, completion_percentage))

        # Auto-complete if 100%
        if milestone.completion_percentage >= 100.0 and not milestone.is_completed:
            milestone.is_completed = True
            milestone.completed_date = datetime.utcnow()

        self.db.commit()
        return {"success": True, "milestone_id": milestone_id, "progress": milestone.completion_percentage}

    def complete_milestone(self, milestone_id: int) -> Dict:
        """Mark a milestone as completed"""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            return {"error": "Milestone not found"}

        milestone.is_completed = True
        milestone.completion_percentage = 100.0
        milestone.completed_date = datetime.utcnow()
        self.db.commit()

        return {
            "success": True,
            "milestone_id": milestone_id,
            "milestone_title": milestone.title,
            "completed_date": milestone.completed_date.isoformat(),
            "celebration_message": self._get_celebration_message(milestone)
        }

    def add_milestone(self, case_id: int, title: str, milestone_type: str,
                     description: Optional[str] = None, target_date: Optional[datetime] = None) -> Dict:
        """Add a new milestone to a case"""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "Case not found"}

        # Get max order index
        max_order = self.db.query(Milestone).filter(
            Milestone.case_id == case_id
        ).count()

        milestone = Milestone(
            case_id=case_id,
            title=title,
            milestone_type=milestone_type,
            description=description,
            target_date=target_date,
            order_index=max_order
        )

        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)

        return {
            "success": True,
            "milestone_id": milestone.id,
            "milestone": {
                "id": milestone.id,
                "title": milestone.title,
                "type": milestone.milestone_type,
                "progress": milestone.completion_percentage
            }
        }

    def get_incomplete_milestones(self, case_id: int) -> List[Dict]:
        """Get all incomplete milestones for a case"""
        milestones = self.db.query(Milestone).filter(
            Milestone.case_id == case_id,
            Milestone.is_completed == False
        ).order_by(Milestone.order_index).all()

        return [{
            "id": m.id,
            "title": m.title,
            "type": m.milestone_type,
            "progress": m.completion_percentage,
            "target_date": m.target_date.isoformat() if m.target_date else None,
            "days_until_target": self._days_until(m.target_date) if m.target_date else None
        } for m in milestones]

    def _get_status_icon(self, progress: float, is_completed: bool) -> str:
        """Get visual status icon based on progress"""
        if is_completed or progress >= 100.0:
            return "✓"
        elif progress > 0:
            return "▶"
        else:
            return "□"

    def _days_until(self, target_date: datetime) -> int:
        """Calculate days until target date"""
        if not target_date:
            return None
        delta = target_date - datetime.now().date()
        return delta.days

    def _estimate_completion_date(self, milestones: List[Milestone]) -> Optional[str]:
        """Estimate when all milestones will be complete"""
        incomplete = [m for m in milestones if not m.is_completed and m.target_date]
        if not incomplete:
            return None

        latest_date = max(m.target_date for m in incomplete)
        return latest_date.isoformat()

    def _get_celebration_message(self, milestone: Milestone) -> str:
        """Generate celebration message for completed milestone"""
        messages = {
            "Pre-action": f"🎉 Pre-action milestone completed: {milestone.title}",
            "Procedural": f"✅ Procedural milestone achieved: {milestone.title}",
            "Evidence": f"📋 Evidence milestone complete: {milestone.title}",
            "Hearing": f"⚖️ Hearing milestone reached: {milestone.title}",
            "Outcome": f"🏆 Outcome milestone accomplished: {milestone.title}"
        }
        return messages.get(milestone.milestone_type, f"✨ Milestone completed: {milestone.title}")

    def get_dashboard_summary(self) -> Dict:
        """Get summary of all cases for dashboard"""
        cases = self.db.query(Case).filter(Case.status != 'Closed').all()

        case_summaries = []
        for case in cases:
            progress = self.calculate_case_progress(case.id)
            case_summaries.append({
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "status": case.status,
                "priority": case.priority,
                "overall_progress": progress["overall_progress"],
                "milestones_completed": progress["milestones_completed"],
                "milestones_total": progress["milestones_total"]
            })

        return {
            "active_cases": len(case_summaries),
            "cases": case_summaries
        }
