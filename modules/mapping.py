# -*- coding: utf-8 -*-
"""
Created on Sat Mar 15 16:42:40 2025

@author: kumab
"""
import hashlib


import geopandas as gpd
import folium
from folium.plugins import Draw, MeasureControl, MousePosition
import osmnx as ox
import os

# Get the absolute path to the project directory
current_dir = os.path.dirname(os.path.abspath(__file__))  # modules directory
project_dir = os.path.dirname(current_dir)  # main project directory

# Create necessary directories
os.makedirs(os.path.join(project_dir, "maps"), exist_ok=True)

# Load the shapefile of Ethiopia's woredas
SHAPEFILE = os.path.join(project_dir, "data", "shapefiles", "eth_admbnda_adm3_csa_bofedb_2021.shp")

try:
    woredas = gpd.read_file(SHAPEFILE)
    # Extract town names for dropdown selection
    town_list = sorted(woredas["ADM3_EN"].unique())
except Exception as e:
    print(f"Error loading shapefile: {str(e)}")
    # Provide a minimal fallback list for testing
    woredas = None
    town_list = ["Addis Ababa", "Bahir Dar", "Hawassa", "Mekelle", "Dire Dawa"]

# Function to create interactive map for roof selection
def create_town_map(selected_town):
    """
    Create interactive map for the selected town with multiple free satellite imagery options
    
    Parameters:
    -----------
    selected_town : str
        Name of the town to create map for
        
    Returns:
    --------
    tuple
        (map object, latitude, longitude, buildings or None)
    """
    # Check if woredas data is available
    if woredas is None:
        print(f"Warning: Shapefile data not available. Using fallback coordinates for {selected_town}")
        # Fallback coordinates (approximate center of Ethiopia)
        lat, lon = 9.0, 38.0
        
        # Create base map with OpenStreetMap
        m = folium.Map(location=[lat, lon], zoom_start=5, tiles=None)  # Start with no tiles
        
        # Add standard OpenStreetMap
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False
        ).add_to(m)
        
        # Add ESRI World Imagery
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='ESRI Satellite',
            overlay=False,
            max_zoom=19
        ).add_to(m)
        
        # Add Google-style satellite map
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google earth Satellite',
            overlay=False,
            max_zoom=20
        ).add_to(m)
        
        # Add Humanitarian OpenStreetMap (sometimes has better coverage in developing regions)
        folium.TileLayer(
            tiles='https://tile-{s}.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            attr='Humanitarian OpenStreetMap Team',
            name='Humanitarian OSM',
            overlay=False
        ).add_to(m)
        
        # Add ESRI World Imagery with labels
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='ESRI Satellite',
            overlay=False
        ).add_to(m)
        
        # Add Terrain map (shows elevation)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Terrain',
            overlay=False,
        ).add_to(m)
        
        # Add Sentinel-2 cloudless 2020 (may have good coverage of Ethiopia)
        folium.TileLayer(
            tiles='https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
            attr='EOX - Sentinel-2 cloudless',
            name='Sentinel-2 (2020)',
            overlay=False,
            max_zoom=16
        ).add_to(m)
        
        # Add Sentinel-2 cloudless 2022 (newer but might have more clouds)
        folium.TileLayer(
            tiles='https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2022_3857/default/g/{z}/{y}/{x}.jpg',
            attr='EOX - Sentinel-2 cloudless',
            name='Sentinel-2 (2022)',
            overlay=False,
            max_zoom=16
        ).add_to(m)
        
        # Add OpenTopoMap for terrain visualization
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='OpenTopoMap',
            name='Topographic Map',
            overlay=False
        ).add_to(m)
        
        # Add a marker for the town center
        folium.Marker(
            [lat, lon],
            popup=f"{selected_town} (approximate)",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        # Add drawing tools for manual roof selection
        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': False,
                'marker': True,  # Allow markers for points of reference
                'circlemarker': False
            },
            edit_options={'edit': True, 'remove': True}  # Allow editing and removing shapes
        )
        m.add_child(draw)
        
        # Add measurement tool
        m.add_child(MeasureControl(position='topleft', primary_length_unit='meters', secondary_length_unit='kilometers'))
        
        # Add mouse position display with coordinates and zoom level
        formatter = "function(num) {return L.Util.formatNum(num, 6) + ' / Zoom: ' + map.getZoom();};"
        MousePosition(
            position='bottomright',
            separator=' | ',
            empty_string='',
            lng_first=True,
            num_digits=6,
            prefix='',
            lat_formatter=formatter,
            lng_formatter=formatter
        ).add_to(m)
        
        # Add layer control to switch between map types
        folium.LayerControl(position='topright').add_to(m)
        
        # Add instructions for users
        title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 120px; width: 320px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 8px;">
           <b>Instructions:</b><br>
           1. Switch between map types using the control in top right<br>
           2. Try different satellite layers for best imagery<br>
           3. Use the draw tools to outline your roof<br>
           4. Measure area using the ruler tool<br>
           5. Current zoom level shows at bottom right
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save the map
        map_filename = os.path.join(project_dir, "maps", f"{selected_town.replace(' ', '_')}.html")
        m.save(map_filename)
        print(f"Map saved to {map_filename}")
        
        return m, lat, lon, None
    
    # Find the woreda entry for the selected town
    town_data = woredas[woredas["ADM3_EN"] == selected_town]
    
    if town_data.empty:
        print(f"Town '{selected_town}' not found in shapefile")
        return None
    
    # Project to a projected CRS suitable for Ethiopia (UTM zone 37N)
    town_data_projected = town_data.to_crs(epsg=32637)
    
    # Get the centroid of the town's geometry
    town_centroid_projected = town_data_projected.geometry.centroid.iloc[0]
    
    # Convert centroid back to WGS84 for mapping
    town_centroid = gpd.GeoSeries([town_centroid_projected], crs=32637).to_crs(4326).iloc[0]
    lat, lon = town_centroid.y, town_centroid.x
    
    # Create a map centered on the town with no initial base layer
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles=None)  # Start with no tiles
    
    # Add standard OpenStreetMap
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False
    ).add_to(m)
    
    # Add ESRI World Imagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='ESRI Satellite',
        overlay=False,
        max_zoom=19
    ).add_to(m)
    
    # Add Google-style satellite map
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google-style Satellite',
        overlay=False,
        max_zoom=20
    ).add_to(m)
    
    # Add Humanitarian OpenStreetMap (sometimes has better coverage in developing regions)
    folium.TileLayer(
        tiles='https://tile-{s}.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attr='Humanitarian OpenStreetMap Team',
        name='Humanitarian OSM',
        overlay=False
    ).add_to(m)
    
    # Add Terrain map (shows elevation)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Terrain',
        overlay=False,
    ).add_to(m)
    
    # Add Sentinel-2 cloudless 2020 (may have good coverage of Ethiopia)
    folium.TileLayer(
        tiles='https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
        attr='EOX - Sentinel-2 cloudless',
        name='Sentinel-2 (2020)',
        overlay=False,
        max_zoom=16
    ).add_to(m)
    
    # Add Sentinel-2 cloudless 2022 (newer but might have more clouds)
    folium.TileLayer(
        tiles='https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2022_3857/default/g/{z}/{y}/{x}.jpg',
        attr='EOX - Sentinel-2 cloudless',
        name='Sentinel-2 (2022)',
        overlay=False,
        max_zoom=16
    ).add_to(m)
    
    # Add OpenTopoMap for terrain visualization
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap',
        name='Topographic Map',
        overlay=False
    ).add_to(m)
    
    # Add the town boundary
    folium.GeoJson(
        town_data.geometry.iloc[0],
        name="Town Boundary",
        style_function=lambda x: {"fillColor": "transparent", "color": "blue", "weight": 2}
    ).add_to(m)
    
    # Try to get buildings
    buildings_found = False
    try:
        distance = 1500  # meters radius
        tags = {"building": True}
        town_buildings = ox.features.features_from_point((lat, lon), tags, dist=distance)
        
        # Add buildings to the map if any were found
        if not town_buildings.empty:
            buildings_found = True
            
            # Create a unique function for each building to enable selection
            def style_function(feature):
                return {
                    "fillColor": "#ff7800",
                    "color": "#555555",
                    "weight": 1,
                    "fillOpacity": 0.7
                }
            
            # Add GeoJson with clickable buildings
            building_layer = folium.GeoJson(
                town_buildings,
                name="Buildings",
                style_function=style_function,
                highlight_function=lambda x: {"fillColor": "#ffaf00", "color": "#000000", "weight": 3, "fillOpacity": 0.9},
                tooltip=folium.GeoJsonTooltip(fields=["building"], labels=True, sticky=True)
            ).add_to(m)
            
            print(f"Added {len(town_buildings)} buildings to the map")
    except Exception as e:
        print(f"Error getting buildings for {selected_town}: {str(e)}")
        buildings_found = False
    
    # Always add drawing tools, even if buildings are found, for manual roof selection
    draw = Draw(
        draw_options={
            'polyline': False,
            'rectangle': True,
            'polygon': True,
            'circle': False,
            'marker': True,  # Allow markers for points of reference
            'circlemarker': False
        },
        edit_options={'edit': True, 'remove': True}  # Allow editing and removing shapes
    )
    m.add_child(draw)
    
    # Add measurement tool
    m.add_child(MeasureControl(position='topleft', primary_length_unit='meters', secondary_length_unit='kilometers'))
    
    # Add mouse position display with coordinates and zoom level
    formatter = "function(num) {return L.Util.formatNum(num, 6) + ' / Zoom: ' + map.getZoom();};"
    MousePosition(
        position='bottomright',
        separator=' | ',
        empty_string='',
        lng_first=True,
        num_digits=6,
        prefix='',
        lat_formatter=formatter,
        lng_formatter=formatter
    ).add_to(m)
    
    # Add a marker for the town center
    folium.Marker(
        [lat, lon],
        popup=f"{selected_town} (center)",
        icon=folium.Icon(color="green", icon="info-sign")
    ).add_to(m)
    
    # Add instructions for users
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 120px; width: 320px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 8px;">
       <b>Instructions:</b><br>
       1. Switch between map types using the control in top right<br>
       2. Try different satellite layers for best imagery<br>
       3. Use the draw tools to outline your roof<br>
       4. Measure area using the ruler tool<br>
       5. Current zoom level shows at bottom right
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl(position='topright').add_to(m)
    
    # Save the map
    map_filename = os.path.join(project_dir, "maps", f"{selected_town.replace(' ', '_')}.html")
    m.save(map_filename)
    print(f"Map saved to {map_filename}")
    
    return m, lat, lon, town_buildings if buildings_found else None