from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.entities import Course, SysUser, CommunityPost, Product
from pydantic import BaseModel

class CourseCreate(BaseModel):
    title: str
    category: str
    target_grade: str
    duration_min: int = 45
    energy_reward: int = 50
    cover_image_url: Optional[str] = None
    video_url: Optional[str] = None
    description: Optional[str] = None
    status: str = "ONLINE"

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    target_grade: Optional[str] = None
    duration_min: Optional[int] = None
    energy_reward: Optional[int] = None
    cover_image_url: Optional[str] = None
    video_url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class CRUDCourse(CRUDBase[Course, CourseCreate, CourseUpdate]):
    def get_by_category(self, db: Session, *, category: str) -> List[Course]:
        return db.query(Course).filter(Course.category == category, Course.status == "ONLINE").all()

    def get_by_grade(self, db: Session, *, grade: str) -> List[Course]:
        return db.query(Course).filter(Course.target_grade == grade, Course.status == "ONLINE").all()

    def toggle_status(self, db: Session, *, course_id: int) -> Optional[Course]:
        course = self.get(db, course_id)
        if course:
            course.status = "OFFLINE" if course.status == "ONLINE" else "ONLINE"
            db.commit()
            db.refresh(course)
        return course

class CRUDUser(CRUDBase[SysUser, BaseModel, BaseModel]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[SysUser]:
        return db.query(SysUser).filter(SysUser.username == username).first()

    def get_by_role(self, db: Session, *, role_code: str) -> List[SysUser]:
        return db.query(SysUser).filter(SysUser.role_code == role_code).all()

class CRUDPost(CRUDBase[CommunityPost, BaseModel, BaseModel]):
    def get_approved(self, db: Session, *, skip: int = 0, limit: int = 50) -> List[CommunityPost]:
        return db.query(CommunityPost).filter(CommunityPost.audit_status == "APPROVED").order_by(CommunityPost.id.desc()).offset(skip).limit(limit).all()

    def get_pending(self, db: Session) -> List[CommunityPost]:
        return db.query(CommunityPost).filter(CommunityPost.audit_status == "PENDING").all()

class CRUDMall(CRUDBase[Product, BaseModel, BaseModel]):
    def get_active_products(self, db: Session) -> List[Product]:
        return db.query(Product).filter(Product.status == "ACTIVE").all()

course = CRUDCourse(Course)
user = CRUDUser(SysUser)
post = CRUDPost(CommunityPost)
mall = CRUDMall(Product)
