#target premierepro

// Debug: Check environment
alert("Script started. App available: " + (app ? "Yes" : "No"));
if (!app || !app.project) {
    alert("Premiere Pro is not running or not targeted correctly.");
} else {
    alert("Current Project: " + app.project.name);
    alert("BridgeTalk version: " + BridgeTalk.version); // Check BridgeTalk, used by ScriptUI
    alert("ScriptUI available: " + (typeof Window !== "undefined" ? "Yes" : "No"));

    // Attempt to create UI
    if (typeof Window !== "undefined") {
        try {
            var win = new Window("dialog", "Test Panel");
            var btn = win.add("button", undefined, "Click Me");
            btn.onClick = function() {
                alert("Button clicked!");
            };
            win.show();
        } catch (e) {
            alert("Error creating dialog: " + e.message);
        }
    } else {
        alert("ScriptUI is not available. Cannot create UI.");
    }
}