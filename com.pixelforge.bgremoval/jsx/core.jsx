function openFileDialog() {
        var file = File.openDialog("Select an image", "*.jpg;*.png", false);
        if (file) {
            return file.fsName;
        } else {
            return null;
        }
    }