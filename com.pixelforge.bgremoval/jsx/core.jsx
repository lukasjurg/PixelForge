function openFileDialog() {
      try {
          var file = File.openDialog("Select an image", "*.jpg;*.png", false);
          if (file) {
              $.writeln("Selected file: " + file.fsName);
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

  // Commented out for now, as preview is removed
  /*
  function readImageAsBase64(filePath) {
      $.writeln("Starting readImageAsBase64 for: " + filePath);
      var file = new File(filePath);
      if (file.exists) {
          try {
              file.open('r');
              var content = file.read();
              $.writeln("File content length: " + (content ? content.length : 0));
              file.close();
              if (content && content.length > 0) {
                  try {
                      var base64String = $.toBase64(content);
                      $.writeln("Base64 conversion result length: " + (base64String ? base64String.length : 0));
                      return "data:image/png;base64," + base64String;
                  } catch (e) {
                      $.writeln("Base64 conversion error: " + e.toString());
                      return null;
                  }
              } else {
                  $.writeln("No content read from file");
                  return null;
              }
          } catch (e) {
              $.writeln("File read error: " + e.toString());
              if (file) file.close();
              return null;
          }
      } else {
          $.writeln("File does not exist: " + filePath);
          return null;
      }
  }
  */