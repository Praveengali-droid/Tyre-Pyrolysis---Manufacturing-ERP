"""
Recipe Stage Model - Process stages within a recipe.

Each stage defines duration, required readings (Temp, Pressure),
and safe limits for operator safety alerts.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class RecipeStage(Base):
    """
    A single stage within a production recipe.
    
    Stages are executed in order_sequence during a batch.
    Each stage can require specific readings from operators
    and has safe limits for safety alerts.
    
    IoT-Ready: The required_readings JSON supports any parameter type:
    - temp_c: Temperature in Celsius
    - pressure_bar: Pressure in Bar
    - meter_kwh: Electricity meter reading
    - humidity_pct: Humidity percentage
    - custom fields as needed
    """
    __tablename__ = "recipe_stages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Parent recipe
    recipe_id = Column(Integer, ForeignKey("batch_recipes.id"), nullable=False)
    
    # Stage identity
    stage_name = Column(String(50), nullable=False)  # Loading, Heating, Distillation, Cooling, Unloading
    order_sequence = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    
    # Duration
    duration_minutes = Column(Integer, nullable=False, default=60)
    
    # Required readings (IoT-ready JSON list)
    # Example: ["temp_c", "pressure_bar", "meter_kwh"]
    required_readings = Column(JSON, default=list)
    
    # Safe limits for each reading (for alerts)
    # Example: {"temp_c": {"min": 0, "max": 450}, "pressure_bar": {"max": 1.0}}
    safe_limits = Column(JSON, default=dict)
    
    # Operator instructions
    instructions = Column(Text, nullable=True)
    
    # Target values (optional - for guidance)
    # Example: {"temp_c": 350, "pressure_bar": 0.2}
    target_values = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    recipe = relationship("BatchRecipe", back_populates="stages")
    
    def __repr__(self):
        return f"<RecipeStage {self.order_sequence}. {self.stage_name}>"
    
    def check_reading_limits(self, readings: dict) -> tuple[bool, list]:
        """
        Check if readings are within safe limits.
        
        Args:
            readings: Dict of reading values, e.g., {"temp_c": 350, "pressure_bar": 0.2}
            
        Returns:
            (is_within_limits, list_of_alerts)
        """
        alerts = []
        
        if not self.safe_limits or not readings:
            return True, []
        
        for param, value in readings.items():
            if param in self.safe_limits:
                limits = self.safe_limits[param]
                
                if "min" in limits and value < limits["min"]:
                    alerts.append(f"{param} too low: {value} < {limits['min']}")
                
                if "max" in limits and value > limits["max"]:
                    alerts.append(f"{param} too high: {value} > {limits['max']}")
        
        return len(alerts) == 0, alerts
    
    @property
    def is_unloading(self) -> bool:
        """Check if this is an unloading stage (for safety interlock)."""
        return self.stage_name.upper() in ["UNLOADING", "DISCHARGE", "EMPTYING"]
