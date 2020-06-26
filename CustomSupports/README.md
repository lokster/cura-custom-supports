# Custom Supports plugin for Cura

Cura plugin which enables you to add custom supports!
It is based on the SupportEraser plugin.
The initial version was tested on Cura 3.3 and 3.4
More information can be found on http://lokspace.eu/cura-custom-supports-plugin/

Installation
----
First, make sure your Cura version is 3.3 or newer
There are two ways to install the plugin - manual and automatic

**Automatic Install**
Go to the releases page, and download the correct file for your Cura version - the .curaplugin file for Cura 3.3.x and the .curapackage file for Cura 3.4 and newer.
Start Cura, and drag & drop the file on the main window. Restart Cura, and you are done!

**Manual Install**
Download & extract the repository as ZIP or clone it. Copy the files/plugins/CustomSupports directory to:
- on Windows: [Cura installation folder]/plugins/CustomSupports
- on Linux: ~/.local/share/cura/[YOUR CURA VERSION]/plugins/CustomSupports (e.g. ~/.local/share/cura/3.4/plugins/CustomSupports)
- on Mac: ~/Library/Application Support/cura/[YOUR CURA VERSION]/plugins/CustomSupports


How to use
----
- Load some model in Cura and select it
- Uncheck the "Generate Support" checkbox in the right panel (if you want to use ONLY custom supports)
- click on the "Custom Supports" button on the left toolbar
- click anywhere on the model to place support block there
- clicking existing support block deletes it
Note: it's easier to add/remove supports when you are in "Solid View" mode

You can see the plugin in action here: https://www.youtube.com/watch?v=bMZLVWhbPEU
