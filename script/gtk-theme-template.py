#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

# for finding files
import glob

# for xml parsing
import xml.dom.minidom
import xml.dom

# for os.path / os.mkdir
import os

# for pretty printing
from pprint import pprint

htmlPathName = "/home/unknown/tmp/gtk3/gtk3/gtk+-3.1.4/docs/reference/gtk/html"
templatePathName = "template/gtk-3.0"
snippetsPath = "snippets"

def getWidgetNameAndNode(root):
	elements = root.getElementsByTagName ('h2')
	found = False

	for element in elements:
		if element.firstChild.nodeValue == "Style Property Details":
			found = True
			break;

	if found:
		widgetName = (element.previousSibling.previousSibling.getAttribute("name").split(".")[0])
		return (widgetName, element.parentNode)
	else:
		return (None, None)
	

def getWidgetStyleProperty (propertyParent):
	properties = {}

	propNode = propertyParent.getElementsByTagName ("pre")
	propName = propNode[0].firstChild.nodeValue.split('"')[1]

	propNode = propertyParent.getElementsByTagName ("span")
	propType = propNode[0].firstChild.nodeValue
	properties['type'] = propType

	propDesc = propertyParent.getElementsByTagName ("p")[0]
	propDesc = propDesc.firstChild.nodeValue.split (".")[0]
	propDesc = propDesc.strip().replace("\n", " ") + "."
	properties['description'] = propDesc

	nodes = propertyParent.getElementsByTagName ("p")
	for node in nodes:

		if node.firstChild.nodeValue.startswith ("Default"):
			defaultValue = node.firstChild.nodeValue.split(":")[1].strip()
			properties['default'] = defaultValue

		if node.firstChild.nodeValue.startswith ("Allowed"):
			allowedValue = node.firstChild.nodeValue.split(":")[1].strip()
			properties['allowed'] = allowedValue

	return (propName, properties)


def getWidgetStyleProperties (propertiesParent):
		properties = []
		for node in propertiesParent.childNodes:
			if node.nodeType == node.ELEMENT_NODE and node.tagName == "div":
				widgetProperties = getWidgetStyleProperty (node)
				if widgetProperties != None:
					properties.append (widgetProperties)

		return properties

def getWidgetHierarcyNode (widgetName, root):
	nodes = root.getElementsByTagName ("h2")
	for node in nodes:
		if node.firstChild.nodeValue == "Object Hierarchy":
			return node.parentNode.getElementsByTagName ("pre")[0]

	return None

def getWidgetHierarchy (widgetName, rootNode):
	hierarchy = []

	hierarchyNode = getWidgetHierarcyNode (widgetName, rootNode)

	for node in hierarchyNode.childNodes:
		if node.nodeType == node.TEXT_NODE:
			lines = node.nodeValue.replace("+----", "").splitlines ()
			lines = map (lambda x: x.strip(), lines)
			hierarchy.extend(lines)
			
		elif node.nodeType == node.ELEMENT_NODE:
			hierarchy.append (node.firstChild.nodeValue)
		else:
			hierarchy = None
			break

	hierarchy = [x for x in hierarchy if x != "" and  x != "GObject" and x != "GInitiallyUnowned"]
	widgetIndex = hierarchy.index (widgetName)
	hierarchy = hierarchy[0:widgetIndex+1]
	hierarchy.reverse()

	return hierarchy


def getWidgetDetailsFromFile (fileName):
	widgetDetails = {}

	root = xml.dom.minidom.parse (fileName).documentElement

	(widgetName, propertiesParent) = getWidgetNameAndNode (root)

	if widgetName != None and propertiesParent != None:
		widgetDetails['styleProperties'] = getWidgetStyleProperties (propertiesParent)
		widgetDetails['hierarchy'] = getWidgetHierarchy (widgetName, root)

		return (widgetName, widgetDetails)
	else:
		return (None, None)


def getWidgetDetails (htmlPathName):
	properties = {}

	#for fileName in [(htmlPathName + "/GtkButton.html")]:
	for fileName in glob.iglob (htmlPathName + "/Gtk*html"):
		print ("Processing '{}'".format (fileName))
		(k, v) = getWidgetDetailsFromFile (fileName)

		if k != None and v != None:
			properties[k] = v

	return properties


def getStyleClassesTable (root):
	nodes = root.getElementsByTagName ('h3')

	for node in nodes:
		if node.firstChild.nodeValue == "Style classes and regions":
			break;

	sectionNode = node.parentNode

	tableNode = sectionNode.getElementsByTagName ('table')[0]

	return tableNode


def getStyleClassesTableBody (root):
	tableNode = getStyleClassesTable (root)
	return tableNode.getElementsByTagName ('tbody')[0]


def getStyleClassesDetailClassName (rowNode):
	colNode = rowNode.getElementsByTagName ('td')[0]
	return colNode.firstChild.nodeValue


def getStyleClassesDetailClassMembers (rowNode):
	members = set()
	colNode = rowNode.getElementsByTagName ('td')[2]

	for node in colNode.getElementsByTagName ('span'):
		members.add (node.firstChild.nodeValue)

	return members


def getStyleClassesDetails (rowNode):
	className = getStyleClassesDetailClassName (rowNode)
	classMembers = getStyleClassesDetailClassMembers (rowNode)

	return (className, classMembers)


def getStyleClasses (htmlPathName):
	styleClasses = {}

	fileName = htmlPathName + "/GtkStyleContext.html"

	root = xml.dom.minidom.parse (fileName).documentElement

	tableNode = getStyleClassesTableBody (root)

	for rowNode in tableNode.getElementsByTagName ('tr'):
		(k, v) = getStyleClassesDetails (rowNode)

		if k != None and k != "default" and v != None and len(v) > 0:
			styleClasses[k] = v

	return styleClasses


""" Print out the css for a single widget. """
def makeWidgetText (widgetName, widgetDetails):
	text = widgetName + " {\n"
	text = text + "\t/**\n\t* Style properties inheritance:\n\t*  " + "->".join(widgetDetails['hierarchy']) + ".\n\t*/\n"
	

	for (propName, propData) in widgetDetails['styleProperties']:
		defaultValue = propData.get ("default", "")
		typeValue = propData.get ("type")
		allowedValue = propData.get ("allowed")

		text += "\n"
		text += "\t/* {} */\n".format (propData["description"])
		text += "\t/* {}: {}; */".format (propName, defaultValue)
		if typeValue != None and allowedValue != None:
			text += " /* {}, {} */\n".format (typeValue, allowedValue)
		elif typeValue != None:
			text += " /* {} */\n".format (typeValue)
		elif allowedValue != None:
			text += " /* {} */\n".format (allowedValue)

	text += "\n}"

	(header, footer) = readHeaderFooter (widgetName)
	
	if header != None:
		text = header + text

	if footer != None:
		text += "\n\n"
		text += footer

	return text
	

""" Print out the css for all widgets in WidgetPropertiesTable. """
def makeWidgetTexts (widgetPropertiesTable):
	widgetTexts = {}

	for (widgetName, widgetDetails) in widgetPropertiesTable.items():
		widgetText = makeWidgetText (widgetName, widgetDetails)
		if widgetText != None:
			widgetTexts[widgetName] = widgetText

	return widgetTexts

def makeStyleClassText (className, classWidgets):
	classText = "." + className + " {\n"
	classText += "\t/* Members: " + ", ".join(classWidgets) + ". */\n"
	classText += "}\n\n"
	return classText

def makeStyleClassTexts (widgetClassesTable, widgetDetails):
	(header, footer) = readHeaderFooter ("gtk-widgets")

	if header != None: text = header
	else: text = ""

	for (className, classWidgets) in widgetClassesTable.items():
		text += makeStyleClassText (className, classWidgets)

	text += "\n"
	text += "/*\n * Imports for widget-specific theming.\n */\n\n"

	for widgetName in widgetDetails.keys():
		text += "@import url(\"widgets/{}.css\");\n".format(widgetName.lower())

	if footer != None: text += footer

	return text

def makeColorsCss ():
	(header, footer) = readHeaderFooter ("colors")
	text = ""

	if header != None: text = header + text
	if footer != None: text += footer

	return text


def makeGtkCss ():
	(header, footer) = readHeaderFooter ("gtk")
	text = ""

	if header != None: text = header + text
	if footer != None: text += footer

	return text

def writeStyleClassTexts (styleClasses, widgetDetails):
	writeFile ("gtk-widgets.css", makeStyleClassTexts (styleClasses, widgetDetails))

""" Write the Widgets/WidgetName.css file for a single widget. """
def writeWidgetText (path, widgetName, widgetText):
	fileName = os.path.join (path, widgetName.lower() + ".css")
	writeFile (fileName, widgetText)

""" Write all the Widgets/WidgetName.css files. """
def writeWidgetTexts (widgetDetails):
	widgetTexts = makeWidgetTexts (widgetDetails)

	for (widgetName, widgetText) in widgetTexts.items():
		writeWidgetText ("widgets", widgetName, widgetText)

def writeFile (fileName, text):
	fileName = os.path.join (templatePathName, fileName)
	os.makedirs (os.path.dirname(fileName), exist_ok=True)
	f = open (fileName, "w")
	print ("Writing '{}'".format(fileName))
	f.write (text)
	f.close ()

def writeIndexTheme ():
	fileName = os.path.join (snippetsPath, "index.theme")
	f = open (fileName, "r")
	text = f.read()
	f.close

	fileName = os.path.join (templatePathName, "../index.theme")
	f = open (fileName, "w")
	f.write (text)
	f.close

def readFile (fileName):
	if os.path.exists (fileName):
		f = open (fileName, "r")
		text = f.read ()
		f.close ()
		return text
	else:
		return None

def readHeader (name):
	fileName = os.path.join (snippetsPath, name.lower() + "_header.css")
	return readFile (fileName)

def readFooter (name):
	fileName = os.path.join (snippetsPath, name.lower() + "_footer.css")
	return readFile (fileName)

def readHeaderFooter (name):
	return (readHeader(name), readFooter(name))

def writeTemplate ():
	widgets = getWidgetDetails (htmlPathName)
	classes = getStyleClasses (htmlPathName)

	writeWidgetTexts (widgets)
	writeStyleClassTexts (classes, widgets)
	writeFile ("gtk.css", makeGtkCss())
	writeFile ("colors.css", makeColorsCss())
	writeIndexTheme ()

writeTemplate ()
