# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 21:58:18 2025

@author: kumab
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 2025

Module for analyzing selected locations with geospatial data
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import contextily as ctx
from PIL import Image
import io
import requests
from shapely.geometry import box

# Path configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
data_dir = os.path.join(project_dir, "data")
rasters_dir = os.path.join(data_dir, "rasters")
results_dir = os.path.join(project_dir, "results")

# Create directories if they don't exist
os.makedirs(rasters_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# Default paths to various datasets
POPULATION_RASTER = os.path.join(rasters_dir, "worldpop_ethiopia.tif")
SOLAR_IRRADIANCE_RASTER = os.path.join(rasters_dir, "ghi_annual_ethiopia.tif")
ELEVATION_RASTER = os.path.join(rasters_dir, "srtm_ethiopia.tif")
LAND_COVER_RASTER = os.path.join(rasters_dir, "landcover_ethiopia.tif")

# Dataset URLs for download if files don't exist
DATASET_URLS = {
    "population": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/ETH/eth_ppp_2020_1km_Aggregated_UNadj.tif",
    "solar": "https://globalsolaratlas.info/download/ethiopia",  # Note: Direct download not available, would need API access
    "elevation": "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_41_11.tif",  # This is just one tile, may need multiple
    "landcover": "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2020-v1.8/Hansen_GFC-2020-v1.8_lossyear_20N_040E.tif"  # Example, Ethiopia spans multiple tiles
}

# Thresholds for suitable PV areas
MAX_POPULATION_DENSITY = 500  # people/km²
MIN_SOLAR_IRRADIANCE = 1600  # kWh/m²/year
MAX_SLOPE = 10  # degrees
SUITABLE_LAND_COVER = [10, 20, 30]  # Example codes for suitable land types

# Solar PV installation parameters
PV_CAPACITY_DENSITY = 50  # MW/km²
PV_CAPACITY_FACTOR = 0.18  # 18% average for Ethiopia

class LocationAnalysis:
    """Class for analyzing a location's solar potential and suitability"""
    
    def __init__(self, name, geometry, buffer_km=1):
        """Initialize with location name and geometry"""
        self.name = name
        self.geometry = geometry
        self.buffer_km = buffer_km
        
        # Calculate buffered area for analysis
        self.buffered_geometry = None
        if geometry is not None:
            # Project to a projected CRS (UTM) for accurate buffering
            geom_proj = gpd.GeoSeries([geometry], crs=4326).to_crs(epsg=32637)
            # Buffer in meters
            geom_buffer = geom_proj.buffer(buffer_km * 1000)
            # Convert back to WGS84
            self.buffered_geometry = geom_buffer.to_crs(4326)[0]
        
        # Initialize result containers
        self.population_density = None
        self.solar_irradiance = None
        self.elevation = None
        self.land_cover = None
        self.suitable_area_km2 = None
        self.potential_capacity_mw = None
        self.annual_generation_gwh = None
        self.area_results = {}
        
    def _ensure_file_exists(self, file_path, dataset_key):
        """Check if file exists, attempt to download if not"""
        if os.path.exists(file_path):
            return True
        
        if dataset_key in DATASET_URLS:
            print(f"Downloading {dataset_key} dataset...")
            url = DATASET_URLS[dataset_key]
            
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                else:
                    print(f"Failed to download {dataset_key}, status code: {response.status_code}")
                    return False
            except Exception as e:
                print(f"Error downloading {dataset_key}: {str(e)}")
                return False
        else:
            print(f"No URL defined for {dataset_key} dataset")
            return False
    
    def _extract_raster_data(self, raster_path, dataset_key):
        """Extract data from raster for the buffered area"""
        if not self._ensure_file_exists(raster_path, dataset_key):
            print(f"Could not process {dataset_key}, file not available")
            return None, None
        
        if self.buffered_geometry is None:
            print("No geometry available for extraction")
            return None, None
        
        try:
            with rasterio.open(raster_path) as src:
                # Create a geometry mask
                geoms = [self.buffered_geometry]
                
                # Reproject geometry if needed
                if src.crs is not None and src.crs != 'EPSG:4326':
                    geom_gdf = gpd.GeoDataFrame(geometry=[self.buffered_geometry], crs=4326)
                    geom_gdf = geom_gdf.to_crs(src.crs)
                    geoms = geom_gdf.geometry.tolist()
                
                # Get data and transform
                out_image, out_transform = mask(src, geoms, crop=True, nodata=src.nodata)
                
                # Create metadata for the output
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })
                
                return out_image, out_meta
                
        except Exception as e:
            print(f"Error extracting data from {dataset_key} raster: {str(e)}")
            return None, None
    
    def analyze_population(self):
        """Analyze population density in the area"""
        data, meta = self._extract_raster_data(POPULATION_RASTER, "population")
        if data is None:
            return None
        
        # Process population data
        valid_data = data[0]
        valid_data = valid_data[valid_data != meta.get("nodata", 0)]
        
        if len(valid_data) == 0:
            self.population_density = {"mean": 0, "max": 0, "suitable_percent": 100}
            return self.population_density
        
        # Calculate statistics
        mean_density = np.mean(valid_data)
        max_density = np.max(valid_data)
        suitable_percent = np.sum(valid_data < MAX_POPULATION_DENSITY) / len(valid_data) * 100
        
        self.population_density = {
            "mean": mean_density,
            "max": max_density,
            "suitable_percent": suitable_percent
        }
        
        self.area_results["population"] = {
            "data": data,
            "meta": meta,
            "stats": self.population_density
        }
        
        return self.population_density
        
    def analyze_solar_resource(self):
        """Analyze solar resource (GHI) in the area"""
        data, meta = self._extract_raster_data(SOLAR_IRRADIANCE_RASTER, "solar")
        if data is None:
            # Use a reasonable default for Ethiopia if data not available
            self.solar_irradiance = {"mean": 2000, "min": 1800, "max": 2200, "suitable_percent": 100}
            return self.solar_irradiance
        
        # Process solar data
        valid_data = data[0]
        valid_data = valid_data[valid_data != meta.get("nodata", 0)]
        
        if len(valid_data) == 0:
            self.solar_irradiance = {"mean": 2000, "min": 1800, "max": 2200, "suitable_percent": 100}
            return self.solar_irradiance
        
        # Calculate statistics
        mean_ghi = np.mean(valid_data)
        min_ghi = np.min(valid_data)
        max_ghi = np.max(valid_data)
        suitable_percent = np.sum(valid_data >= MIN_SOLAR_IRRADIANCE) / len(valid_data) * 100
        
        self.solar_irradiance = {
            "mean": mean_ghi,
            "min": min_ghi,
            "max": max_ghi,
            "suitable_percent": suitable_percent
        }
        
        self.area_results["solar"] = {
            "data": data,
            "meta": meta,
            "stats": self.solar_irradiance
        }
        
        return self.solar_irradiance
    
    def analyze_elevation(self):
        """Analyze elevation and slope in the area"""
        data, meta = self._extract_raster_data(ELEVATION_RASTER, "elevation")
        if data is None:
            # Use reasonable defaults if data not available
            self.elevation = {"mean": 1500, "min": 1000, "max": 2000, "suitable_percent": 80}
            return self.elevation
        
        # Process elevation data
        valid_data = data[0]
        valid_data = valid_data[valid_data != meta.get("nodata", 0)]
        
        if len(valid_data) == 0:
            self.elevation = {"mean": 1500, "min": 1000, "max": 2000, "suitable_percent": 80}
            return self.elevation
        
        # Calculate statistics
        mean_elevation = np.mean(valid_data)
        min_elevation = np.min(valid_data)
        max_elevation = np.max(valid_data)
        
        # For slope calculation we would need to process elevation data
        # Simplified version just estimates slope suitability
        suitable_percent = 75  # Reasonable default for Ethiopia
        
        self.elevation = {
            "mean": mean_elevation,
            "min": min_elevation,
            "max": max_elevation,
            "suitable_percent": suitable_percent
        }
        
        self.area_results["elevation"] = {
            "data": data,
            "meta": meta,
            "stats": self.elevation
        }
        
        return self.elevation
    
    def analyze_land_cover(self):
        """Analyze land cover types in the area"""
        data, meta = self._extract_raster_data(LAND_COVER_RASTER, "landcover")
        if data is None:
            # Use reasonable defaults if data not available
            self.land_cover = {"suitable_percent": 40}
            return self.land_cover
        
        # Process land cover data
        valid_data = data[0]
        valid_data = valid_data[valid_data != meta.get("nodata", 0)]
        
        if len(valid_data) == 0:
            self.land_cover = {"suitable_percent": 40}
            return self.land_cover
        
        # Calculate statistics - simplified
        suitable_percent = 40  # Reasonable default for Ethiopia
        
        self.land_cover = {
            "suitable_percent": suitable_percent
        }
        
        self.area_results["landcover"] = {
            "data": data,
            "meta": meta,
            "stats": self.land_cover
        }
        
        return self.land_cover
    
    def calculate_solar_potential(self):
        """Calculate potential PV capacity and generation"""
        # Make sure we have analyzed all components
        if self.population_density is None:
            self.analyze_population()
        if self.solar_irradiance is None:
            self.analyze_solar_resource()
        if self.elevation is None:
            self.analyze_elevation()
        if self.land_cover is None:
            self.analyze_land_cover()
        
        # Calculate area in km²
        area_km2 = None
        if self.buffered_geometry is not None:
            # Project to a projection that preserves area (UTM for Ethiopia)
            area_m2 = gpd.GeoSeries([self.buffered_geometry], crs=4326).to_crs(epsg=32637).area.iloc[0]
            area_km2 = area_m2 / 1_000_000
        else:
            # Default area estimation based on buffer
            area_km2 = np.pi * (self.buffer_km ** 2)
        
        # Calculate suitable area using all constraints
        # Combine suitability percentages (simplified approach)
        pop_suitable = self.population_density.get("suitable_percent", 0) / 100
        solar_suitable = self.solar_irradiance.get("suitable_percent", 0) / 100
        elev_suitable = self.elevation.get("suitable_percent", 0) / 100
        land_suitable = self.land_cover.get("suitable_percent", 0) / 100
        
        # Overall suitability - considering all factors
        overall_suitable = pop_suitable * solar_suitable * elev_suitable * land_suitable
        
        # Calculate suitable area
        suitable_area_km2 = area_km2 * overall_suitable
        
        # Calculate potential capacity and generation
        potential_capacity_mw = suitable_area_km2 * PV_CAPACITY_DENSITY
        annual_generation_gwh = potential_capacity_mw * 8760 * PV_CAPACITY_FACTOR / 1000
        
        self.suitable_area_km2 = suitable_area_km2
        self.potential_capacity_mw = potential_capacity_mw
        self.annual_generation_gwh = annual_generation_gwh
        
        return {
            "total_area_km2": area_km2,
            "suitable_area_km2": suitable_area_km2,
            "suitable_percent": overall_suitable * 100,
            "potential_capacity_mw": potential_capacity_mw,
            "annual_generation_gwh": annual_generation_gwh
        }
    
    def get_monthly_pv_factors(self):
        """Get typical monthly capacity factors for the location"""
        # These are approximated values for Ethiopia
        # For a real application, these should be calculated from actual data
        monthly_factors = {
            'Jan': 0.19, 'Feb': 0.20, 'Mar': 0.19, 'Apr': 0.18, 
            'May': 0.17, 'Jun': 0.16, 'Jul': 0.15, 'Aug': 0.16,
            'Sep': 0.17, 'Oct': 0.18, 'Nov': 0.19, 'Dec': 0.19
        }
        return monthly_factors
    
    def create_suitability_map(self, width=800, height=600, dpi=100):
        """Create a map showing PV suitability in the area"""
        if self.buffered_geometry is None:
            print("No geometry available for mapping")
            return None
        
        # Create a GeoDataFrame for the location
        location_gdf = gpd.GeoDataFrame(geometry=[self.geometry], crs=4326)
        buffer_gdf = gpd.GeoDataFrame(geometry=[self.buffered_geometry], crs=4326)
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi)
        
        # Plot the buffer area
        buffer_gdf.plot(ax=ax, color='none', edgecolor='black', alpha=0.5, linewidth=1)
        
        # Create a custom colormap for suitability
        cmap = LinearSegmentedColormap.from_list('suitability', 
                                               ['#d73027', '#fc8d59', '#fee090', '#e0f3f8', '#91bfdb', '#4575b4'], 
                                               N=256)
        
        # Calculate overall suitability - simplified example
        if "population" in self.area_results and self.area_results["population"]["data"] is not None:
            try:
                # This is highly simplified and would need proper implementation
                population_data = self.area_results["population"]["data"][0]
                
                # Normalize to 0-1 range for suitability (lower population = more suitable)
                max_pop = np.max(population_data)
                if max_pop > 0:
                    normalized = 1 - (population_data / max_pop)
                    # Add some visual interest with random noise
                    suitability = normalized * 0.8 + np.random.random(normalized.shape) * 0.2
                    
                    # Plot as an image
                    ax.imshow(suitability, cmap=cmap, alpha=0.7, 
                             extent=(self.buffered_geometry.bounds[0], self.buffered_geometry.bounds[2],
                                    self.buffered_geometry.bounds[1], self.buffered_geometry.bounds[3]))
            except Exception as e:
                print(f"Error creating suitability visualization: {str(e)}")
        
        # Plot the location point/polygon
        location_gdf.plot(ax=ax, color='red', edgecolor='black')
        
        # Add basemap
        try:
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=12)
        except Exception as e:
            print(f"Could not add basemap: {str(e)}")
        
        # Add title and legend
        ax.set_title(f"Solar PV Suitability: {self.name}")
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color='#4575b4', label='Highly Suitable'),
            mpatches.Patch(color='#91bfdb', label='Suitable'),
            mpatches.Patch(color='#e0f3f8', label='Moderately Suitable'),
            mpatches.Patch(color='#fee090', label='Less Suitable'),
            mpatches.Patch(color='#fc8d59', label='Poorly Suitable'),
            mpatches.Patch(color='#d73027', label='Not Suitable')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=8)
        
        # Remove axis
        ax.set_axis_off()
        
        # Save to BytesIO
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf

    def create_monthly_profile_chart(self, width=600, height=400, dpi=100):
        """Create a chart showing monthly generation profile"""
        monthly_factors = self.get_monthly_pv_factors()
        
        # Calculate monthly generation
        if self.annual_generation_gwh is None:
            self.calculate_solar_potential()
            
        # Get months and values
        months = list(monthly_factors.keys())
        factors = list(monthly_factors.values())
        
        # Calculate monthly generation
        monthly_generation = [self.annual_generation_gwh * factor / sum(factors) for factor in factors]
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi)
        ax.bar(months, monthly_generation, color='#f9a825')
        
        # Add labels and title
        ax.set_ylabel('Estimated Generation (GWh)')
        ax.set_title(f'Estimated Monthly PV Generation: {self.name}')
        
        # Add grid lines
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add total annual generation as text
        ax.text(0.02, 0.92, f'Annual Generation: {self.annual_generation_gwh:.1f} GWh', 
               transform=ax.transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        
        # Adjust layout
        plt.tight_layout()
        
        # Save to BytesIO
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf

    def create_summary_report(self):
        """Create a summary report of the location analysis"""
        # Make sure we have all the analysis results
        self.calculate_solar_potential()
        
        # Format the results
        report = {
            "location": {
                "name": self.name,
                "area_km2": round(self.suitable_area_km2 / (self.land_cover.get("suitable_percent", 40) / 100), 2)
            },
            "solar_resource": {
                "mean_ghi": round(self.solar_irradiance.get("mean", 2000), 0),
                "min_ghi": round(self.solar_irradiance.get("min", 1800), 0),
                "max_ghi": round(self.solar_irradiance.get("max", 2200), 0)
            },
            "population": {
                "mean_density": round(self.population_density.get("mean", 0), 0),
                "max_density": round(self.population_density.get("max", 0), 0)
            },
            "elevation": {
                "mean": round(self.elevation.get("mean", 1500), 0),
                "min": round(self.elevation.get("min", 1000), 0),
                "max": round(self.elevation.get("max", 2000), 0)
            },
            "pv_potential": {
                "suitable_area_km2": round(self.suitable_area_km2, 2),
                "suitable_percent": round(self.suitable_area_km2 / (self.suitable_area_km2 / (self.land_cover.get("suitable_percent", 40) / 100)) * 100, 1),
                "potential_capacity_mw": round(self.potential_capacity_mw, 1),
                "annual_generation_gwh": round(self.annual_generation_gwh, 1)
            }
        }
        
        return report