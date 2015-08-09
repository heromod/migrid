# Custom Web Interfaces #

Users can customize their private MiG pages in terms of layout and additional content.
On the Settings page there's a _style settings_ subpage where all page style settings can be overruled to provide anything from simple page layout changes to a complete change of the default page _skin_.
Additional page content in the form of _widgets_ can be configured on the _widgets settings_ subpage. Widgets can be anything from plain text or static HTML to fully interactive gadgets written in JavaScript, CSS and HTML. A number of example widgets are included, but users can develop their own widgets, too.

Please tell us if you developed your own skins or widgets suitable for inclusion in the examples. In that way your effort may be of help to other users!


## Style ##
The style editor allows you to define your own Cascading Style Sheet (CSS) for defining the layout of all pages. If you are not familiar with CSS, you can find tons of tutorials on the internet, but simple changes may not even require much more than a few experiments with the examples.
You can load the _default_ style sheet on the style settings page and copy/paste any sections your want to override into the editor field there. Then you are free to experiment with each of the settings until you are satisfied with the page layout. It may be a good idea to keep a backup window/tab open with the original style contents for easy restoring in the rare case that some experiment renders new pages completely unusable.

The _bluesky_ style sheet available on the same page is a quite different skin with a horizontal top menu instead of the default vertical menu. It used to be the default style some time ago, so it should still be mostly working despite any recent development mainly considering the new default style.

As a simple example we could change the background color on all pages to a light blue one by just entering:
```
body {
    background: lightblue;
}
```
in the style editor and hit _Save style_ to immediately see the result.

A more MiG specific example is to hide the small exit code at the bottom of the page. Viewing the raw page source code of e.g. the Settings page we can find the exit code text to be wrapped in a _div_ tag with an id of 'exitcode'. Alternatively we could go searching for mention of 'exit' in the default CSS and find the exitcode section there. Now to actually hide the exit code we can simply define our style sheet to not display this particular _div_:
```
#exitcode {
    display: none;
}
```
Simply hit _Save style_ and watch the exit code line disappear.


## Widgets ##
The widget editors are used for adding your own content to your private MiG pages. Four widget areas are provided for a flexible widget positioning. the actual location of the areas depend on the active page style as described in the previous section. With the default style the areas are located above and below the navigation menu and above and below the framed white content area to the right of the menu. As the menu is rather narrow the number of widgets fitting above and below the menu is rather limited, but bigger widgets can just sit above or below the content area.

The simplest test is to just enter a basic text in e.g. the PREMENU editor and hit _Save Widgets_ at the bottom of the page. Please note that widget changes only show up after the next page load, so the save widgets page will not show the update, but if you reload or open another page your changes should now show up.

You can load any one of the example widgets on the widgets settings page and copy/paste them into one of the editor fields there to try it out. Please read the header of the examples carefully and tick any mentioned dependencies (entries in the _Requires_ list) in the SITE\_SCRIPT\_DEPS selector above the widget editors. For the simple calendar example this would be the jquery.js and jquery.calendar-widget.js entries.
If you do not enable the required '.js' dependencies you will get a 'Please enable Javascript to view ...' message where your widget was supposed to be displayed and if you miss any '.css' dependencies your widget will likely look strange or unpolished.
Just keep experimenting with the widgets until you are satisfied with the contents and layout. Again it may be a good idea to keep a backup window/tab open with the original widgets contents for easy restoring in the rare case that some experiment renders new pages completely unusable.

Remember that widget areas can contain just about any HTML contents so you can use HTML elements like lists or tables to layout multiple widgets side by side or in a grid.