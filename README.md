# MI Companion

This plugin is an editor for MI-based data, it provides a direct view into what currently resides in the MI
Database and thus lets you modify and extend it with ease.

### How to setup python interpreter in pycharm

1. Build mi_companion_bundle and install. Run `bundle_packaging.py` to build the mi_companion_bundle. Run
   `dev_install_plugin.py` to install the plugin.
2. Open QGIS and open the Python console. Run

```
import sys
sys.executable
sys.path
 ```

3. Create a new virtual environment interpreter in Pycharm using the path output from `sys.executable` as your
   base interpreter.
   If you're on MacOS you might get the path to the QGIS executable instead, then insert the path to your
   system interpreter as your base interpreter.
4. Click the interpreter paths button when highlighting your newly create interpreter.
   ![interpreter_paths_button.png](images/interpreter_paths_button.png)
5. Add all the different paths in the output from `sys.path` to your interpreter.
   There can be duplicates in the output, but you only have to add the once.
   ![intepreter_paths_window.png](images/intepreter_paths_window.png)
7. Now you should be able to run the code and tests!
