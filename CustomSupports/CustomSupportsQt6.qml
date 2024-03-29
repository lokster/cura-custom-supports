// Copyright (c) 2016 Ultimaker B.V.
// Copyright (c) 2020 Lokster <http://lokspace.eu>

import QtQuick 2.2
import QtQuick.Controls 2.2

import UM 1.5 as UM

Item
{
    id: base;
    width: childrenRect.width;
    height: childrenRect.height;

    property var currentSupportType: UM.ActiveTool.properties.getValue("SupportType");

    function setSupportType(type)
    {
        // set checked state of mesh type buttons
        supportCubeButton.checked = type === 'cube';
        supportCylinderButton.checked = type === 'cylinder';
        UM.ActiveTool.setProperty("SupportType", type);
    }

    Column
    {
        id: supportTypeItems
        anchors.top: parent.top;
        anchors.left: parent.left;
        spacing: UM.Theme.getSize("default_margin").height;

        Row // Mesh type buttons
        {
            id: supportTypeButtons
            spacing: UM.Theme.getSize("default_margin").width

            UM.ToolbarButton
            {
                id: supportCubeButton;
                text: catalog.i18nc("@label", "Use Cube");

                toolItem: UM.ColorImage
                {
                    source: Qt.resolvedUrl("support_type_cube.svg")
                    color: UM.Theme.getColor("icon")
                }

                property bool needBorder: true;
                checkable: true;
                onClicked: setSupportType('cube');
                checked: UM.ActiveTool.properties.getValue("SupportType") === 'cube';
                z: 2;
            }

            UM.ToolbarButton
            {
                id: supportCylinderButton;
                text: catalog.i18nc("@label", "Use Cylinder");

                toolItem: UM.ColorImage
                {
                    source: Qt.resolvedUrl("support_type_cylinder.svg")
                    color: UM.Theme.getColor("icon")
                }

                property bool needBorder: true;
                checkable:true;
                onClicked: setSupportType('cylinder');
                checked: UM.ActiveTool.properties.getValue("SupportType") === 'cylinder';
                z: 1;
            }

            UM.ToolbarButton
            {
                id: donateButton;
                text: catalog.i18nc("@label", "Donate to the plugin developer!");

                toolItem: UM.ColorImage
                {
                    source: Qt.resolvedUrl("donate.svg")
                    color: UM.Theme.getColor("icon")
                }

                property bool needBorder: true;
                onClicked: Qt.openUrlExternally('https://paypal.me/loksterr?locale.x=en_US');
            }


        }
    }

    UM.CheckBox
    {
        id: dropToBuildplateCheckbox;
        anchors.top: supportTypeItems.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").height;
        anchors.left: parent.left;
        text: catalog.i18nc("@option:check","Drop to build plate");

        checked: UM.ActiveTool.properties.getValue("DropToBuildplate");
        onClicked: UM.ActiveTool.setProperty("DropToBuildplate", checked);
    }

    UM.CheckBox
    {
        id: widerBaseCheckbox;
        anchors.top: dropToBuildplateCheckbox.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").height;
        anchors.left: parent.left;
        text: catalog.i18nc("@option:check","Wider base");

        checked: UM.ActiveTool.properties.getValue("WiderBase");
        onClicked: UM.ActiveTool.setProperty("WiderBase", checked);
    }

    Grid
    {
        id: textfields;
        anchors.top: widerBaseCheckbox.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").height;
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;

        columns: 2;
        flow: Grid.TopToBottom;
        spacing: Math.round(UM.Theme.getSize("default_margin").width / 2);

        Label
        {
            height: UM.Theme.getSize("setting_control").height;
            text: "Size";
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            verticalAlignment: Text.AlignVCenter;
            renderType: Text.NativeRendering;
            width: Math.ceil(contentWidth);
        }

        Label
        {
            height: UM.Theme.getSize("setting_control").height;
            text: "Base";
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            verticalAlignment: Text.AlignVCenter;
            renderType: Text.NativeRendering;
            visible: widerBaseCheckbox.checked;
            width: Math.ceil(contentWidth)
        }

        UM.TextFieldWithUnit
        {
            id: sizeTextField;
            width: UM.Theme.getSize("setting_control").width/2;
            height: UM.Theme.getSize("setting_control").height;
            property string unit: "mm";
            text: UM.ActiveTool.properties.getValue("SupportSize");
            validator: DoubleValidator
            {
                decimals: 2;
                bottom: 0.1;
                locale: "en_US";
            }
            onEditingFinished:
            {
                var modified_text = text.replace(",", ".");
                UM.ActiveTool.setProperty("SupportSize", modified_text);
            }
        }
        
        UM.TextFieldWithUnit
        {
            id: baseSizeTextField;
            width: UM.Theme.getSize("setting_control").width/2;
            height: UM.Theme.getSize("setting_control").height;
            property string unit: "mm";
            text: UM.ActiveTool.properties.getValue("SupportBaseSize")
            visible: widerBaseCheckbox.checked;
            validator: DoubleValidator
            {
                decimals: 2;
                bottom: 0.1;
                locale: "en_US";
            }
            onEditingFinished:
            {
                var modified_text = text.replace(",", ".");
                UM.ActiveTool.setProperty("SupportBaseSize", modified_text);
            }
        }
    }
}
