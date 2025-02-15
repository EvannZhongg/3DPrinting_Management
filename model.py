import json
from typing import List, Dict

class Model:
    def __init__(self, name: str, materials: list, quantity: int = 1):
        """
        :param materials: [{"filament": "耗材名称", "weight": 重量(g)}, ...]
        """
        self.name = name
        self.materials = materials  # 改为耗材列表
        self.quantity = quantity

    @property
    def total_cost(self, filament_manager) -> float:
        total = 0
        for material in self.materials:
            filament = filament_manager.find_filament(material["filament"])
            if filament:
                total += filament.price * material["weight"]
        return total * self.quantity

    @property
    def unit_cost(self, filament_manager) -> float:
        return self.total_cost(filament_manager) / self.quantity if self.quantity > 0 else 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "materials": self.materials,
            "quantity": self.quantity
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Model':
        return cls(
            name=data["name"],
            materials=data["materials"],
            quantity=data.get("quantity", 1)
        )
class ModelManager:
    def __init__(self, filename: str = "models.json"):
        self.models = []
        self.filename = filename
        self.load_data()

    def add_model(self, model: Model):
        self.models.append(model)
        self.save_data()

    def find_model(self, name: str) -> Model:
        for m in self.models:
            if m.name == name:
                return m
        return None

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump([model.to_dict() for model in self.models], f)

    def load_data(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.models = [Model.from_dict(item) for item in data]
        except FileNotFoundError:
            self.models = []
