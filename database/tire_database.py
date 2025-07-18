import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TireRecommendation:
    """Individual tire recommendation"""
    brand: str
    model: str
    size: str
    price: float
    type: str
    characteristics: List[str]
    pros: List[str]
    cons: List[str]
    best_for: List[str]
    warranty_miles: int
    performance_rating: float

@dataclass
class VehicleInfo:
    """Vehicle information"""
    make: str
    model: str
    year_range: str
    oem_tire_sizes: List[str]
    alternative_sizes: List[str]
    oem_brands: List[str]
    wheel_bolt_pattern: str
    special_requirements: List[str]

class TireDatabase:
    """
    Comprehensive tire database with vehicles and tire information
    Serves as the static knowledge base for the living form
    """
    
    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file or "database/tire_data.json"
        self.data = self._load_database()
        self.vehicles = self.data.get("vehicles", {})
        self.tires = self.data.get("tires", {})
        self.tire_sizes = self.data.get("tire_sizes", {})
        self.brands = self.data.get("brands", {})
        
        logger.info(f"Loaded tire database with {len(self.vehicles)} vehicles and {len(self.tires)} tires")
    
    def _load_database(self) -> Dict[str, Any]:
        """Load tire database from JSON file"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default database if file doesn't exist
                return self._create_default_database()
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return self._create_default_database()
    
    def _create_default_database(self) -> Dict[str, Any]:
        """Create comprehensive default tire database"""
        return {
            "vehicles": {
                "honda_accord_2018_2022": {
                    "make": "Honda",
                    "model": "Accord",
                    "year_range": "2018-2022",
                    "oem_tire_sizes": ["225/60R16", "235/45R18", "245/40R19"],
                    "alternative_sizes": ["215/65R16", "235/50R18"],
                    "oem_brands": ["Michelin", "Bridgestone", "Continental"],
                    "wheel_bolt_pattern": "5x114.3",
                    "special_requirements": ["Standard pressure monitoring", "Low rolling resistance preferred"]
                },
                "toyota_camry_2017_2023": {
                    "make": "Toyota",
                    "model": "Camry",
                    "year_range": "2017-2023",
                    "oem_tire_sizes": ["215/60R16", "235/45R18", "245/40R19"],
                    "alternative_sizes": ["215/65R16", "225/60R16"],
                    "oem_brands": ["Michelin", "Bridgestone", "Dunlop"],
                    "wheel_bolt_pattern": "5x114.3",
                    "special_requirements": ["TPMS required", "Fuel efficiency focus"]
                },
                "ford_f150_2015_2023": {
                    "make": "Ford",
                    "model": "F-150",
                    "year_range": "2015-2023",
                    "oem_tire_sizes": ["245/70R17", "275/55R20", "275/45R22"],
                    "alternative_sizes": ["245/75R17", "265/60R18"],
                    "oem_brands": ["BFGoodrich", "Michelin", "Pirelli"],
                    "wheel_bolt_pattern": "6x135",
                    "special_requirements": ["Load rating important", "All-terrain capability"]
                },
                "honda_civic_2016_2023": {
                    "make": "Honda",
                    "model": "Civic",
                    "year_range": "2016-2023",
                    "oem_tire_sizes": ["215/55R16", "235/40R18", "245/30R20"],
                    "alternative_sizes": ["205/60R16", "225/45R17"],
                    "oem_brands": ["Michelin", "Continental", "Bridgestone"],
                    "wheel_bolt_pattern": "5x114.3",
                    "special_requirements": ["Low profile on sport models", "Fuel economy focus"]
                },
                "toyota_rav4_2019_2023": {
                    "make": "Toyota",
                    "model": "RAV4",
                    "year_range": "2019-2023",
                    "oem_tire_sizes": ["225/65R17", "235/55R19"],
                    "alternative_sizes": ["225/70R16", "235/60R18"],
                    "oem_brands": ["Falken", "Bridgestone", "Michelin"],
                    "wheel_bolt_pattern": "5x114.3",
                    "special_requirements": ["AWD capability", "Light off-road use"]
                },
                "kia_forte_2019_2023": {
                    "make": "Kia",
                    "model": "Forte",
                    "year_range": "2019-2023",
                    "oem_tire_sizes": ["205/55R16", "225/45R17"],
                    "alternative_sizes": ["215/60R16", "205/60R16"],
                    "oem_brands": ["Nexen", "Kumho", "Hankook"],
                    "wheel_bolt_pattern": "5x114.3",
                    "special_requirements": ["Fuel efficiency focus", "Compact car sizing"]
                }
            },
            "tires": {
                "michelin_defender_th": {
                    "brand": "Michelin",
                    "model": "Defender T+H",
                    "type": "all-season",
                    "available_sizes": ["215/60R16", "225/60R16", "235/60R16", "215/55R16", "225/55R17"],
                    "price_range": [115, 135],
                    "characteristics": ["longevity", "comfort", "wet_traction", "fuel_efficiency"],
                    "pros": ["Exceptional tread life", "Comfortable ride", "Great wet weather performance"],
                    "cons": ["Higher price point", "Limited performance in snow"],
                    "best_for": ["daily_driving", "highway", "fuel_economy"],
                    "warranty_miles": 80000,
                    "performance_rating": 4.5
                },
                "bridgestone_turanza_quiettrack": {
                    "brand": "Bridgestone",
                    "model": "Turanza QuietTrack",
                    "type": "all-season",
                    "available_sizes": ["215/60R16", "225/60R16", "235/60R16", "235/45R18"],
                    "price_range": [105, 125],
                    "characteristics": ["quiet", "comfort", "wet_traction", "durability"],
                    "pros": ["Very quiet ride", "Good wet performance", "Comfortable"],
                    "cons": ["Average snow performance", "Moderate tread life"],
                    "best_for": ["daily_driving", "comfort", "quiet_ride"],
                    "warranty_miles": 80000,
                    "performance_rating": 4.3
                },
                "continental_truecontact_tour": {
                    "brand": "Continental",
                    "model": "TrueContact Tour",
                    "type": "all-season",
                    "available_sizes": ["215/60R16", "225/60R16", "235/60R16", "215/55R16"],
                    "price_range": [100, 120],
                    "characteristics": ["balanced", "wet_traction", "comfort", "durability"],
                    "pros": ["Balanced performance", "Good value", "Reliable wet traction"],
                    "cons": ["Not exceptional in any category", "Average snow performance"],
                    "best_for": ["daily_driving", "value", "balanced_performance"],
                    "warranty_miles": 80000,
                    "performance_rating": 4.2
                },
                "general_altimax_rt43": {
                    "brand": "General",
                    "model": "Altimax RT43",
                    "type": "all-season",
                    "available_sizes": ["215/60R16", "225/60R16", "235/60R16", "215/55R16", "225/55R17"],
                    "price_range": [75, 95],
                    "characteristics": ["budget", "durability", "wet_traction", "value"],
                    "pros": ["Great value", "Decent tread life", "Good wet performance for price"],
                    "cons": ["Road noise", "Limited performance capabilities"],
                    "best_for": ["budget", "daily_driving", "value"],
                    "warranty_miles": 75000,
                    "performance_rating": 3.8
                },
                "michelin_pilot_sport_4s": {
                    "brand": "Michelin",
                    "model": "Pilot Sport 4S",
                    "type": "summer",
                    "available_sizes": ["235/45R18", "245/40R19", "245/30R20", "235/40R18"],
                    "price_range": [180, 250],
                    "characteristics": ["performance", "handling", "dry_traction", "wet_traction"],
                    "pros": ["Exceptional dry performance", "Excellent handling", "Good wet traction"],
                    "cons": ["Expensive", "Not for winter use", "Road noise"],
                    "best_for": ["performance", "sports_cars", "track_use"],
                    "warranty_miles": 30000,
                    "performance_rating": 4.8
                },
                "bridgestone_blizzak_ws90": {
                    "brand": "Bridgestone",
                    "model": "Blizzak WS90",
                    "type": "winter",
                    "available_sizes": ["215/60R16", "225/60R16", "235/60R16", "215/55R16"],
                    "price_range": [120, 150],
                    "characteristics": ["winter", "snow_traction", "ice_traction", "cold_weather"],
                    "pros": ["Excellent snow performance", "Great ice traction", "Proven winter performance"],
                    "cons": ["Poor warm weather performance", "Fast wear in heat"],
                    "best_for": ["winter", "snow", "ice", "cold_climates"],
                    "warranty_miles": 0,
                    "performance_rating": 4.7
                },
                "bfgoodrich_all_terrain_ta_ko2": {
                    "brand": "BFGoodrich",
                    "model": "All-Terrain T/A KO2",
                    "type": "all-terrain",
                    "available_sizes": ["245/70R17", "275/55R20", "275/45R22", "245/75R17"],
                    "price_range": [150, 200],
                    "characteristics": ["all_terrain", "durability", "traction", "toughness"],
                    "pros": ["Excellent off-road capability", "Very durable", "Good traction"],
                    "cons": ["Road noise", "Lower fuel economy", "Expensive"],
                    "best_for": ["off_road", "trucks", "suv", "adventure"],
                    "warranty_miles": 50000,
                    "performance_rating": 4.4
                }
            },
            "tire_sizes": {
                "215/60R16": {
                    "width": 215,
                    "aspect_ratio": 60,
                    "construction": "radial",
                    "wheel_diameter": 16,
                    "overall_diameter": 26.2,
                    "common_vehicles": ["Honda Civic", "Toyota Camry", "Nissan Sentra"],
                    "load_index": 95,
                    "speed_rating": "H"
                },
                "225/60R16": {
                    "width": 225,
                    "aspect_ratio": 60,
                    "construction": "radial",
                    "wheel_diameter": 16,
                    "overall_diameter": 26.6,
                    "common_vehicles": ["Honda Accord", "Toyota Camry", "Mazda6"],
                    "load_index": 98,
                    "speed_rating": "H"
                },
                "235/45R18": {
                    "width": 235,
                    "aspect_ratio": 45,
                    "construction": "radial",
                    "wheel_diameter": 18,
                    "overall_diameter": 26.3,
                    "common_vehicles": ["Honda Accord Sport", "Toyota Camry XSE", "Nissan Altima"],
                    "load_index": 94,
                    "speed_rating": "V"
                }
            },
            "brands": {
                "michelin": {
                    "name": "Michelin",
                    "country": "France",
                    "reputation": "premium",
                    "strengths": ["longevity", "wet_performance", "comfort"],
                    "typical_price_range": "high",
                    "warranty_reputation": "excellent"
                },
                "bridgestone": {
                    "name": "Bridgestone",
                    "country": "Japan",
                    "reputation": "premium",
                    "strengths": ["technology", "performance", "variety"],
                    "typical_price_range": "high",
                    "warranty_reputation": "very_good"
                },
                "continental": {
                    "name": "Continental",
                    "country": "Germany",
                    "reputation": "premium",
                    "strengths": ["wet_performance", "technology", "safety"],
                    "typical_price_range": "high",
                    "warranty_reputation": "very_good"
                },
                "general": {
                    "name": "General",
                    "country": "USA",
                    "reputation": "value",
                    "strengths": ["value", "durability", "availability"],
                    "typical_price_range": "low",
                    "warranty_reputation": "good"
                }
            }
        }
    
    def find_vehicle_by_make_model_year(self, make: str, model: str, year: int) -> Optional[VehicleInfo]:
        """Find vehicle information by make, model, and year"""
        make_lower = make.lower()
        model_lower = model.lower()
        
        for vehicle_key, vehicle_data in self.vehicles.items():
            if (make_lower in vehicle_data["make"].lower() and 
                model_lower in vehicle_data["model"].lower()):
                
                # Check if year is in range
                year_range = vehicle_data["year_range"]
                if self._year_in_range(year, year_range):
                    return VehicleInfo(
                        make=vehicle_data["make"],
                        model=vehicle_data["model"],
                        year_range=vehicle_data["year_range"],
                        oem_tire_sizes=vehicle_data["oem_tire_sizes"],
                        alternative_sizes=vehicle_data.get("alternative_sizes", []),
                        oem_brands=vehicle_data.get("oem_brands", []),
                        wheel_bolt_pattern=vehicle_data.get("wheel_bolt_pattern", ""),
                        special_requirements=vehicle_data.get("special_requirements", [])
                    )
        
        return None
    
    def _year_in_range(self, year: int, year_range: str) -> bool:
        """Check if year is within the specified range"""
        try:
            # Ensure year is an integer
            year_int = int(year) if isinstance(year, str) else year
            
            if '-' in year_range:
                start_year, end_year = year_range.split('-')
                return int(start_year) <= year_int <= int(end_year)
            else:
                return year_int == int(year_range)
        except (ValueError, TypeError):
            return False
    
    def get_tire_recommendations(self, vehicle_info: VehicleInfo, preferences: Dict[str, Any]) -> List[TireRecommendation]:
        """Get tire recommendations based on vehicle and preferences"""
        recommendations = []
        
        # Get available tire sizes for this vehicle
        available_sizes = vehicle_info.oem_tire_sizes + vehicle_info.alternative_sizes
        
        # Filter tires based on preferences
        for tire_key, tire_data in self.tires.items():
            if self._tire_matches_preferences(tire_data, preferences, available_sizes):
                recommendation = TireRecommendation(
                    brand=tire_data["brand"],
                    model=tire_data["model"],
                    size=self._get_best_size_match(tire_data["available_sizes"], available_sizes),
                    price=self._get_price_for_size(tire_data["price_range"]),
                    type=tire_data["type"],
                    characteristics=tire_data["characteristics"],
                    pros=tire_data["pros"],
                    cons=tire_data["cons"],
                    best_for=tire_data["best_for"],
                    warranty_miles=tire_data["warranty_miles"],
                    performance_rating=tire_data["performance_rating"]
                )
                recommendations.append(recommendation)
        
        # Sort by preference match score
        recommendations.sort(key=lambda x: self._calculate_preference_score(x, preferences), reverse=True)
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _tire_matches_preferences(self, tire_data: Dict[str, Any], preferences: Dict[str, Any], available_sizes: List[str]) -> bool:
        """Check if tire matches user preferences"""
        # Check if tire is available in compatible sizes
        if not any(size in tire_data["available_sizes"] for size in available_sizes):
            return False
        
        # Check budget constraints
        budget = preferences.get("budget", "mid")
        tire_price = sum(tire_data["price_range"]) / 2  # Average price
        
        if budget == "low" and tire_price > 100:
            return False
        elif budget == "high" and tire_price < 120:
            # For high budget, don't show lowest tier tires
            pass
        
        # Check tire type preferences
        usage_type = preferences.get("usage_type", "daily_driving")
        if usage_type == "performance" and tire_data["type"] not in ["summer", "performance"]:
            return False
        elif usage_type == "winter" and tire_data["type"] != "winter":
            return False
        
        return True
    
    def _get_best_size_match(self, tire_sizes: List[str], vehicle_sizes: List[str]) -> str:
        """Get the best size match between tire and vehicle"""
        for vehicle_size in vehicle_sizes:
            if vehicle_size in tire_sizes:
                return vehicle_size
        return tire_sizes[0] if tire_sizes else ""
    
    def _get_price_for_size(self, price_range: List[float]) -> float:
        """Get price (average of range)"""
        return sum(price_range) / len(price_range)
    
    def _calculate_preference_score(self, recommendation: TireRecommendation, preferences: Dict[str, Any]) -> float:
        """Calculate how well this recommendation matches user preferences"""
        score = 0.0
        
        # Base score from performance rating
        score += recommendation.performance_rating
        
        # Budget preference
        budget = preferences.get("budget", "mid")
        if budget == "low" and recommendation.price < 100:
            score += 2.0
        elif budget == "high" and recommendation.price > 150:
            score += 1.5
        elif budget == "mid" and 100 <= recommendation.price <= 150:
            score += 1.0
        
        # Usage type preference
        usage_type = preferences.get("usage_type", "daily_driving")
        if usage_type in recommendation.best_for:
            score += 2.0
        
        # Performance priorities
        priorities = preferences.get("performance_priorities", [])
        if isinstance(priorities, list):
            for priority in priorities:
                if priority.lower() in [char.lower() for char in recommendation.characteristics]:
                    score += 1.0
        
        return score
    
    def get_tire_by_brand_model(self, brand: str, model: str) -> Optional[Dict[str, Any]]:
        """Get tire information by brand and model"""
        for tire_key, tire_data in self.tires.items():
            if (brand.lower() in tire_data["brand"].lower() and 
                model.lower() in tire_data["model"].lower()):
                return tire_data
        return None
    
    def get_compatible_tire_sizes(self, vehicle_info: VehicleInfo) -> List[str]:
        """Get all compatible tire sizes for a vehicle"""
        return vehicle_info.oem_tire_sizes + vehicle_info.alternative_sizes
    

    
    def search_vehicles(self, query: str) -> List[Dict[str, Any]]:
        """Search vehicles by query"""
        results = []
        query_lower = query.lower()
        
        for vehicle_key, vehicle_data in self.vehicles.items():
            if (query_lower in vehicle_data["make"].lower() or 
                query_lower in vehicle_data["model"].lower() or 
                query_lower in vehicle_key.lower()):
                results.append(vehicle_data)
        
        return results
    
    def search_tires(self, query: str) -> List[Dict[str, Any]]:
        """Search tires by query"""
        results = []
        query_lower = query.lower()
        
        for tire_key, tire_data in self.tires.items():
            if (query_lower in tire_data["brand"].lower() or 
                query_lower in tire_data["model"].lower() or 
                query_lower in tire_data["type"].lower()):
                results.append(tire_data)
        
        return results 