# Fusion360_3_axis_milling_automation

This 3 axis milling automation has two scripts

1.setup_toolpath.py will add and load the template of toolpaths.
2.Posting.py will post the NC files of the toolpaths.

In order to use this scripts, you need to first create a template of toolpaths. A template can contain one or more toolpaths. Store the template in your local computer and copy the filepath of template.
Paste the file path in the setup_toolpath.py script for the variable TEMPLATE_FILENAME. Save the script.

You are good to run the 1.setup_toolpath.py. After running it will generate a setup and toolpath as there in the template. Check whether all parameters are ok.
If everything is ok then run the Posting.py, then it will post the toolpaths.
