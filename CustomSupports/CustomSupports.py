# Copyright (c) 2018 Lokster <http://lokspace.eu>
# Based on the SupportBlocker plugin by Ultimaker B.V., and licensed under LGPLv3 or higher.

IS_QT5 = False
try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import QApplication
except:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtWidgets import QApplication
    IS_QT5 = True

from UM.Math.Vector import Vector
from UM.Tool import Tool
from UM.Event import Event, MouseEvent
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.Selection import Selection

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.PickingPass import PickingPass

from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from cura.Operations.SetParentOperation import SetParentOperation

from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator

from UM.Settings.SettingInstance import SettingInstance
#from UM.Scene.ToolHandle import ToolHandle
from UM.Tool import Tool

import math
import numpy

class CustomSupports(Tool):
    def __init__(self):
        super().__init__()
        self._SupportType = 'cube'
        self._SupportSize = 5.0
        self._SupportBaseSize = 7.5
        self._DropToBuildplate = True
        self._WiderBase = False

        self._shortcut_key = Qt.Key_C if IS_QT5 else Qt.Key.Key_C
        self._controller = self.getController()
        self._selection_pass = None
        self.setExposedProperties("SupportSize", "SupportType", "DropToBuildplate", "SupportBaseSize", "WiderBase")

        CuraApplication.getInstance().globalContainerStackChanged.connect(self._updateEnabled)

        # Note: if the selection is cleared with this tool active, there is no way to switch to
        # another tool than to reselect an object (by clicking it) because the tool buttons in the
        # toolbar will have been disabled. That is why we need to ignore the first press event
        # after the selection has been cleared.
        Selection.selectionChanged.connect(self._onSelectionChanged)
        self._had_selection = False
        self._skip_press = False

        self._had_selection_timer = QTimer()
        self._had_selection_timer.setInterval(0)
        self._had_selection_timer.setSingleShot(True)
        self._had_selection_timer.timeout.connect(self._selectionChangeDelay)
        
        # set the preferences to store the default value
        self._preferences = CuraApplication.getInstance().getPreferences()
        self._preferences.addPreference("customsupports/support_size", 5)
        self._preferences.addPreference("customsupports/support_type", 'cube')
        self._preferences.addPreference("customsupports/support_base_size", 7.5)
        self._preferences.addPreference("customsupports/drop_to_buildplate", True)
        self._preferences.addPreference("customsupports/wider_base", True)
        # convert as float to avoid further issue
        self._SupportSize = float(self._preferences.getValue("customsupports/support_size"))
        self._SupportBaseSize = float(self._preferences.getValue("customsupports/support_base_size"))
        self._SupportType = str(self._preferences.getValue("customsupports/support_type"))
        self._DropToBuildplate = bool(self._preferences.getValue("customsupports/drop_to_buildplate"))
        self._WiderBase = bool(self._preferences.getValue("customsupports/wider_base"))
        
    def event(self, event):
        super().event(event)
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = (
            modifiers & (Qt.ControlModifier if IS_QT5 else Qt.KeyboardModifier.ControlModifier)
        )

        if event.type == Event.MousePressEvent and MouseEvent.LeftButton in event.buttons and self._controller.getToolsEnabled():
            if ctrl_is_active:
                self._controller.setActiveTool("TranslateTool")
                return

            if self._skip_press:
                # The selection was previously cleared, do not add/remove an support mesh but
                # use this click for selection and reactivating this tool only.
                self._skip_press = False
                return

            if self._selection_pass is None:
                # The selection renderpass is used to identify objects in the current view
                self._selection_pass = CuraApplication.getInstance().getRenderer().getRenderPass("selection")
            picked_node = self._controller.getScene().findObject(self._selection_pass.getIdAtPosition(event.x, event.y))
            if not picked_node:
                # There is no slicable object at the picked location
                return

            node_stack = picked_node.callDecoration("getStack")
            if node_stack:
                if node_stack.getProperty("support_mesh", "value"):
                    self._removeSupportMesh(picked_node)
                    return

                elif node_stack.getProperty("anti_overhang_mesh", "value") or node_stack.getProperty("infill_mesh", "value") or node_stack.getProperty("cutting_mesh", "value"):
                    # Only "normal" meshes can have support_mesh added to them
                    return

            # Create a pass for picking a world-space location from the mouse location
            active_camera = self._controller.getScene().getActiveCamera()
            picking_pass = PickingPass(active_camera.getViewportWidth(), active_camera.getViewportHeight())
            picking_pass.render()

            picked_position = picking_pass.getPickedPosition(event.x, event.y)

            # Add the support_mesh cube at the picked location
            self._createSupportMesh(picked_node, picked_position)

    def _createSupportMesh(self, parent: CuraSceneNode, position: Vector):
        node = CuraSceneNode()
        node.setSelectable(True)
        
        if self._SupportType == 'cylinder':
            height = position.y
            node.setName("CustomSupportCylinder")
            mesh = self._createCylinder(self._SupportSize,22.5,height)
            node_position = Vector(position.x,position.y,position.z)
        else:
            node.setName("CustomSupportCube")
            height = position.y-self._SupportSize/2+self._SupportSize*0.1
            mesh =  self._createCube(self._SupportSize,height)
            node_position = Vector(position.x,position.y-self._SupportSize/2+self._SupportSize*0.1,position.z)
        node.setMeshData(mesh.build())

        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        node.addDecorator(BuildPlateDecorator(active_build_plate))
        node.addDecorator(SliceableObjectDecorator())

        stack = node.callDecoration("getStack") # created by SettingOverrideDecorator that is automatically added to CuraSceneNode
        settings = stack.getTop()

        for key in ["support_mesh", "support_mesh_drop_down"]:
            definition = stack.getSettingDefinition(key)
            new_instance = SettingInstance(definition, settings)
            new_instance.setProperty("value", True)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            settings.addInstance(new_instance)

        op = GroupedOperation()
        # First add node to the scene at the correct position/scale, before parenting, so the support mesh does not get scaled with the parent
        op.addOperation(AddSceneNodeOperation(node, self._controller.getScene().getRoot()))
        op.addOperation(SetParentOperation(node, parent))
        op.push()
        node.setPosition(node_position, CuraSceneNode.TransformSpace.World)

        CuraApplication.getInstance().getController().getScene().sceneChanged.emit(node)

    def _removeSupportMesh(self, node: CuraSceneNode):
        parent = node.getParent()
        if parent == self._controller.getScene().getRoot():
            parent = None

        op = RemoveSceneNodeOperation(node)
        op.push()

        if parent and not Selection.isSelected(parent):
            Selection.add(parent)

        CuraApplication.getInstance().getController().getScene().sceneChanged.emit(node)

    def _updateEnabled(self):
        plugin_enabled = False

        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if global_container_stack:
            plugin_enabled = global_container_stack.getProperty("support_mesh", "enabled")

        CuraApplication.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, plugin_enabled)

    def _onSelectionChanged(self):
        # When selection is passed from one object to another object, first the selection is cleared
        # and then it is set to the new object. We are only interested in the change from no selection
        # to a selection or vice-versa, not in a change from one object to another. A timer is used to
        # "merge" a possible clear/select action in a single frame
        if Selection.hasSelection() != self._had_selection:
            self._had_selection_timer.start()

    def _selectionChangeDelay(self):
        has_selection = Selection.hasSelection()
        if not has_selection and self._had_selection:
            self._skip_press = True
        else:
            self._skip_press = False

        self._had_selection = has_selection

    def _createCube(self, size, height):
        mesh = MeshBuilder()

        # Can't use MeshBuilder.addCube() because that does not get per-vertex normals
        # Per-vertex normals require duplication of vertices
        s = size / 2
        l = height
        #s_inf=math.tan(math.radians(dep))*l+s
        if self._WiderBase:
            base_size = self._SupportBaseSize/2
        else:
            base_size = s
        if self._DropToBuildplate:
            verts = [ # 6 faces with 4 corners each
                [-base_size, -l,  base_size], [-s,  s,  s], [ s,  s,  s], [ base_size, -l,  base_size],
                [-s,  s, -s], [-base_size, -l, -base_size], [ base_size, -l, -base_size], [ s,  s, -s],
                [ base_size, -l, -base_size], [-base_size, -l, -base_size], [-base_size, -l,  base_size], [ base_size, -l,  base_size],
                [-s,  s, -s], [ s,  s, -s], [ s,  s,  s], [-s,  s,  s],
                [-base_size, -l,  base_size], [-base_size, -l, -base_size], [-s,  s, -s], [-s,  s,  s],
                [ base_size, -l, -base_size], [ base_size, -l,  base_size], [ s,  s,  s], [ s,  s, -s]
            ]
        else:
            verts = [ # 6 faces with 4 corners each
                [-s, -s,  s], [-s,  s,  s], [ s,  s,  s], [ s, -s,  s],
                [-s,  s, -s], [-s, -s, -s], [ s, -s, -s], [ s,  s, -s],
                [ s, -s, -s], [-s, -s, -s], [-s, -s,  s], [ s, -s,  s],
                [-s,  s, -s], [ s,  s, -s], [ s,  s,  s], [-s,  s,  s],
                [-s, -s,  s], [-s, -s, -s], [-s,  s, -s], [-s,  s,  s],
                [ s, -s, -s], [ s, -s,  s], [ s,  s,  s], [ s,  s, -s]
            ]
        mesh.setVertices(numpy.asarray(verts, dtype=numpy.float32))

        indices = []
        for i in range(0, 24, 4): # All 6 quads (12 triangles)
            indices.append([i, i+2, i+1])
            indices.append([i, i+3, i+2])
        mesh.setIndices(numpy.asarray(indices, dtype=numpy.int32))

        mesh.calculateNormals()
        return mesh
	
    def _createCylinder(self, size, nb , height):
        mesh = MeshBuilder()
        # Per-vertex normals require duplication of vertices
        r = size / 2
        # additionale length
        sup = size * 0.1
        l = -height
        rng = int(360 / nb)
        ang = math.radians(nb)
        verts = []
        
        if self._WiderBase:
            r_base = self._SupportBaseSize/2
        else:
            r_base = r

        if self._DropToBuildplate:
            for i in range(0, rng):
                # Top
                verts.append([0, sup, 0])
                verts.append([r*math.cos((i+1)*ang), sup, r*math.sin((i+1)*ang)])
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                #Side 1a
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                verts.append([r*math.cos((i+1)*ang), sup, r*math.sin((i+1)*ang)])
                verts.append([r_base*math.cos((i+1)*ang), l, r_base*math.sin((i+1)*ang)])
                #Side 1b
                verts.append([r_base*math.cos((i+1)*ang), l, r_base*math.sin((i+1)*ang)])
                verts.append([r_base*math.cos(i*ang), l, r_base*math.sin(i*ang)])
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                #Bottom 
                verts.append([0, l, 0])
                verts.append([r_base*math.cos((i+1)*ang), l, r_base*math.sin((i+1)*ang)]) 
                verts.append([r_base*math.cos(i*ang), l, r_base*math.sin(i*ang)])
        else:
            for i in range(0, rng):
                # Top
                verts.append([0, sup, 0])
                verts.append([r*math.cos((i+1)*ang), sup, r*math.sin((i+1)*ang)])
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                #Side 1a
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                verts.append([r*math.cos((i+1)*ang), sup, r*math.sin((i+1)*ang)])
                verts.append([r*math.cos((i+1)*ang), -size, r*math.sin((i+1)*ang)])
                #Side 1b
                verts.append([r*math.cos((i+1)*ang), -size, r*math.sin((i+1)*ang)])
                verts.append([r*math.cos(i*ang), -size, r*math.sin(i*ang)])
                verts.append([r*math.cos(i*ang), sup, r*math.sin(i*ang)])
                #Bottom 
                verts.append([0, -size, 0])
                verts.append([r*math.cos((i+1)*ang), -size, r*math.sin((i+1)*ang)]) 
                verts.append([r*math.cos(i*ang), -size, r*math.sin(i*ang)])
        
        
        mesh.setVertices(numpy.asarray(verts, dtype=numpy.float32))
        indices = []
        # for every angle increment 12 Vertices
        tot = rng * 12
        for i in range(0, tot, 3): # 
            indices.append([i, i+1, i+2])
        mesh.setIndices(numpy.asarray(indices, dtype=numpy.int32))
        mesh.calculateNormals()
        return mesh
    
    def getSupportSize(self) -> float:
        return self._SupportSize
  
    def setSupportSize(self, SupportSize: str) -> None:
        try:
            s_value = float(SupportSize)
        except ValueError:
            return

        if s_value <= 0:
            return
        self._SupportSize = s_value
        self._preferences.setValue("customsupports/support_size", s_value)

    def getSupportBaseSize(self) -> float:
        return self._SupportBaseSize
  
    def setSupportBaseSize(self, SupportBaseSize: str) -> None:
        try:
            s_value = float(SupportBaseSize)
        except ValueError:
            return

        if s_value <= 0:
            return
        self._SupportBaseSize = s_value
        self._preferences.setValue("customsupports/support_base_size", s_value)

    def setWiderBase (self, WiderBase: bool) -> None:
        self._WiderBase = WiderBase
        self._preferences.setValue("customsupports/wider_base", WiderBase)
    
    def getWiderBase(self) -> bool:
        return self._WiderBase
    
    def getDropToBuildplate(self) -> bool:
        return self._DropToBuildplate
    
    def setDropToBuildplate(self, DropToBuildplate: bool) -> None:
        self._DropToBuildplate = DropToBuildplate
        self._preferences.setValue("customsupports/drop_to_buildplate", DropToBuildplate)
        
    def getSupportType(self) -> str:
        return self._SupportType
    
    def setSupportType(self, SupportType: str) -> None:
        self._SupportType = SupportType
        self._preferences.setValue("customsupports/support_type", SupportType)
