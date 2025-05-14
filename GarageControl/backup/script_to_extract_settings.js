// Script to extract and display complete device settings from localStorage
// This can be copy-pasted into the browser console on the garage monitor page

function displayDeviceRanges() {
  console.log("===== DEVICE SETTINGS WITH RANGES =====");
  
  // Get all keys from localStorage that contain device settings
  const settingsKeys = Object.keys(localStorage).filter(key => key.startsWith('device_settings_'));
  
  if (settingsKeys.length === 0) {
    console.log("No device settings found in localStorage.");
    console.log("Please visit the main page and let the settings load first.");
    return;
  }
  
  console.log(`Found settings for ${settingsKeys.length} devices in localStorage`);
  
  // Process each device's settings
  settingsKeys.forEach(key => {
    try {
      const deviceId = key.replace('device_settings_', '');
      const settings = JSON.parse(localStorage.getItem(key));
      
      console.log("\n" + "=".repeat(50));
      console.log(`Device ID: ${deviceId}`);
      console.log("-".repeat(50));
      
      // Temperature Settings
      console.log("Temperature Control:");
      console.log(`  Enabled: ${settings.temp_control_enabled}`);
      console.log(`  Source: ${settings.temp_source}`);
      console.log(`  Range: ${settings.target_temp_min}°F - ${settings.target_temp_max}°F`);
      console.log(`  Function: ${settings.temp_range_type === 'inside' ? 'Turn ON when inside range' : 'Turn ON when outside range'}`);
      
      // Humidity Settings
      console.log("Humidity Control:");
      console.log(`  Enabled: ${settings.humidity_control_enabled}`);
      console.log(`  Source: ${settings.humidity_source}`);
      console.log(`  Range: ${settings.target_humidity_min}% - ${settings.target_humidity_max}%`);
      console.log(`  Function: ${settings.humidity_range_type === 'inside' ? 'Turn ON when inside range' : 'Turn ON when outside range'}`);
      
      // Database representation (for reference)
      console.log("\nStored in Database as:");
      console.log(`  Temperature: ${settings.target_temp}°F, Function: ${settings.temp_function}`);
      console.log(`  Humidity: ${settings.target_humidity}%, Function: ${settings.humidity_function}`);
      
      console.log("=".repeat(50));
    } catch (error) {
      console.error(`Error processing device settings: ${error}`);
    }
  });
}

// Create a button in the UI to show settings
function addSettingsDisplayButton() {
  // Check if button already exists
  if (document.getElementById('show-ranges-btn')) {
    return;
  }
  
  // Find the reload settings button to place our button next to it
  const reloadBtn = document.getElementById('reload-settings-btn');
  
  if (reloadBtn && reloadBtn.parentElement) {
    // Create our button
    const showRangesBtn = document.createElement('button');
    showRangesBtn.id = 'show-ranges-btn';
    showRangesBtn.className = 'bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 ml-2';
    showRangesBtn.innerText = '👁️ View Full Ranges';
    
    // Add click handler
    showRangesBtn.addEventListener('click', function() {
      // Create a pop-up to display settings
      const settingsDiv = document.createElement('div');
      settingsDiv.style.position = 'fixed';
      settingsDiv.style.top = '50%';
      settingsDiv.style.left = '50%';
      settingsDiv.style.transform = 'translate(-50%, -50%)';
      settingsDiv.style.backgroundColor = 'white';
      settingsDiv.style.padding = '20px';
      settingsDiv.style.borderRadius = '8px';
      settingsDiv.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
      settingsDiv.style.zIndex = '1000';
      settingsDiv.style.maxHeight = '80vh';
      settingsDiv.style.overflow = 'auto';
      settingsDiv.style.width = '80%';
      settingsDiv.style.maxWidth = '600px';
      
      // Add a close button
      const closeBtn = document.createElement('button');
      closeBtn.innerText = '✕';
      closeBtn.style.position = 'absolute';
      closeBtn.style.top = '10px';
      closeBtn.style.right = '10px';
      closeBtn.style.background = 'none';
      closeBtn.style.border = 'none';
      closeBtn.style.cursor = 'pointer';
      closeBtn.style.fontSize = '20px';
      closeBtn.addEventListener('click', () => settingsDiv.remove());
      
      // Add a title
      const title = document.createElement('h2');
      title.innerText = 'Complete Device Settings';
      title.style.fontSize = '18px';
      title.style.fontWeight = 'bold';
      title.style.marginBottom = '15px';
      
      // Get the settings content
      const content = document.createElement('div');
      content.style.fontFamily = 'monospace';
      content.style.whiteSpace = 'pre-wrap';
      content.style.fontSize = '14px';
      
      // Process each device's settings
      const settingsKeys = Object.keys(localStorage).filter(key => key.startsWith('device_settings_'));
      
      if (settingsKeys.length === 0) {
        content.innerText = "No device settings found in localStorage.\nPlease reload the page to load settings.";
      } else {
        let settingsText = `Found settings for ${settingsKeys.length} devices\n\n`;
        
        // Process each device's settings
        settingsKeys.forEach(key => {
          try {
            const deviceId = key.replace('device_settings_', '');
            const settings = JSON.parse(localStorage.getItem(key));
            
            settingsText += "=".repeat(40) + "\n";
            settingsText += `Device ID: ${deviceId}\n`;
            settingsText += "-".repeat(40) + "\n";
            
            // Temperature Settings
            settingsText += "Temperature Control:\n";
            settingsText += `  Enabled: ${settings.temp_control_enabled}\n`;
            settingsText += `  Source: ${settings.temp_source}\n`;
            settingsText += `  Range: ${settings.target_temp_min}°F - ${settings.target_temp_max}°F\n`;
            settingsText += `  Function: ${settings.temp_range_type === 'inside' ? 'Turn ON when inside range' : 'Turn ON when outside range'}\n`;
            
            // Humidity Settings
            settingsText += "\nHumidity Control:\n";
            settingsText += `  Enabled: ${settings.humidity_control_enabled}\n`;
            settingsText += `  Source: ${settings.humidity_source}\n`;
            settingsText += `  Range: ${settings.target_humidity_min}% - ${settings.target_humidity_max}%\n`;
            settingsText += `  Function: ${settings.humidity_range_type === 'inside' ? 'Turn ON when inside range' : 'Turn ON when outside range'}\n`;
            
            settingsText += "=".repeat(40) + "\n\n";
          } catch (error) {
            settingsText += `Error processing device settings: ${error}\n`;
          }
        });
        
        content.innerText = settingsText;
      }
      
      // Add components to the pop-up
      settingsDiv.appendChild(closeBtn);
      settingsDiv.appendChild(title);
      settingsDiv.appendChild(content);
      
      // Add the pop-up to the document
      document.body.appendChild(settingsDiv);
    });
    
    // Add our button next to the reload button
    reloadBtn.parentElement.appendChild(showRangesBtn);
  }
}

// Run the functions
displayDeviceRanges();
addSettingsDisplayButton();

// Instructions for the user
console.log("\nTo view settings again, call displayDeviceRanges()");
console.log("A button '👁️ View Full Ranges' has been added next to the 'Reload Saved Settings' button"); 