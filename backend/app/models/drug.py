"""
PharmaMind AI - Drug, Ingredient, and Synonym Data Models
"""

import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

class Drug(Base, TimestampMixin):
    __tablename__ = "drugs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    generic_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    rxnorm_cui: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    atc_code: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    drug_class: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mechanism_of_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    route_of_administration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_fda_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    ingredients: Mapped[List["DrugIngredient"]] = relationship("DrugIngredient", back_populates="drug", cascade="all, delete-orphan")
    synonyms: Mapped[List["DrugSynonym"]] = relationship("DrugSynonym", back_populates="drug", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_drugs_generic_name_lower", "generic_name"),
    )


class Ingredient(Base, TimestampMixin):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    unii: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    pubchem_cid: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    chemical_formula: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    molecular_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    drugs: Mapped[List["DrugIngredient"]] = relationship("DrugIngredient", back_populates="ingredient")


class DrugIngredient(Base):
    __tablename__ = "drug_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id", ondelete="CASCADE"), index=True, nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredients.id", ondelete="CASCADE"), index=True, nullable=False)
    strength: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    drug: Mapped["Drug"] = relationship("Drug", back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="drugs")


class DrugSynonym(Base):
    __tablename__ = "drug_synonyms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id", ondelete="CASCADE"), index=True, nullable=False)
    synonym: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="RxNorm", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    drug: Mapped["Drug"] = relationship("Drug", back_populates="synonyms")

