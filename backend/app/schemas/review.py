from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    rating: int
    review: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5")
        return value


class FeedbackCreate(ReviewCreate):
    issue_id: int = Field(validation_alias=AliasChoices("issue_id", "issueId"))


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    issue_id: int = Field(alias="issueId")
    expert_id: int = Field(alias="expertId")
    customer_id: int = Field(alias="customerId")
    rating: int
    review: str | None = None
    created_at: datetime = Field(alias="createdAt")
