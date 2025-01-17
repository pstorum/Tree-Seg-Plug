# Tree Segementation of Aerial Point Clouds

The purpose of this QGIS plugin is to parse a LiDAR(.las or .laz) scan of a forested area. After providing our plugin with a scan, we return information about the forest as well as a segmented shape files of the crowns and peaks found in the forest.

# Build Status

1. Data become less and less acurate the larger the given file gets. We think its a problem with the parsing algorithm (/Trex/capi) and (/Trex/python)<br>
2. The original program which can run on its own, seems to conflict with the plugin build, requiring an initial manual dependency setup (see below). original program is located in /Trex/<br><br>
            a. The original build is run through a command prompt which needs a conda environment to run. The current fix is that we activate the conda environment and dump the enviroment information to a json, then move the json to the current working dirrectory of the plugin.<br>  
            `/Trex/scripts/qgis_setup_env.py`<br>
            `/Trex/scripts/env_qgis_setup.cmd`<br><br>
      b. This has to be done before the program launchs because we need the enviroment dump to be done while the conda env is active. The first lines in tree_seg.py in __init__ of TreeSeg class will then use the env_vars.json to create the env for the plugin to run
      
            Possible Solutions
            1. Bundle all dependency libraries with code directly
            2. Package all of /Trex/ into an executable, that the plugin runs when it needs access

# Installation

<h3> Download and Install:</h3>

[QGIS](https://www.qgis.org/en/site/)

[Anaconda](https://www.anaconda.com/)

Download our plugin as .zip

1. After installing Anaconda be sure to set system environment variables.

    (path to installation)\anaconda3

    (path to installation)\anaconda3\Scripts

    (path to installation)\anaconda3\Library\bin



2. Open QGIS, and on the top bar navigate to Plugins --> Manage and Install

3. Install from Zip

4. Then navigate to the Installed tab and check off Tree Segmentation

5. Restart QGIS

6. You are ready to begin using the plugin.

(Note: currently there is some conflict with automated dependency setup, and some extra steps are needed to get the plugin running. See below for instructions to manually get dependencies working)

# Using the plugin

1. Open QGIS (Note: If you get a write error, you may have to run the program as admin)
2. Open the plugin
3. Select a .las or .laz file to start segmenting.
4. Set your parameters and press start segmentation.
5. Depending on the size of the LiDAR file used, computation time will vary.
6. Save the data a Shape file for direct use within QGIS.


# Manual Dependency Setup
1. Open a command prompt
2. Change directory to the install location of QGIS, and navigate to the following folder "QGIS\QGIS3\profiles\default\python\plugins\Tree-Seg-Plug\TrEx\scripts"
3. Run "env_setup" and enter yes when prompted to.
4. Run "env_activate"
5. Run "env_qgis_setup"
6. A new file should be created called "env_vars.json"
7. Move that file to the main working directory of the plugin. "/Tree-Seg_Plug"

# Credits
Junsu Lee - leejuns@oregonstate.edu<br>
Kaiyuan Liu - liukaiy@oregonstate.edu<br>
Peter Storum - storump@oregonstate.edu<br>

(Note: Feel free to contact for assistance up to the end of 2023)
