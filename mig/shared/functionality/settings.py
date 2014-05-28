#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# settings - back end for the settings page
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
#
# This file is part of MiG.
#
# MiG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MiG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#

import os

import shared.returnvalues as returnvalues
from shared.base import client_alias, client_id_dir
from shared.defaults import any_vgrid, default_mrsl_filename, \
     default_css_filename, profile_img_max_kb, profile_img_extensions
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry, extract_menu
from shared.settings import load_settings, load_widgets, load_profile, \
     load_ssh, load_davs, load_ftps
from shared.profilekeywords import get_profile_specs
from shared.safeinput import html_escape
from shared.settingskeywords import get_settings_specs
from shared.widgetskeywords import get_widgets_specs
from shared.useradm import get_default_mrsl, get_default_css
from shared.vgrid import vgrid_list_vgrids

try:
    import shared.arcwrapper as arc
except Exception, exc:
    # Ignore errors and let it crash if ARC is enabled without the lib
    pass


cm_prefix = '/images/lib/codemirror'
cm_css_prefix = '%s/lib' % cm_prefix
cm_js_prefix = '%s/lib' % cm_prefix
cm_addon_prefix = '%s/addon' % cm_prefix
cm_mode_prefix = '%s/mode' % cm_prefix
edit_defaults = {'matchBrackets': "true", 'indentUnit': 4}
general_edit = edit_defaults.copy()
ssh_edit = edit_defaults.copy()
davs_edit = edit_defaults.copy()
ftps_edit = edit_defaults.copy()
style_edit = edit_defaults.copy()
style_edit['mode'] = 'css'
widgets_edit = edit_defaults.copy()
widgets_edit['mode'] = 'htmlmixed'
profile_edit = edit_defaults.copy()
profile_edit['mode'] = 'htmlmixed'


def py_to_js(options):
    """Format python dictionary as dictionary string used in javascript"""

    out = []
    for (key, val) in options.items():
        if isinstance(val, basestring):
            val = '"%s"' % val
        out.append('%s: %s' % (key, val))
    return '{%s}' % ', '.join(out)

def wrap_edit_area(name, area, edit_opts=edit_defaults, toolbar_buttons='ALL'):
    """Wrap HTML textarea in user friendly editor with syntax highlighting
    and optional basic toolbar.
    """
    init_buttons = ''
    button_impl = ''
    if toolbar_buttons:
        # TODO: switch to python generated html with icon buttons!
        init_buttons = '''  
  this.spellcheck;
  makeField(this.searchid, 15);
  makeButton("Search", "search");
  makeField(this.replaceid, 15);
  makeButton("Replace", "replace");
  makeButton("Replace All", "replaceall");
  makeSpace("SearchSep");
  makeButton("Undo", "undo");
  makeButton("Redo", "redo");
  makeSpace("UndoSep");
  makeButton("Help", "help");
'''
        button_impl = '''
  search: function() {
    var text = document.getElementById(this.searchid).value;
    if (!text) {
      alert("Please specify something in the search field!");
      return;
    }
    var first = true;
    var line = this.editor.getCursor()
    do {
      if (!first) line = 0;
      var cursor = this.editor.getSearchCursor(text, line, first);
      first = false;
      while (cursor.findNext()) {
        this.editor.setSelection(cursor.from(), cursor.to());
        return;
      }
    } while (confirm("End of document reached. Start over?"));
  },

  replace: function() {
    var from = document.getElementById(this.searchid).value;
    if (!from) {
      alert("Please specify something to replace in the search field!");
      return;
    }
    var to = document.getElementById(this.replaceid).value;
    var cursor = this.editor.getSearchCursor(from, this.editor.pos, false);
    while (cursor.findNext()) {
      this.editor.setSelection(cursor.from(), cursor.to());
      if (confirm("Replace selected entry with '" + to + "'?")) {
        cursor.replace(to);
      }
    }
  },

  replaceall: function() {
    var from = document.getElementById(this.searchid).value, to;
    if (!from) {
      alert("Please specify something to replace in the search field!");
      return;
    }
    var to = document.getElementById(this.replaceid).value;

    var cursor = this.editor.getSearchCursor(from, false);
    while (cursor.findNext()) {
      cursor.replace(to);
    }
  },

  undo: function() {
    this.editor.undo();
  },
  
  redo: function() {
    this.editor.redo();
  },
  
  help: function() {
    alert("Quick help:\\n\\nShortcuts:\\nCtrl-z: undo\\nCtrl-y: redo\\nTab re-indents line\\nEnter inserts a new indented line\\n\\nPlease refer the CodeMirror manual for more detailed help.");
  },
'''

    if toolbar_buttons == 'ALL':
        init_buttons += '''
  makeSpace("HelpSep");
  makeField(this.jumpid, 2);
  makeButton("Jump to line", "jump");
  makeSpace("JumpSep");
  makeButton("Re-Indent all", "reindent");
  makeSpace("IndentSep");
  makeButton("Toggle line numbers", "line");
  //makeSpace("LineSep");
  //makeButton("Toggle spell check", "spell");
'''
        button_impl += '''
  jump: function() {
    var line = document.getElementById(this.jumpid).value;
    if (line && !isNaN(Number(line)))
      this.editor.scrollIntoView(Number(line));
    else
      alert("Please specify a line to jump to in the jump field!");
  },

  line: function() {
    this.editor.setOption("lineNumbers", !this.editor.getOption("lineNumbers"));
    this.editor.focus();
  },

  reindent: function() {
    var that = this.editor;
    var last = that.lineCount();
    that.operation(function() {
                       for (var i = 0; i < last; ++i) that.indentLine(i);
                   });
  },
  
  spell: function() {
    if (this.spellcheck == undefined) this.spellcheck = !this.editor.options.disableSpellcheck;
    this.spellcheck = !this.spellcheck
    this.editor.setSpellcheck(this.spellcheck);
    this.editor.focus();
  },
'''

    script = '''
/*
Modified version of the MirrorFrame example from CodeMirror:
Adds a basic toolbar to the editor widget with limited use of alert popups.
*/


function dumpobj(obj) {
  alert("dump: " + obj.toSource());
}


function TextAreaEditor(toolbar, textarea, options) {
  this.bar = toolbar;
  this.prefix = textarea;
  this.searchid = this.prefix + "searchfield";
  this.replaceid = this.prefix + "replacefield";
  this.jumpid = this.prefix + "jumpfield";

  var self = this;
  function makeButton(name, action) {
    var button = document.createElement("INPUT");
    button.type = "button";
    button.value = name;
    self.bar.appendChild(button);
    button.onclick = function() { self[action].call(self); };
  }
  function makeField(name, size) {
    var field = document.createElement("INPUT");
    field.type = "text";
    field.id = name;
    field.size = size;
    self.bar.appendChild(field);
  }
  function makeSpace(name) {
    var elem = document.createTextNode(" | ");
    self.bar.appendChild(elem);
  }

%s  

  this.editor = CodeMirror.fromTextArea(textarea, options);
}

TextAreaEditor.prototype = {
%s
};
''' % (init_buttons, button_impl)
    out = '''
<div class="inlineeditor" id="%sinlineeditor">
<div class="editortoolbar" id="%stoolbar">
<!-- filled by script -->
</div>
%s
<script type="text/javascript">
%s
var editor = new TextAreaEditor(document.getElementById("%stoolbar"),
                                document.getElementById("%s"), %s);
</script>
</div>
'''
    return out % (name, name, area, script, name, name, py_to_js(edit_opts))


def signature():
    """Signature of the main function"""

    defaults = {'topic': ['general']}
    return ['html_form', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
    client_dir = client_id_dir(client_id)
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_arguments_dict,
        defaults,
        output_objects,
        client_id,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep

    css = '''
<link rel="stylesheet" type="text/css" href="%s/codemirror.css" media="screen"/>
<link rel="stylesheet" type="text/css" href="%s/dialog/dialog.css" media="screen"/>
<link rel="stylesheet" type="text/css" href="/images/css/codemirror.custom.css" media="screen"/>
''' % (cm_css_prefix, cm_addon_prefix)
    javascript = '''
<script type="text/javascript" src="%s/codemirror.js"></script>
<script src="%s/dialog/dialog.js"></script>
<script src="%s/search/searchcursor.js"></script>
<script src="%s/search/search.js"></script>
<script src="%s/edit/matchbrackets.js"></script>
<script src="%s/xml/xml.js"></script>
<script src="%s/javascript/javascript.js"></script>
<script src="%s/css/css.js"></script>
<script src="%s/htmlmixed/htmlmixed.js"></script>
''' % (cm_js_prefix, cm_addon_prefix, cm_addon_prefix, cm_addon_prefix,
       cm_addon_prefix, cm_mode_prefix, cm_mode_prefix, cm_mode_prefix,
       cm_mode_prefix)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Settings'
    title_entry['style'] = css
    title_entry['javascript'] = javascript

    valid_topics = ['general', 'style']
    active_menu = extract_menu(configuration, title_entry)
    if 'submitjob' in active_menu:
        valid_topics.append('job')
    if 'people' in active_menu:
        valid_topics.append('profile')
    if configuration.site_script_deps:
        valid_topics.append('widgets')
    if configuration.arc_clusters:
        valid_topics.append('arc')
    if configuration.site_enable_sftp:
        valid_topics.append('ssh')
    if configuration.site_enable_davs:
        valid_topics.append('davs')
    if configuration.site_enable_ftps:
        valid_topics.append('ftps')
    topics = accepted['topic']
    topics = [i for i in topics if i in valid_topics]
    output_objects.append({'object_type': 'header', 'text'
                          : 'Settings'})

    links = []
    for name in valid_topics:
        links.append({'object_type': 'link', 
                      'destination': "settings.py?topic=%s" % name,
                      'class': '%ssettingslink' % name,
                      'title': 'Switch to %s settings' % name,
                      'text' : '%s settings' % name,
                      })

    output_objects.append({'object_type': 'multilinkline', 'links': links})
    output_objects.append({'object_type': 'text', 'text': ''})

    # load current settings

    current_settings_dict = load_settings(client_id, configuration)
    if not current_settings_dict:

        # no current settings found

        current_settings_dict = {}

    if not topics:
        output_objects.append({'object_type': 'error_text', 'text': 'No valid topics!'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    if 'general' in topics:
        html = \
             '''
        <div id="settings">
        <form method="post" action="settingsaction.py">
        <table class="settings">
        <tr class="title"><td class="centertext">
        Select your %s settings
        </td></tr>
        <tr><td>
        </td></tr>
        <tr><td>
        <input type="hidden" name="topic" value="general" />
        Please note that if you want to set multiple values (e.g. addresses)
        in the same field, you must write each value on a separate line but
        without blank lines.
        </td></tr>
        <tr><td>
        </td></tr>
        ''' % configuration.site_title
        settings_entries = get_settings_specs()
        for (keyword, val) in settings_entries:
            if 'notify' == val['Context'] and \
                   keyword.lower() not in configuration.notify_protocols:
                continue
            html += \
                """
            <tr class='title'><td>
            %s
            </td></tr>
            <tr><td>
            %s
            </td></tr>
            <tr><td>
            """\
                 % (keyword, val['Description'])
            if val['Type'] == 'multiplestrings':
                try:

                    # get valid choices from conf. multiple selections

                    valid_choices = eval('configuration.%s' % keyword.lower())
                    current_choice = []
                    if current_settings_dict.has_key(keyword):
                        current_choice = current_settings_dict[keyword]

                    if len(valid_choices) > 0:
                        html += '<div class="scrollselect">'
                        for choice in valid_choices:
                            selected = ''
                            if choice in current_choice:
                                selected = 'checked'
                            html += '<input type="checkbox" name="%s" %s value="%s">%s<br />'\
                                    % (keyword, selected, choice, choice)
                        html += '</div>'
                except:
                    # failed on evaluating configuration.%s

                    area = \
                         '''<textarea id="%s" cols=40 rows=1 name="%s">''' % (keyword,
                                                               keyword)
                    if current_settings_dict.has_key(keyword):
                        area += '\n'.join(current_settings_dict[keyword])
                    area += '</textarea>'
                    html += wrap_edit_area(keyword, area, general_edit, 'BASIC')

            elif val['Type'] == 'string':

                # get valid choices from conf

                valid_choices = eval('configuration.%s' % keyword.lower())
                current_choice = ''
                if current_settings_dict.has_key(keyword):
                    current_choice = current_settings_dict[keyword]

                if len(valid_choices) > 0:
                    html += '<select name="%s">' % keyword
                    for choice in valid_choices:
                        selected = ''
                        if choice == current_choice:
                            selected = 'selected'
                        html += '<option %s value="%s">%s</option>'\
                             % (selected, choice, choice)
                    html += '</select><br />'
            html += """
            </td></tr>
            """

        html += \
            """
        <tr><td>
        <input type="submit" value="Save Settings" />
        </td></tr>
        </table>
        </form>
        </div>
        """
        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'job' in topics:
        mrsl_path = os.path.join(base_dir, default_mrsl_filename)

        default_mrsl = get_default_mrsl(mrsl_path)
        html = \
        '''
<div id="defaultmrsl">
<form method="post" action="editfile.py">
<table class="defaultjob">
<tr class="title"><td class="centertext">
Default job on submit page
</td></tr>
<tr><td>
</td></tr>
<tr><td>
If you use the same fields and values in many of your jobs, you can save your preferred job description here to always start out with that description on your submit job page.
</td></tr>
<tr><td>
</td></tr>
<tr><td>
<input type="hidden" name="path" value="%(mrsl_template)s" />
<input type="hidden" name="newline" value="unix" />
'''
        keyword = "defaultjob"
        area = '''
<textarea id="%(keyword)s" cols=82 rows=25 name="editarea">
%(default_mrsl)s
</textarea>
'''
        html += wrap_edit_area(keyword, area, edit_defaults, 'BASIC')
        
        html += '''
</td></tr>
<tr><td>
<input type="submit" value="Save template" />
</td></tr>
</table>
</form>
</div>
'''
        html = html % {
            'default_mrsl': default_mrsl,
            'mrsl_template': default_mrsl_filename,
            'site': configuration.short_title,
            'keyword': keyword
            }

        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'style' in topics:
        css_path = os.path.join(base_dir, default_css_filename)
        default_css = get_default_css(css_path)
        html = \
             '''
<div id="defaultcss">
<form method="post" action="editfile.py">
<table class="defaultstyle">
<tr class="title"><td class="centertext">
Default CSS (style) for all pages
</td></tr>
<tr><td>
</td></tr>
<tr><td>
If you want to customize the look and feel of the %(site)s web interfaces you can override default values here. If you leave the style file blank you will just use the default style.<br />
You can copy paste from the available style file links below if you want to override specific parts.<br />
<div class="warningtext">Please note that you can not save an empty style file, but must at least leave a blank line to use defaults. Additionally any errors in your style code may cause severe corruption in your pages, so it may be a good idea to keep another browser tab/window open on this page while experimenting.
</div>
</td></tr>
<tr><td>
<a class="urllink" href="/images/default.css">default</a> , <a class="urllink" href="/images/bluesky.css">bluesky</a>
</td></tr>
<tr><td>
</td></tr>
<tr><td>
<input type="hidden" name="path" value="%(css_template)s" />
<input type="hidden" name="newline" value="unix" />
'''
        keyword = "defaultstyle"
        area = '''
<textarea id="%(keyword)s" cols=82 rows=25 min_len=1 name="editarea">
%(default_css)s
</textarea>
'''
        html += wrap_edit_area(keyword, area, style_edit)
        html += '''
</td></tr>
<tr><td>
<input type="submit" value="Save style" />
</td></tr>
</table>
</form>
</div>
'''
        html = html % {
            'default_css': default_css,
            'css_template': default_css_filename,
            'site': configuration.short_title,
            'keyword': keyword
            }

        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'widgets' in topics:

        # load current widgets

        current_widgets_dict = load_widgets(client_id, configuration)
        if not current_widgets_dict:
            
            # no current widgets found
            
            current_widgets_dict = {}

        html = \
             '''
<div id="widgets">
<form method="post" action="settingsaction.py">
<table class="widgets">
<tr class="title"><td class="centertext">
Default user defined widgets for all pages
</td></tr>
<tr><td>
</td></tr>
<tr><td>
If you want to customize the look and feel of the %s web interfaces you can add your own widgets here. If you leave the widgets blank you will just get the default empty widget spaces.<br />
You can simply copy/paste from the available widget file links below if you want to reuse existing widgets.<br />
</td></tr>
<tr><td>
<a class="urllink" href="/images/widgets/hello-grid.app">hello grid</a>,
<a class="urllink" href="/images/widgets/simple-calendar.app">simple calendar</a>,
<a class="urllink" href="/images/widgets/calendar.app">calendar</a>,
<a class="urllink" href="/images/widgets/gcal.app">google calendar</a>,
<a class="urllink" href="/images/widgets/calculator.app">calculator</a>,
<a class="urllink" href="/images/widgets/localrss.app">local rss reader</a>,
<a class="urllink" href="/images/widgets/rss.app">rss reader</a>,
<a class="urllink" href="/images/widgets/clock.app">clock</a>,
<a class="urllink" href="/images/widgets/weather.app">weather</a>,
<a class="urllink" href="/images/widgets/progressbar.app">progress bar</a>,
<a class="urllink" href="/images/widgets/simple-move.app">simple-move</a>,
<a class="urllink" href="/images/widgets/portlets.app">portlets</a>,
<a class="urllink" href="/images/widgets/countdown.app">countdown</a>,
<a class="urllink" href="/images/widgets/sparkline.app">mini chart</a>,
<a class="urllink" href="/images/widgets/piechart.app">pie chart</a>,
<a class="urllink" href="/images/widgets/simple-jobmon.app">simple-jobmon</a>,
<a class="urllink" href="/images/widgets/cert-countdown.app">certificate countdown</a>,
<a class="urllink" href="/images/widgets/disk-use.app">disk use progress bar</a>,
<a class="urllink" href="/images/widgets/jobs-stats.app">jobs stats table</a>,
<a class="urllink" href="/images/widgets/jobs-stats-chart.app">jobs stats chart</a>,
<a class="urllink" href="/images/widgets/daily-wm-comic.app">Daily WulffMorgenthaler comic</a>,
<a class="urllink" href="/images/widgets/kunet-login.app">KUnet login</a>
<a class="urllink" href="/images/widgets/tdchotspot-login.app">TDC Hotspot login</a>
</td></tr>
<tr><td>
<div class="warningtext">Please note that the widgets parser is rather grumpy so you may have to avoid blank lines in your widget code below. Additionally any errors in your widgets code may cause severe corruption in your pages, so it may be a good idea to keep another browser tab/window open on this page while experimenting.</div> 
</td></tr>
<tr><td>
<input type="hidden" name="topic" value="widgets" />
</td></tr>
<tr><td>
''' % configuration.short_title

        widgets_entries = get_widgets_specs()
        for (keyword, val) in widgets_entries:
            html += \
                """
            <tr class=title><td>
            %s
            </td></tr>
            <tr><td>
            %s
            </td></tr>
            <tr><td>
            """\
                 % (keyword, val['Description'])
            if val['Type'] == 'multiplestrings':
                try:

                    # get valid choices from conf. multiple selections

                    valid_choices = eval('configuration.%s' % keyword.lower())
                    current_choice = []
                    if current_widgets_dict.has_key(keyword):
                        current_choice = current_widgets_dict[keyword]

                    if len(valid_choices) > 0:
                        html += '<div class="scrollselect">'
                        for choice in valid_choices:
                            selected = ''
                            if choice in current_choice:
                                selected = 'checked'
                            html += '<input type="checkbox" name="%s" %s value="%s">%s<br />'\
                                    % (keyword, selected, choice, choice)
                        html += '</div>'
                except:
                    area = \
                         """<textarea id='%s' cols=78 rows=10 name='%s'>""" % \
                         (keyword, keyword)
                    if current_widgets_dict.has_key(keyword):
                        area += '\n'.join(current_widgets_dict[keyword])
                    area += '</textarea>'
                    html += wrap_edit_area(keyword, area, widgets_edit)

        html += \
             '''
        <tr><td>
        <input type="submit" value="Save Widgets" />
</td></tr>
</table>
</form>
</div>
'''
        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'profile' in topics:

        # load current profile

        current_profile_dict = load_profile(client_id, configuration)
        if not current_profile_dict:
            
            # no current profile found
            
            current_profile_dict = {}

        (got_list, all_vgrids) = vgrid_list_vgrids(configuration)
        if not got_list:
            all_vgrids = []
        all_vgrids.append(any_vgrid)
        all_vgrids.sort()
        configuration.vgrids_allow_email = all_vgrids
        configuration.vgrids_allow_im = all_vgrids
        images = []
        for path in os.listdir(base_dir):
            real_path = os.path.join(base_dir, path)
            if os.path.splitext(path)[1].strip('.') in profile_img_extensions \
                   and os.path.getsize(real_path) < profile_img_max_kb*1024:
                images.append(path)
        configuration.public_image = images
        html = \
             '''
<div id="profile">
<form method="post" action="settingsaction.py">
<table class="profile">
<tr class="title"><td class="centertext">
Public profile information visible to other users.
</td></tr>
<tr><td>
</td></tr>
<tr><td>
If you want to let other users know more about you can add your own text here. If you leave the text area blank you will just get the default empty profile information.<br />
</td></tr>
<tr><td>
<div class="warningtext">Please note that the profile parser is rather grumpy so you may have to avoid blank lines in your text below.
</div> 
</td></tr>
<tr><td>
<input type="hidden" name="topic" value="profile" />
</td></tr>
<tr><td>
'''

        profile_entries = get_profile_specs()
        for (keyword, val) in profile_entries:
            html += \
                """
            <tr class=title><td>
            %s
            </td></tr>
            <tr><td>
            %s
            </td></tr>
            <tr><td>
            """\
                 % (keyword, html_escape(val['Description']))
            if val['Type'] == 'multiplestrings':
                try:

                    # get valid choices from conf. multiple selections

                    valid_choices = eval('configuration.%s' % keyword.lower())
                    current_choice = []
                    if current_profile_dict.has_key(keyword):
                        current_choice = current_profile_dict[keyword]

                    if len(valid_choices) > 0:
                        html += '<div class="scrollselect">'
                        for choice in valid_choices:
                            selected = ''
                            if choice in current_choice:
                                selected = 'checked'
                            html += '<input type="checkbox" name="%s" %s value="%s">%s<br />'\
                                    % (keyword, selected, choice, choice)
                        html += '</div>'
                except:
                    area = \
                         """<textarea id='%s' cols=78 rows=10 name='%s'>""" % \
                         (keyword, keyword)
                    if current_profile_dict.has_key(keyword):
                        area += '\n'.join(current_profile_dict[keyword])
                    area += '</textarea>'
                    html += wrap_edit_area(keyword, area, profile_edit)
            elif val['Type'] == 'boolean':
                valid_choices = [True, False]
                current_choice = ''
                if current_profile_dict.has_key(keyword):
                    current_choice = current_profile_dict[keyword]

                if len(valid_choices) > 0:
                    html += '<select name="%s">' % keyword
                    for choice in valid_choices:
                        selected = ''
                        if choice == current_choice:
                            selected = 'selected'
                        html += '<option %s value="%s">%s</option>'\
                             % (selected, choice, choice)
                    html += '</select><br />'

        html += \
             '''
        <tr><td>
        <input type="submit" value="Save Profile" />
</td></tr>
</table>
</form>
</div>
'''
        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'ssh' in topics:

        # load current ssh

        current_ssh_dict = load_ssh(client_id, configuration)
        if not current_ssh_dict:
            
            # no current ssh found
            
            current_ssh_dict = {}

        default_authkeys = current_ssh_dict.get('authkeys', '')
        default_authpassword = current_ssh_dict.get('authpassword', '')
        sftp_server = configuration.user_sftp_address
        # address may be empty to use all interfaces - then use FQDN
        if not sftp_server:
            sftp_server = configuration.server_fqdn
        sftp_port = configuration.user_sftp_port
        html = \
        '''
<div id="sshaccess">
<form method="post" action="settingsaction.py">
<table class="sshsettings">
<tr class="title"><td class="centertext">
SSH/SFTP access to your MiG account
</td></tr>
<tr><td>
</td></tr>
<tr><td>
You can configure SFTP login to your %(site)s account for efficient file
access. Login takes place with %(auth_methods)s and your automatic
username:
<pre>%(username)s</pre>
%(pw_key_notes)s
<h3>Graphical SFTP access</h3>
The FireFTP plugin for Firefox is known to generally work for graphical
access to your MiG home over SFTP.
Enter the following values in the FireFTP Account Manager:
<pre>
Host %(sftp_server)s
Login %(username)s
Password YOUR_KEY_PASSWORD_HERE
Security SFTP
Port %(sftp_port)s
Private Key ~/.mig/key.pem
</pre>
other graphical clients may work as well.
<h3>Command line SFTP/SSHFS access on Linux/UN*X</h3>
Save something like the following lines in your local ~/.ssh/config
to avoid typing the full login details every time:<br />
<pre>
Host %(sftp_server)s
Hostname %(sftp_server)s
User %(username)s
Port %(sftp_port)s
IdentityFile ~/.mig/key.pem
</pre>
From then on you can use sftp and sshfs to access your MiG home:
<pre>
sftp %(sftp_server)s
</pre>
<pre>
sshfs %(sftp_server)s: mig-home -o uid=$(id -u) -o gid=$(id -g)
</pre>
</td></tr>
<tr><td>
<input type="hidden" name="topic" value="ssh" />
'''
        
        pw_key_notes = ''
        keyword_keys = "authkeys"
        if 'publickey' in configuration.user_sftp_auth:
            pw_key_notes += '''
You can use any existing RSA key, including the key.pem you received along with
your user certificate, or create a new one. In any case you need to save the
contents of the corresponding public key (X.pub) in the text area below, to be
able to connect with username and key as described in the following sections.
'''
            html += '''
</td></tr>
<tr><td>
'''
            area = '''
<textarea id="%(keyword_keys)s" cols=82 rows=5 name="publickeys">
%(default_authkeys)s
</textarea>
'''
            html += wrap_edit_area(keyword_keys, area, ssh_edit, 'BASIC')
            html += '''
(leave empty to disable sftp access with public keys)
</td></tr>
'''
            
        keyword_password = "authpassword"
        if 'password' in configuration.user_sftp_auth:
            pw_key_notes += '''
Please enter and save your desired password in the text field below, to be able
to connect with username and password as described in the following sections.
'''
            # We only want a single password and a masked input field
            html += '''
<tr><td>
<input type=password id="%(keyword_password)s" size=40 name="password"
value="%(default_authpassword)s" />
(leave empty to disable sftp access with password)
</td></tr>
'''
        
        html += '''
<tr><td>
<input type="submit" value="Save ssh" />
</td></tr>
'''
        
        html += '''
</table>
</form>
</div>
'''
        html = html % {
            'default_authkeys': default_authkeys,
            'default_authpassword': default_authpassword,
            'site': configuration.short_title,
            'keyword_keys': keyword_keys,
            'keyword_password': keyword_password,
            'username': client_alias(client_id),
            'sftp_server': sftp_server,
            'sftp_port': sftp_port,
            'pw_key_notes': pw_key_notes,
            'auth_methods': ' or '.join(configuration.user_sftp_auth),
            }

        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'davs' in topics:

        # load current davs

        current_davs_dict = load_davs(client_id, configuration)
        if not current_davs_dict:
            
            # no current davs found
            
            current_davs_dict = {}

        default_authkeys = current_davs_dict.get('authkeys', '')
        default_authpassword = current_davs_dict.get('authpassword', '')
        davs_server = configuration.user_davs_address
        # address may be empty to use all interfaces - then use FQDN
        if not davs_server:
            davs_server = configuration.server_fqdn
        davs_port = configuration.user_davs_port
        html = \
        '''
<div id="davsaccess">
<form method="post" action="settingsaction.py">
<table class="davssettings">
<tr class="title"><td class="centertext">
Secure WebDAV access to your MiG account
</td></tr>
<tr><td>
</td></tr>
<tr><td>
You can configure secure WebDAV login to your %(site)s account for efficient
file access. Login takes place with %(auth_methods)s and your automatic
username:
<pre>%(username)s</pre>
%(pw_key_notes)s
<h3>Graphical WebDAV access</h3>
Several native file browsers and web browsers are known to generally work for
graphical access to your MiG home over WebDAV when password support is enabled.
<br />
Enter the address https://%(davs_server)s:%(davs_port)s and when fill in the
login details:
<pre>
Username %(username)s
Password YOUR_PASSWORD_HERE
</pre>
other graphical clients should work as well.
<h3>Command line WebDAV access on Linux/UN*X</h3>
Save something like the following lines in your local ~/.netrc
to avoid typing the full login details every time:<br />
<pre>
machine %(davs_server)s
login %(username)s
password YOUR_PASSWORD_HERE
</pre>
From then on you can use e.g. cadaver or fusedav to access your MiG home:
<pre>
cadaver https://%(davs_server)s:%(davs_port)s
</pre>
<pre>
fusedav https://%(davs_server)s:%(davs_port)s mig-home -o uid=$(id -u) -o gid=$(id -g)
</pre>
</td></tr>
<tr><td>
<input type="hidden" name="topic" value="davs" />
'''
        
        pw_key_notes = ''
        keyword_keys = "authkeys"
        if 'publickey' in configuration.user_davs_auth:
            pw_key_notes += '''
You can use any existing RSA key, including the key.pem you received along with
your user certificate, or create a new one. In any case you need to save the
contents of the corresponding public key (X.pub) in the text area below, to be
able to connect with username and key as described in the following sections.
'''
            html += '''
</td></tr>
<tr><td>
'''
            area = '''
<textarea id="%(keyword_keys)s" cols=82 rows=5 name="publickeys">
%(default_authkeys)s
</textarea>
'''
            html += wrap_edit_area(keyword_keys, area, davs_edit, 'BASIC')
            html += '''
(leave empty to disable davs access with public keys)
</td></tr>
'''
            
        keyword_password = "authpassword"
        if 'password' in configuration.user_davs_auth:
            pw_key_notes += '''
Please enter and save your desired password in the text field below, to be able
to connect with username and password as described in the following sections.
'''
            # We only want a single password and a masked input field
            html += '''
<tr><td>
<input type=password id="%(keyword_password)s" size=40 name="password"
value="%(default_authpassword)s" />
(leave empty to disable davs access with password)
</td></tr>
'''
        
        html += '''
<tr><td>
<input type="submit" value="Save davs" />
</td></tr>
'''
        
        html += '''
</table>
</form>
</div>
'''
        html = html % {
            'default_authkeys': default_authkeys,
            'default_authpassword': default_authpassword,
            'site': configuration.short_title,
            'keyword_keys': keyword_keys,
            'keyword_password': keyword_password,
            'username': client_alias(client_id),
            'davs_server': davs_server,
            'davs_port': davs_port,
            'pw_key_notes': pw_key_notes,
            'auth_methods': ' or '.join(configuration.user_davs_auth),
            }

        output_objects.append({'object_type': 'html_form', 'text': html})

    if 'ftps' in topics:

        # load current ftps

        current_ftps_dict = load_ftps(client_id, configuration)
        if not current_ftps_dict:
            
            # no current ftps found
            
            current_ftps_dict = {}

        default_authkeys = current_ftps_dict.get('authkeys', '')
        default_authpassword = current_ftps_dict.get('authpassword', '')
        ftps_server = configuration.user_ftps_address
        # address may be empty to use all interfaces - then use FQDN
        if not ftps_server:
            ftps_server = configuration.server_fqdn
        ftps_ctrl_port = configuration.user_ftps_ctrl_port
        html = \
        '''
<div id="ftpsaccess">
<form method="post" action="settingsaction.py">
<table class="ftpssettings">
<tr class="title"><td class="centertext">
Secure FTP access to your MiG account
</td></tr>
<tr><td>
</td></tr>
<tr><td>
You can configure secure FTP login to your %(site)s account for efficient file
access. Login takes place with %(auth_methods)s and your automatic
username:
<pre>%(username)s</pre>
%(pw_key_notes)s
<h3>Graphical FTP access</h3>
Several native file browsers and web browsers are known to generally work for
graphical access to your MiG home over FTP when password support is enabled.
<br />
Enter the address ftps://%(ftps_server)s:%(ftps_ctrl_port)s and when fill in the
login details:
<pre>
Username %(username)s
Password YOUR_PASSWORD_HERE
</pre>
other graphical clients should work as well.
<h3>Command line FTP access on Linux/UN*X</h3>
Save something like the following lines in your local ~/.netrc
to avoid typing the full login details every time:<br />
<pre>
machine %(ftps_server)s
login %(username)s
password YOUR_PASSWORD_HERE
</pre>
From then on you can use e.g. lftp or CurlFtpFS to access your MiG home:
<pre>
lftp -e "set ssl:ca-file $HOME/.mig/cacert.pem; set ftp:ssl-protect-data on" \\
    -p %(ftps_ctrl_port)s %(ftps_server)s
</pre>
<pre>
curlftpfs -o ssl -o cacert=$HOME/.mig/cacert.pem \\
    %(ftps_server)s:%(ftps_ctrl_port)s mig-home -o uid=$(id -u) -o gid=$(id -g)
</pre>
</td></tr>
<tr><td>
<input type="hidden" name="topic" value="ftps" />
'''
        
        pw_key_notes = ''
        keyword_keys = "authkeys"
        if 'publickey' in configuration.user_ftps_auth:
            pw_key_notes += '''
You can use any existing RSA key, including the key.pem you received along with
your user certificate, or create a new one. In any case you need to save the
contents of the corresponding public key (X.pub) in the text area below, to be
able to connect with username and key as described in the following sections.
'''
            html += '''
</td></tr>
<tr><td>
'''
            area = '''
<textarea id="%(keyword_keys)s" cols=82 rows=5 name="publickeys">
%(default_authkeys)s
</textarea>
'''
            html += wrap_edit_area(keyword_keys, area, ftps_edit, 'BASIC')
            html += '''
(leave empty to disable ftps access with public keys)
</td></tr>
'''
            
        keyword_password = "authpassword"
        if 'password' in configuration.user_ftps_auth:
            pw_key_notes += '''
Please enter and save your desired password in the text field below, to be able
to connect with username and password as described in the following sections.
'''

            # We only want a single password and a masked input field
            html += '''
<tr><td>
<input type=password id="%(keyword_password)s" size=40 name="password"
value="%(default_authpassword)s" />
(leave empty to disable ftps access with password)
</td></tr>
'''
        
        html += '''
<tr><td>
<input type="submit" value="Save ftps" />
</td></tr>
'''
        
        html += '''
</table>
</form>
</div>
'''
        html = html % {
            'default_authkeys': default_authkeys,
            'default_authpassword': default_authpassword,
            'site': configuration.short_title,
            'keyword_keys': keyword_keys,
            'keyword_password': keyword_password,
            'username': client_alias(client_id),
            'ftps_server': ftps_server,
            'ftps_ctrl_port': ftps_ctrl_port,
            'pw_key_notes': pw_key_notes,
            'auth_methods': ' or '.join(configuration.user_ftps_auth),
            }

        output_objects.append({'object_type': 'html_form', 'text': html})

    # if ARC-enabled server:
    if 'arc' in topics:
        # provide information about the available proxy, offer upload
        try:
            home_dir = os.path.normpath(base_dir)
            session_Ui = arc.Ui(home_dir, require_user_proxy=True)
            proxy = session_Ui.getProxy()
            if proxy.IsExpired():
                # can rarely happen, constructor will throw exception
                output_objects.append({'object_type': 'text', 
                                       'text': 'Proxy certificate is expired.'})
            else:
                output_objects.append({'object_type': 'text', 
                                       'text': 'Proxy for %s' \
                                       % proxy.GetIdentitySN()})
                output_objects.append(
                    {'object_type': 'text', 
                     'text': 'Proxy certificate will expire on %s (in %s sec.)' \
                     % (proxy.Expires(), proxy.getTimeleft())
                     })
        except arc.NoProxyError, err:
            output_objects.append({'object_type':'warning',
                                   'text': 'No proxy certificate to load: %s' \
                                   % err.what()})
    
        output_objects = output_objects + arc.askProxy()
    
    return (output_objects, returnvalues.OK)


