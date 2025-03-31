from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, field_validator, Field, model_validator
import re

class TimeInfo(BaseModel):
    occur_time: str
    processing_time: str
    completion_time: str

    @field_validator('*', pre=True)
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
            return v
        except ValueError:
            raise ValueError("时间格式必须为 YYYY-MM-DD HH:MM")

class LocationInfo(BaseModel):
    province: str
    city: str
    district: str
    street: str = Field(..., max_length=50)
    detail: str = Field(..., max_length=100)

class SubjectInfo(BaseModel):
    name: str
    sexuality: str = Field(..., regex='^(男|女|暂无)$')
    phone: Union[str, None] = Field(default="暂无", max_length=20)
    id_card: Union[str, None] = Field(default="暂无", max_length=20)

    @field_validator('phone', pre=True)
    def validate_phone(cls, v):
        if v in ["暂无", None]:
            return "暂无"
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式无效')
        return v
    
    @field_validator('id_card', pre=True)
    def validate_id_card(cls, v):
        if v in ["暂无", None]:
            return "暂无"
        if not re.match(r'^\d{17}[\dXx]$', v):
            raise ValueError('身份证号格式无效')
        return v

class ActionDetails(BaseModel):
    subject: List[SubjectInfo]
    object: List[SubjectInfo]
    actions: str = Field(..., max_length=500)

class JurisdictionInfo(BaseModel):
    authority: str
    lead_officer: List[str]
    assistants: List[str]

class FinancialInfo(BaseModel):
    amount: float
    currency: str = Field(default="CNY")

class PersonInfo(BaseModel):
    total: int
    injured: str
    fatalities: int

class AddressInfo(BaseModel):
    type: str = Field(..., regex='^(案发地|户籍地|公司注册地)$')
    full_address: str

class SpecialFlags(BaseModel):
    police_involvement: bool
    physical_conflict: bool
    group_event: bool
    religious_factor: bool

class ElementsInfo(BaseModel):
    financial: FinancialInfo
    person: PersonInfo
    addresses: List[AddressInfo]
    organizations: List[str]
    special_flags: SpecialFlags

class RelationshipItem(BaseModel):
    person_1: Dict[str, str]
    person_2: Dict[str, str]
    relationship: str

class CaseRelationships(BaseModel):
    individual: List[RelationshipItem]
    person_multiEvent: Optional[Dict[str, str]] = None
    person_multiOccur: Optional[Dict[str, str]] = None
    location_multiEvent: Optional[Dict[str, str]] = None
    location_multiOccur: Optional[Dict[str, str]] = None

class CaseDegree(BaseModel):
    is_major: bool
    is_sensitive: bool

class CaseData(BaseModel):
    id: str = Field(..., min_length=10, max_length=20)
    title: str = Field(..., max_length=25)
    keywords: List[str]
    time: TimeInfo
    location: LocationInfo
    details: ActionDetails
    jurisdiction: JurisdictionInfo
    resolution: str
    elements: ElementsInfo
    degree: CaseDegree
    relationships: CaseRelationships

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                # 此处添加示例结构，与用户提供的JSON示例一致
            }
        }

    @model_validator(pre=True)
    def set_defaults(cls, values):
        # 确保嵌套字段都有默认值
        if 'relationships' not in values:
            values['relationships'] = {}
        if 'special_flags' not in values.get('elements', {}):
            values['elements']['special_flags'] = {}
        return values