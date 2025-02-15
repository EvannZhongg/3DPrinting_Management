import json
from typing import List, Dict

class Filament:
    def __init__(self, name: str, category: str, total_price: float, initial_amount: int, remaining: int = None):
        self.name = name
        self.category = category
        self.total_price = total_price
        self.initial_amount = initial_amount
        self.remaining = remaining if remaining is not None else initial_amount

    @property
    def price(self) -> float:
        return self.total_price / self.initial_amount if self.initial_amount > 0 else 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "total_price": self.total_price,
            "initial_amount": self.initial_amount,
            "remaining": self.remaining
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Filament':
        return cls(
            name=data["name"],
            category=data.get("category", "未分类"),
            total_price=data["total_price"],
            initial_amount=data["initial_amount"],
            remaining=data.get("remaining", data["initial_amount"])
        )

class FilamentManager:
    def __init__(self, filename: str = "filaments.json"):
        self.filaments = []
        self.filename = filename
        self.load_data()

    def add_filament(self, filament: Filament):
        self.filaments.append(filament)
        self.save_data()

    def find_filament(self, name: str) -> Filament:
        return next((f for f in self.filaments if f.name == name), None)

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump([filament.to_dict() for filament in self.filaments], f)

    def load_data(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.filaments = [Filament.from_dict(item) for item in data]
        except FileNotFoundError:
            self.filaments = []
