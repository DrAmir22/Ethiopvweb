// File: custom_components/roof_selector/index.js

// Define the Streamlit component
const RoofSelector = {
  render: function(container, props) {
    // Create a simple interface for testing
    container.innerHTML = `
      <div style="padding: 20px; border: 1px solid #ccc; margin-bottom: 20px;">
        <h3>Roof Selector Component</h3>
        <p>This is a simplified version for testing.</p>
        <p>Latitude: ${props.lat}, Longitude: ${props.lon}</p>
        <p>To simulate selection, click the button below:</p>
        <button id="select-roof" style="background-color: #ff4b4b; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">
          Simulate Roof Selection
        </button>
      </div>
    `;
    
    // Add click event to the button
    document.getElementById('select-roof').addEventListener('click', function() {
      // Return simulated roof data
      Streamlit.setComponentValue({
        area: 100,
        orientation: 180,
        coordinates: [
          [props.lat - 0.0005, props.lon - 0.0005],
          [props.lat - 0.0005, props.lon + 0.0005],
          [props.lat + 0.0005, props.lon + 0.0005],
          [props.lat + 0.0005, props.lon - 0.0005]
        ]
      });
    });
  }
};

// Register the component
Streamlit.registerComponentInstance(RoofSelector);