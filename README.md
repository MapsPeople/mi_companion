# MI Companion


[![pipeline status](https://git.rtx.mapspeople.com/MapsIndoors/automation/gds-tools/gds_companion/badges/develop/pipeline.svg)](https://git.rtx.mapspeople.com/MapsIndoors/automation/gds-tools/gds_companion/-/commits/develop)



        <li>If resources.py is not present in your plugin directory, compile the resources file using pyrcc5
            (simply use <b>pb_tool</b> or <b>make</b> if you have automake)
        <li>Optionally, test the generated sources using <b>make test</b> (or run tests from your IDE)
        <li>Copy the entire directory containing your new plugin to the QGIS plugin directory (see Notes below)
        <li>Test the plugin by enabling it in the QGIS plugin manager
        <li>Customize it by editing the implementation file <b>ProfileCreator.py</b>
        <li>Create your own custom icon, replacing the default <b>icon.png</b>
        <li>Modify your user interface by opening <b>ProfileCreator_dialog_base.ui</b> in Qt Designer
    </ol>
    Notes:
    <ul>
        <li>You can use <b>pb_tool</b> to compile, deploy, and manage your plugin. Tweak the <i>pb_tool.cfg</i>
            file included with your plugin as you add files. Install <b>pb_tool</b> using
            <i>pip</i> or <i>easy_install</i>. See <b>http://loc8.cc/pb_tool</b> for more information.
        <li>You can also use the <b>Makefile</b> to compile and deploy when you
            make changes. This requires GNU make (gmake). The Makefile is ready to use, however you
            will have to edit it to add addional Python source files, dialogs, and translations.
