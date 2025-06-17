function openFileDialog() {
      try {
          var file = File.openDialog("Select an image", "*.jpg;*.png", false);
          if (file) {
              return file.fsName;
          } else {
              $.writeln("No file selected in openFileDialog");
              return null;
          }
      } catch (e) {
          $.writeln("Error in openFileDialog: " + e.toString());
          return null;
      }
  }

  function saveFileDialog() {
      try {
          var file = File.saveDialog("Save processed image", "no_bg_output.png");
          if (file) {
              return file.fsName;
          } else {
              $.writeln("No file path selected in saveFileDialog");
              return null;
          }
      } catch (e) {
          $.writeln("Error in saveFileDialog: " + e.toString());
          return null;
      }
  }

  function readImageAsBase64(filePath) {
      $.writeln("Starting readImageAsBase64 for: " + filePath);
      var file = new File(filePath);
      if (file.exists) {
          $.writeln("File exists: " + file.fsName);
          file.open('r');
          $.writeln("File opened for reading");
          var content = "";
          try {
              while (!file.eof) {
                  content += file.read(1024); // Read in 1KB chunks
              }
              $.writeln("Content read, total length: " + content.length);
              file.close();
              $.writeln("File closed");
              if (content.length > 0) {
                  var base64Prefix = "data:image/png;base64,";
                  try {
                      var base64String = $.toBase64(content);
                      $.writeln("Base64 conversion successful, length: " + base64String.length);
                      return base64Prefix + base64String;
                  } catch (e) {
                      $.writeln("Base64 conversion failed: " + e.toString());
                      return null;
                  }
              } else {
                  $.writeln("No content read");
                  return null;
              }
          } catch (e) {
              $.writeln("Error reading file: " + e.toString());
              file.close();
              return null;
          }
      } else {
          $.writeln("File does not exist: " + filePath);
          return null;
      }
  }