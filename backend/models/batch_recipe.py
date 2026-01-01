"""
Batch Recipe Model - Configurable production process templates.

Each recipe defines the stages (Heating, Distillation, Cooling)
and expected parameters for different tyre types.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BatchRecipe(Base):
    """
    Production recipe template.
    
    Recipes are reusable process definitions that can be assigned
    to production batches. Different tyre types (Radial, Nylon)
    require different temperature profiles and durations.
    """
    __tablename__ = "batch_recipes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    recipe_code = Column(String(30), unique=True, nullable=False, index=True)  # RECIPE-RADIAL
    name = Column(String(100), nullable=False)  # Radial Tyre Cycle
    description = Column(Text, nullable=True)  # Detailed description
    
    # Tyre type this recipe is designed for
    tyre_type = Column(String(50), nullable=True)  # Radial, Nylon, Mixed
    
    # Calculated from stages
    total_duration_minutes = Column(Integer, default=0)
    stage_count = Column(Integer, default=0)
    
    # Status
    is_default = Column(Boolean, default=False)  # Default recipe for quick start
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    stages = relationship("RecipeStage", back_populates="recipe", order_by="RecipeStage.order_sequence")
    
    def __repr__(self):
        return f"<BatchRecipe {self.recipe_code}: {self.name}>"
    
    def calculate_totals(self):
        """Recalculate total duration from stages."""
        if self.stages:
            self.total_duration_minutes = sum(s.duration_minutes or 0 for s in self.stages)
            self.stage_count = len(self.stages)
