"""Team member models for the management system."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr


class ExperienceLevel(str, Enum):
    """Experience level for skills."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    """Represents a skill with proficiency level."""

    name: str
    experience_level: ExperienceLevel
    years_of_experience: Optional[float] = None


class TeamMemberRole(str, Enum):
    """Role of team member."""

    DEVELOPER = "developer"
    DESIGNER = "designer"
    PROJECT_MANAGER = "project_manager"
    QA_ENGINEER = "qa_engineer"
    DEVOPS = "devops"
    DATA_SCIENTIST = "data_scientist"
    PRODUCT_MANAGER = "product_manager"
    OTHER = "other"


class TeamMember(BaseModel):
    """Represents a team member with all their information."""

    id: Optional[str] = None  # Will be set after database/ClickUp creation
    name: str
    email: EmailStr
    role: TeamMemberRole
    skills: List[Skill] = []
    timezone: str = "UTC"
    hours_per_week: float = 40.0
    preferred_task_types: List[str] = []
    bio: Optional[str] = None
    clickup_user_id: Optional[str] = None  # ClickUp user ID
    gdoc_profile_id: Optional[str] = None  # Google Doc profile ID
    joined_date: datetime = datetime.now()
    is_active: bool = True

    # Metadata
    current_workload_hours: float = 0.0  # Estimated hours from current tasks
    availability_percentage: float = 100.0  # 0-100

    def get_availability_hours(self) -> float:
        """Calculate available hours per week."""
        return max(0, self.hours_per_week - self.current_workload_hours)

    def has_skill(
        self, skill_name: str, min_level: Optional[ExperienceLevel] = None
    ) -> bool:
        """
        Check if member has a specific skill.

        Args:
            skill_name: Name of skill to check
            min_level: Minimum experience level required

        Returns:
            True if member has the skill at required level
        """
        skill_name_lower = skill_name.lower()
        for skill in self.skills:
            if skill_name_lower in skill.name.lower():
                if min_level:
                    level_order = [
                        ExperienceLevel.BEGINNER,
                        ExperienceLevel.INTERMEDIATE,
                        ExperienceLevel.ADVANCED,
                        ExperienceLevel.EXPERT,
                    ]
                    return level_order.index(
                        skill.experience_level
                    ) >= level_order.index(min_level)
                return True
        return False

    def get_skill_score(self, required_skills: List[str]) -> float:
        """
        Calculate skill match score (0-100) based on required skills.

        Args:
            required_skills: List of required skill names

        Returns:
            Score from 0-100
        """
        if not required_skills:
            return 100.0

        matches = 0
        total_score = 0.0

        level_scores = {
            ExperienceLevel.BEGINNER: 0.25,
            ExperienceLevel.INTERMEDIATE: 0.50,
            ExperienceLevel.ADVANCED: 0.75,
            ExperienceLevel.EXPERT: 1.0,
        }

        for required_skill in required_skills:
            required_lower = required_skill.lower()
            best_match_score = 0.0

            for skill in self.skills:
                # Check for exact or partial match
                if (
                    required_lower in skill.name.lower()
                    or skill.name.lower() in required_lower
                ):
                    score = level_scores.get(skill.experience_level, 0.5)
                    best_match_score = max(best_match_score, score)

            total_score += best_match_score
            if best_match_score > 0:
                matches += 1

        # Calculate final score
        if len(required_skills) == 0:
            return 100.0

        # Average of matched skills * 100
        return (total_score / len(required_skills)) * 100


class TaskRequirement(BaseModel):
    """Requirements for a task to be assigned."""

    task_name: str
    task_description: str
    required_skills: List[str]
    estimated_hours: float
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    preferred_assignee: Optional[str] = None  # Email or name


class AssignmentScore(BaseModel):
    """Score for a team member's fit for a task."""

    member: TeamMember
    skill_score: float  # 0-100
    availability_score: float  # 0-100
    overall_score: float  # 0-100
    reason: str  # Explanation of the score

    @classmethod
    def calculate(
        cls, member: TeamMember, task_requirement: TaskRequirement
    ) -> "AssignmentScore":
        """
        Calculate assignment score for a member and task.

        Args:
            member: Team member to evaluate
            task_requirement: Task requirements

        Returns:
            AssignmentScore with calculated scores
        """
        # Calculate skill match
        skill_score = member.get_skill_score(task_requirement.required_skills)

        # Calculate availability
        available_hours = member.get_availability_hours()
        if available_hours >= task_requirement.estimated_hours:
            availability_score = 100.0
        elif available_hours > 0:
            availability_score = (
                available_hours / task_requirement.estimated_hours
            ) * 100
        else:
            availability_score = 0.0

        # Overall score (weighted: 60% skills, 40% availability)
        overall_score = (skill_score * 0.6) + (availability_score * 0.4)

        # Generate reason
        reasons = []
        if skill_score >= 80:
            reasons.append("strong skill match")
        elif skill_score >= 50:
            reasons.append("moderate skill match")
        else:
            reasons.append("weak skill match")

        if availability_score >= 80:
            reasons.append("good availability")
        elif availability_score >= 50:
            reasons.append("limited availability")
        else:
            reasons.append("low availability")

        reason = f"{member.name}: {', '.join(reasons)} (skill: {skill_score:.0f}%, availability: {availability_score:.0f}%)"

        return cls(
            member=member,
            skill_score=skill_score,
            availability_score=availability_score,
            overall_score=overall_score,
            reason=reason,
        )
