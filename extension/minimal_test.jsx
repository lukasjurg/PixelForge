#target premierepro

if (typeof Window !== "undefined") {
    var win = new Window("dialog", "Minimal Test");
    win.show();
} else {
    alert("ScriptUI is not available.");
}