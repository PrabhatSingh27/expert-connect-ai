from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class ExpertBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )


class ExpertSignup(ExpertBaseModel):
    full_name: str = Field(
        default="",
        validation_alias=AliasChoices("full_name", "fullName", "name"),
    )
    email: str
    phone: str = Field(
        default="",
        validation_alias=AliasChoices("phone", "phoneNumber", "mobile", "phone_number"),
    )
    government_id: str = Field(
        default="",
        validation_alias=AliasChoices("government_id", "governmentId", "governmentID", "govtId", "govtID"),
    )
    government_id_file_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("government_id_file_url", "governmentIdFileUrl"),
    )
    skills: str = ""
    service_area: str = Field(
        default="",
        validation_alias=AliasChoices("service_area", "serviceArea", "area"),
    )
    service_city: str | None = Field(
        default=None,
        validation_alias=AliasChoices("service_city", "serviceCity", "city"),
    )
    service_pincodes: str | None = Field(
        default=None,
        validation_alias=AliasChoices("service_pincodes", "servicePincodes", "pincodes"),
    )
    bio: str | None = None
    permanent_address: str = Field(
        default="",
        validation_alias=AliasChoices("permanent_address", "permanentAddress", "address"),
    )
    profile_image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("profile_image_url", "profileImageUrl"),
    )
    experience_years: int = Field(
        default=0,
        validation_alias=AliasChoices("experience_years", "experienceYears"),
    )
    password: str

    @model_validator(mode="before")
    @classmethod
    def normalize_form_payload(cls, data: Any):
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "fullName" not in normalized and "full_name" not in normalized and "name" not in normalized:
            first_name = normalized.get("firstName") or normalized.get("first_name")
            last_name = normalized.get("lastName") or normalized.get("last_name")
            if first_name or last_name:
                normalized["fullName"] = " ".join(
                    part for part in [first_name, last_name] if part
                )

        return normalized

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_skills(cls, value):
        if value is None:
            return ""
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item)
        return str(value)


class ExpertLogin(BaseModel):
    email: str
    password: str


class ExpertResponse(ExpertBaseModel):
    id: int
    full_name: str = Field(alias="fullName")
    email: str
    phone: str
    government_id: str = Field(alias="governmentId")
    government_id_file_url: str | None = Field(default=None, alias="governmentIdFileUrl")
    skills: str
    service_area: str = Field(alias="serviceArea")
    service_city: str | None = Field(default=None, alias="serviceCity")
    service_pincodes: str | None = Field(default=None, alias="servicePincodes")
    bio: str | None = None
    permanent_address: str = Field(alias="permanentAddress")
    profile_image_url: str | None = Field(default=None, alias="profileImageUrl")
    experience_years: int = Field(alias="experienceYears")
    is_verified: bool = Field(alias="isVerified")
    is_active: bool = Field(alias="isActive")
    created_at: datetime
    updated_at: datetime


class ExpertUpdate(ExpertBaseModel):
    full_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("full_name", "fullName"),
    )
    phone: str | None = Field(
        default=None,
        validation_alias=AliasChoices("phone", "phoneNumber"),
    )
    government_id_file_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("government_id_file_url", "governmentIdFileUrl"),
    )
    skills: str | None = None
    service_area: str | None = Field(
        default=None,
        validation_alias=AliasChoices("service_area", "serviceArea"),
    )
    service_city: str | None = Field(
        default=None,
        validation_alias=AliasChoices("service_city", "serviceCity", "city"),
    )
    service_pincodes: str | None = Field(
        default=None,
        validation_alias=AliasChoices("service_pincodes", "servicePincodes", "pincodes"),
    )
    bio: str | None = None
    permanent_address: str | None = Field(
        default=None,
        validation_alias=AliasChoices("permanent_address", "permanentAddress"),
    )
    profile_image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("profile_image_url", "profileImageUrl"),
    )
    experience_years: int | None = Field(
        default=None,
        validation_alias=AliasChoices("experience_years", "experienceYears"),
    )

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_skills(cls, value):
        if value is None:
            return None
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item)
        return str(value)
