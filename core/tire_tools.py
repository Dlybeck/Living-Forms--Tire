"""
Tire Tools using LangChain
Provides web search and tire data lookup capabilities
"""

from typing import Dict, Any, Optional
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
import re
import logging

logger = logging.getLogger(__name__)

class TireTools:
    """
    Collection of tools for tire research and verification
    """
    
    def __init__(self):
        self.search = DuckDuckGoSearchRun()
        self.wiki = WikipediaAPIWrapper()
        
        # Initialize tools
        self.tools = self._create_tools()
    
    def _create_tools(self) -> list[Tool]:
        """
        Create LangChain tools for tire research
        """
        return [
            Tool(
                name="tire_size_lookup",
                description="Look up tire size for a specific vehicle make, model, year, and trim. Use this when users don't know their tire size or need verification.",
                func=self._lookup_tire_size,
                return_direct=False
            ),
            Tool(
                name="vehicle_specs_search",
                description="Search for vehicle specifications including dimensions, weight, and other details that might affect tire selection.",
                func=self._search_vehicle_specs,
                return_direct=False
            ),
            Tool(
                name="tire_review_search",
                description="Search for tire reviews, ratings, and comparisons for specific tire models or types.",
                func=self._search_tire_reviews,
                return_direct=False
            ),
            Tool(
                name="weather_condition_search",
                description="Search for weather conditions and driving conditions in a specific location to recommend appropriate tire types.",
                func=self._search_weather_conditions,
                return_direct=False
            ),
            Tool(
                name="vin_decoder_search",
                description="Search for VIN decoder information to extract vehicle details from a VIN number.",
                func=self._decode_vin,
                return_direct=False
            )
        ]
    
    def _lookup_tire_size(self, query: str) -> str:
        """
        Look up tire size for a specific vehicle
        """
        try:
            # Enhance the search query for better results
            enhanced_query = f"tire size specifications {query} original equipment tires"
            results = self.search.run(enhanced_query)
            
            # Extract tire size patterns
            tire_patterns = [
                r'\d{3}/\d{2}R\d{2}',  # 205/55R16
                r'\d{3}-\d{2}R\d{2}',  # 205-55R16
                r'\d{3}/\d{2}ZR\d{2}', # 205/55ZR16
                r'P\d{3}/\d{2}R\d{2}', # P205/55R16
                r'LT\d{3}/\d{2}R\d{2}' # LT205/55R16
            ]
            
            found_sizes = []
            for pattern in tire_patterns:
                matches = re.findall(pattern, results, re.IGNORECASE)
                found_sizes.extend(matches)
            
            if found_sizes:
                unique_sizes = list(set(found_sizes))
                return f"Found tire sizes for {query}: {', '.join(unique_sizes)}. Source: {results[:200]}..."
            else:
                return f"Could not find specific tire sizes for {query}. Search results: {results[:300]}..."
                
        except Exception as e:
            logger.error(f"Error in tire size lookup: {e}")
            return f"Error searching for tire size: {str(e)}"
    
    def _search_vehicle_specs(self, query: str) -> str:
        """
        Search for vehicle specifications
        """
        try:
            enhanced_query = f"vehicle specifications {query} dimensions weight"
            results = self.search.run(enhanced_query)
            return f"Vehicle specifications for {query}: {results[:500]}..."
        except Exception as e:
            logger.error(f"Error in vehicle specs search: {e}")
            return f"Error searching for vehicle specifications: {str(e)}"
    
    def _search_tire_reviews(self, query: str) -> str:
        """
        Search for tire reviews and ratings
        """
        try:
            enhanced_query = f"tire reviews ratings {query} comparison"
            results = self.search.run(enhanced_query)
            return f"Tire reviews for {query}: {results[:500]}..."
        except Exception as e:
            logger.error(f"Error in tire review search: {e}")
            return f"Error searching for tire reviews: {str(e)}"
    
    def _search_weather_conditions(self, query: str) -> str:
        """
        Search for weather and driving conditions
        """
        try:
            enhanced_query = f"weather conditions driving {query} climate"
            results = self.search.run(enhanced_query)
            return f"Weather and driving conditions for {query}: {results[:500]}..."
        except Exception as e:
            logger.error(f"Error in weather search: {e}")
            return f"Error searching for weather conditions: {str(e)}"
    
    def _decode_vin(self, vin: str) -> str:
        """
        Decode VIN to get vehicle information
        """
        try:
            # Clean VIN
            vin = vin.strip().upper()
            if len(vin) != 17:
                return f"Invalid VIN length. VINs must be 17 characters. Provided: {len(vin)} characters."
            
            enhanced_query = f"VIN decoder {vin} vehicle information decode"
            results = self.search.run(enhanced_query)
            return f"VIN {vin} decoded information: {results[:500]}..."
        except Exception as e:
            logger.error(f"Error in VIN decoding: {e}")
            return f"Error decoding VIN: {str(e)}"
    
    def get_tools(self) -> list[Tool]:
        """
        Get all available tools
        """
        return self.tools
    
    def get_tool_names(self) -> list[str]:
        """
        Get list of available tool names
        """
        return [tool.name for tool in self.tools] 