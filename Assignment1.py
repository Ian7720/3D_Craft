from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys
import vtk
from PyQt5 import QtCore, QtWidgets
from vtkmodules.util.colors import tomato, banana, orange, green
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QLineEdit
from PyQt5.QtWidgets import QColorDialog
import os

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)
        self.AddObserver("MouseMoveEvent", self.mouse_move_event)
        self.shift_pressed = False
        self.right_button_pressed = False

    def right_button_press_event(self, obj, event):
        if self.GetInteractor().GetShiftKey():
            self.shift_pressed = True
            self.right_button_pressed = True
            self.OnMiddleButtonDown()  # Treat as middle button down for panning
        else:
            self.OnRightButtonDown()
        return

    def right_button_release_event(self, obj, event):
        if self.shift_pressed and self.right_button_pressed:
            self.shift_pressed = False
            self.right_button_pressed = False
            self.OnMiddleButtonUp()  # Treat as middle button up for panning
        else:
            self.OnRightButtonUp()
        return

    def mouse_move_event(self, obj, event):
        if self.shift_pressed and self.right_button_pressed:
            self.OnMouseMove()  # Continue panning
        else:
            self.OnMouseMove()
        return

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_main_layout()
        self.setup_side_frame()
        
        self.texture_file_name = None
        
        # Create the main layout and add both frames
        self.central_layout = QHBoxLayout()
        self.central_layout.addWidget(self.main_frame)
        self.central_layout.addWidget(self.side_frame)
        
        self.central_layout.setStretch(0, 3)  # Main frame stretch factor
        self.central_layout.setStretch(1, 1)  # Side frame stretch factor
        
        # Set the central widget
        central_widget = QWidget()
        central_widget.setLayout(self.central_layout)
        self.setCentralWidget(central_widget)
        
        self.create_menu()
        self.show()
        
        self.iren.Initialize()
        
        # List to keep track of loaded models
        self.loaded_models = []
        
        # List to store model details
        self.model_details_list = []
        
        # Set the custom interactor style
        self.style = CustomInteractorStyle()
        self.style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(self.style)
        #self.iren.Start()
        
        self.add_3d_grid()
        
    def setup_main_layout(self):
        # Create the main frame
        self.main_frame = QFrame()
        self.main_layout = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.main_frame)
        self.main_layout.addWidget(self.vtkWidget)
        
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        self.main_frame.setLayout(self.main_layout)
    
    def setup_side_frame(self):
        # Create the side frame
        self.side_frame = QFrame()
        self.side_layout = QVBoxLayout()
        self.model_list_widget = QListWidget()
        self.side_layout.addWidget(self.model_list_widget)
        
        # Create a vertical layout for the new section
        self.bottom_layout = QVBoxLayout()

        # Create a label to display the model number
        self.model_number_label = QLabel()
        self.model_number_label.setAlignment(QtCore.Qt.AlignCenter)
        self.bottom_layout.addWidget(self.model_number_label)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Create buttons
        self.btn_transformation = QPushButton("Transformation")
        self.btn_transformation.clicked.connect(self.show_transformation_panel)
        self.btn_colour = QPushButton("Colour")
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_model)
        self.btn_texture = QPushButton("Texture")
        self.btn_texture.clicked.connect(self.show_texture_panel)
        self.btn_close = QPushButton("Close")

        # Set fixed size for buttons
        button_size = QtCore.QSize(100, 30)  # Adjust the size as needed
        self.btn_transformation.setFixedSize(button_size)
        self.btn_colour.setFixedSize(button_size)
        self.btn_save.setFixedSize(button_size)
        self.btn_texture.setFixedSize(button_size)
        self.btn_close.setFixedSize(button_size)

        # Add buttons to the vertical layout
        button_layout.addWidget(self.btn_transformation)
        button_layout.addWidget(self.btn_colour)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_texture)
        button_layout.addWidget(self.btn_close)

        # Add a spacer to push the buttons to the top
        button_layout.addStretch()

        # Add the button layout to the bottom layout
        self.bottom_layout.addLayout(button_layout)

        # Create a vertical layout for the details
        self.details_layout = QVBoxLayout()

        # Create a label to display model details
        self.details_label = QLabel()
        self.details_label.setWordWrap(True)

        # Add the label to the details layout
        self.details_layout.addWidget(self.details_label)

        # Add a spacer to push the label to the top
        self.details_layout.addStretch()

        # Add the details layout to the bottom layout
        self.bottom_layout.addLayout(self.details_layout)

        # Create a color picker
        self.color_picker = QColorDialog()

        # Add the color picker to the details layout
        self.details_layout.addWidget(self.color_picker)

        # Hide the color picker initially
        self.color_picker.hide()

        # Define the function to show the color picker
        def show_color_picker():
            self.color_picker.show()
            self.details_label.hide()

        # Connect the Colour button to the show_color_picker function
        self.btn_colour.clicked.connect(show_color_picker)

        # Define the function to apply the selected color
        def apply_color():
            model_number = self.current_model_number
            color = self.color_picker.currentColor()
            if color.isValid():
                actor = self.loaded_models[model_number - 1]
                r, g, b, _ = color.getRgbF()
                actor.GetProperty().SetColor(r, g, b)
                self.vtkWidget.GetRenderWindow().Render()

        # Override the default behavior of the OK button
        def on_color_picker_accepted():
            apply_color()
            self.color_picker.show()  # Ensure the color picker remains visible

        # Connect the OK button of the color picker to the custom function
        self.color_picker.accepted.connect(on_color_picker_accepted)

        # Define the function to hide the color picker
        def hide_color_picker():
            self.color_picker.hide()

        # Connect the Cancel button of the color picker to the hide_color_picker function
        self.color_picker.rejected.connect(hide_color_picker)

        # Connect other buttons to hide the color picker
        self.btn_transformation.clicked.connect(hide_color_picker)
        self.btn_save.clicked.connect(hide_color_picker)
        self.btn_texture.clicked.connect(lambda: (hide_color_picker()))
        self.btn_close.clicked.connect(lambda: self.hide_edit_panel(self.current_model_number))

        # Initially hide the bottom layout
        self.bottom_layout_widget = QWidget()
        self.bottom_layout_widget.setLayout(self.bottom_layout)
        self.bottom_layout_widget.hide()
        self.side_layout.addWidget(self.bottom_layout_widget)

        self.side_frame.setLayout(self.side_layout)
        
        # Initialize the transformation panel
        self.transformation_layout = QVBoxLayout()
        self.transformation_panel_widget = QWidget()
        self.transformation_panel_widget.setLayout(self.transformation_layout)
        self.transformation_panel_widget.hide()
        self.side_layout.addWidget(self.transformation_panel_widget)
        
        # Initialize the texture panel
        self.texture_layout = QVBoxLayout()
        self.texture_panel_widget = QWidget()
        self.texture_panel_widget.setLayout(self.texture_layout)
        self.texture_panel_widget.hide()
        self.side_layout.addWidget(self.texture_panel_widget)
        
    def show_edit_panel(self, model_number):
        self.current_model_number = model_number
        self.model_number_label.setText(f"Model {model_number}")
        # Show the transformation panel when a model is selected for editing
        self.transformation_panel_widget.show()
        # Show the texture panel when a model is selected for editing
        self.texture_panel_widget.show()
        self.bottom_layout_widget.show()
        
    def hide_edit_panel(self, model_number):
        self.transformation_panel_widget.hide()
        # Hide the texture panel when editing is done or canceled
        self.texture_panel_widget.hide()
        self.bottom_layout_widget.hide()
    
    def create_menu(self):
        menuBar = self.menuBar()
        file_menu = menuBar.addMenu("File")
        design_menu = menuBar.addMenu("Design")
        geometry_menu = QMenu("Geometry", self)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file_dialog)
        save_action = QAction("Save",self)
        save_action.triggered.connect(self.save_window)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        
        cuboid_action = QAction("Cuboid", self)
        sphere_action = QAction("Sphere", self)
        cone_action = QAction("Cone", self)
        cylinder_action = QAction("Cylinder", self)
        prism_action = QAction("Prism", self)
                      
        geometry_menu.addAction(cuboid_action)
        geometry_menu.addAction(sphere_action)
        geometry_menu.addAction(cone_action)
        geometry_menu.addAction(cylinder_action)
        geometry_menu.addAction(prism_action)
        
        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self.reset)
        lighting_action = QAction("Lighting", self)
        lighting_action.triggered.connect(self.show_lighting_dialog)
        background_action = QAction("Background Colour", self)
        
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)
        
        design_menu.addAction(reset_action)
        design_menu.addAction(lighting_action)
        design_menu.addAction(background_action)
        design_menu.addMenu(geometry_menu)
        
        def create_prism_dialog(self):
            # Create a new dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Prism")
            dialog.setMinimumSize(300, 200)

            # Create a vertical layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create input fields for the prism variables
            base_label = QLabel("Base Length:")
            base_input = QLineEdit()
            height_label = QLabel("Height:")
            height_input = QLineEdit()
            depth_label = QLabel("Depth:")
            depth_input = QLineEdit()

            # Add input fields to the layout
            layout.addWidget(base_label)
            layout.addWidget(base_input)
            layout.addWidget(height_label)
            layout.addWidget(height_input)
            layout.addWidget(depth_label)
            layout.addWidget(depth_input)

            # Create OK and Cancel buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Define the function to create the prism
            def create_prism():
                base_length = float(base_input.text())
                height = float(height_input.text())
                depth = float(depth_input.text())

                # Define the vertices of the triangular prism
                points = vtk.vtkPoints()
                points.InsertNextPoint(0, 0, 0)
                points.InsertNextPoint(base_length, 0, 0)
                points.InsertNextPoint(base_length / 2, height, 0)
                points.InsertNextPoint(0, 0, depth)
                points.InsertNextPoint(base_length, 0, depth)
                points.InsertNextPoint(base_length / 2, height, depth)

                # Define the faces of the triangular prism
                faces = vtk.vtkCellArray()
                faces.InsertNextCell(3)
                faces.InsertCellPoint(0)
                faces.InsertCellPoint(1)
                faces.InsertCellPoint(2)
                faces.InsertNextCell(3)
                faces.InsertCellPoint(3)
                faces.InsertCellPoint(4)
                faces.InsertCellPoint(5)
                faces.InsertNextCell(4)
                faces.InsertCellPoint(0)
                faces.InsertCellPoint(1)
                faces.InsertCellPoint(4)
                faces.InsertCellPoint(3)
                faces.InsertNextCell(4)
                faces.InsertCellPoint(1)
                faces.InsertCellPoint(2)
                faces.InsertCellPoint(5)
                faces.InsertCellPoint(4)
                faces.InsertNextCell(4)
                faces.InsertCellPoint(2)
                faces.InsertCellPoint(0)
                faces.InsertCellPoint(3)
                faces.InsertCellPoint(5)

                # Create the triangular prism using vtkPolyData
                prism = vtk.vtkPolyData()
                prism.SetPoints(points)
                prism.SetPolys(faces)

                # Create a mapper and actor for the prism
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(prism)

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(1, 1, 1)  # Default color: white

                # Add the prism to the renderer
                self.ren.AddActor(actor)
                self.ren.ResetCamera()
                self.vtkWidget.GetRenderWindow().Render()

                # Add the prism details to the model list
                model_number = len(self.loaded_models) + 1
                self.loaded_models.append(actor)
                self.model_details_list.append({
                    "file_name": f"Prism {model_number}",
                    "num_points": prism.GetNumberOfPoints(),
                    "num_polys": prism.GetNumberOfPolys(),
                    "num_surfaces": prism.GetNumberOfCells()
                })
                self.add_model_details(model_number, f"Prism {model_number}", prism.GetNumberOfPoints(), prism.GetNumberOfPolys(), prism.GetNumberOfCells())

                # Close the dialog
                dialog.accept()

            # Connect the OK button to the create_prism function
            ok_button.clicked.connect(create_prism)

            # Connect the Cancel button to close the dialog
            cancel_button.clicked.connect(dialog.reject)

            # Show the dialog
            dialog.exec_()
            
        def create_cuboid_dialog(self):
            # Create a new dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Cuboid")
            dialog.setMinimumSize(300, 200)

            # Create a vertical layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create input fields for the prism variables
            base_label = QLabel("Base Length:")
            base_input = QLineEdit()
            height_label = QLabel("Height:")
            height_input = QLineEdit()
            width_label = QLabel("Width:")
            width_input = QLineEdit()

            # Add input fields to the layout
            layout.addWidget(base_label)
            layout.addWidget(base_input)
            layout.addWidget(height_label)
            layout.addWidget(height_input)
            layout.addWidget(width_label)
            layout.addWidget(width_input)

            # Create OK and Cancel buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Define the function to create the prism
            def create_cuboid():
                base_length = float(base_input.text())
                height = float(height_input.text())
                width = float(width_input.text())

                # Create the prism using VTK
                cuboid = vtk.vtkCubeSource()
                cuboid.SetXLength(base_length)
                cuboid.SetYLength(width)
                cuboid.SetZLength(height)
                cuboid.Update()

                # Create a mapper and actor for the prism
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(cuboid.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(1, 1, 1)  # Default color: white

                # Add the prism to the renderer
                self.ren.AddActor(actor)
                self.ren.ResetCamera()
                self.vtkWidget.GetRenderWindow().Render()

                # Add the prism details to the model list
                model_number = len(self.loaded_models) + 1
                self.loaded_models.append(actor)
                self.model_details_list.append({
                    "file_name": f"Cuboid {model_number}",
                    "num_points": cuboid.GetOutput().GetNumberOfPoints(),
                    "num_polys": cuboid.GetOutput().GetNumberOfPolys(),
                    "num_surfaces": cuboid.GetOutput().GetNumberOfCells()
                })
                self.add_model_details(model_number, f"Cuboid {model_number}", cuboid.GetOutput().GetNumberOfPoints(), cuboid.GetOutput().GetNumberOfPolys(), cuboid.GetOutput().GetNumberOfCells())

                # Close the dialog
                dialog.accept()

            # Connect the OK button to the create_prism function
            ok_button.clicked.connect(create_cuboid)

            # Connect the Cancel button to close the dialog
            cancel_button.clicked.connect(dialog.reject)

            # Show the dialog
            dialog.exec_()
            
        def create_sphere_dialog(self):
            # Create a new dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Sphere")
            dialog.setMinimumSize(300, 200)

            # Create a vertical layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create input fields for the prism variables
            radius_label = QLabel("Radius:")
            radius_input = QLineEdit()
            theta_label = QLabel("Theta Resolution:")
            theta_input = QLineEdit()
            phi_label = QLabel("Phi Resolution:")
            phi_input = QLineEdit()

            # Add input fields to the layout
            layout.addWidget(radius_label)
            layout.addWidget(radius_input)
            layout.addWidget(theta_label)
            layout.addWidget(theta_input)
            layout.addWidget(phi_label)
            layout.addWidget(phi_input)

            # Create OK and Cancel buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Define the function to create the sphere
            def create_sphere():
                radius = float(radius_input.text())
                theta = int(float(theta_input.text()))
                phi = int(float(phi_input.text()))

                # Create the sphere using VTK
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(radius)
                sphere.SetThetaResolution(theta)
                sphere.SetPhiResolution(phi)
                sphere.Update()

                # Create a mapper and actor for the sphere
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(sphere.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(1, 1, 1)  # Default color: white

                # Add the sphere to the renderer
                self.ren.AddActor(actor)
                self.ren.ResetCamera()
                self.vtkWidget.GetRenderWindow().Render()

                # Add the sphere details to the model list
                model_number = len(self.loaded_models) + 1
                self.loaded_models.append(actor)
                self.model_details_list.append({
                    "file_name": f"Sphere {model_number}",
                    "num_points": sphere.GetOutput().GetNumberOfPoints(),
                    "num_polys": sphere.GetOutput().GetNumberOfPolys(),
                    "num_surfaces": sphere.GetOutput().GetNumberOfCells()
                })
                self.add_model_details(model_number, f"Sphere {model_number}", sphere.GetOutput().GetNumberOfPoints(), sphere.GetOutput().GetNumberOfPolys(), sphere.GetOutput().GetNumberOfCells())

                # Close the dialog
                dialog.accept()

            # Connect the OK button to the create_sphere function
            ok_button.clicked.connect(create_sphere)

            # Connect the Cancel button to close the dialog
            cancel_button.clicked.connect(dialog.reject)

            # Show the dialog
            dialog.exec_()
            
        def create_cone_dialog(self):
            # Create a new dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Cone")
            dialog.setMinimumSize(300, 200)

            # Create a vertical layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create input fields for the prism variables
            radius_label = QLabel("Radius:")
            radius_input = QLineEdit()
            height_label = QLabel("Height:")
            height_input = QLineEdit()
            re_label = QLabel("Resolution:")
            re_input = QLineEdit()

            # Add input fields to the layout
            layout.addWidget(radius_label)
            layout.addWidget(radius_input)
            layout.addWidget(height_label)
            layout.addWidget(height_input)
            layout.addWidget(re_label)
            layout.addWidget(re_input)

            # Create OK and Cancel buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Define the function to create the sphere
            def create_cone():
                radius = float(radius_input.text())
                height = int(float(height_input.text()))
                re = int(float(re_input.text()))

                # Create the cone using VTK
                cone = vtk.vtkConeSource()
                cone.SetRadius(radius)
                cone.SetHeight(height)
                cone.SetResolution(re)
                cone.Update()

                # Create a mapper and actor for the cone
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(cone.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(1, 1, 1)  # Default color: white

                # Add the cone to the renderer
                self.ren.AddActor(actor)
                self.ren.ResetCamera()
                self.vtkWidget.GetRenderWindow().Render()

                # Add the cone details to the model list
                model_number = len(self.loaded_models) + 1
                self.loaded_models.append(actor)
                self.model_details_list.append({
                    "file_name": f"Cone {model_number}",
                    "num_points": cone.GetOutput().GetNumberOfPoints(),
                    "num_polys": cone.GetOutput().GetNumberOfPolys(),
                    "num_surfaces": cone.GetOutput().GetNumberOfCells()
                })
                self.add_model_details(model_number, f"Cone {model_number}", cone.GetOutput().GetNumberOfPoints(), cone.GetOutput().GetNumberOfPolys(), cone.GetOutput().GetNumberOfCells())

                # Close the dialog
                dialog.accept()

            # Connect the OK button to the create_cone function
            ok_button.clicked.connect(create_cone)

            # Connect the Cancel button to close the dialog
            cancel_button.clicked.connect(dialog.reject)

            # Show the dialog
            dialog.exec_()
            
        def create_cylinder_dialog(self):
            # Create a new dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Cylinder")
            dialog.setMinimumSize(300, 200)

            # Create a vertical layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create input fields for the cylinder variables
            radius_label = QLabel("Radius:")
            radius_input = QLineEdit()
            height_label = QLabel("Height:")
            height_input = QLineEdit()
            re_label = QLabel("Resolution:")
            re_input = QLineEdit()

            # Add input fields to the layout
            layout.addWidget(radius_label)
            layout.addWidget(radius_input)
            layout.addWidget(height_label)
            layout.addWidget(height_input)
            layout.addWidget(re_label)
            layout.addWidget(re_input)

            # Create OK and Cancel buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
    
            # Define the function to create the cylinder
            def create_cylinder():
                radius = float(radius_input.text())
                height = float(height_input.text())
                re = int(float(re_input.text()))

                # Create the cylinder using VTK
                cylinder = vtk.vtkCylinderSource()
                cylinder.SetRadius(radius)
                cylinder.SetHeight(height)
                cylinder.SetResolution(re)
                cylinder.Update()

                # Create a mapper and actor for the cylinder
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(cylinder.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(1, 1, 1)  # Default color: white

                # Add the cylinder to the renderer
                self.ren.AddActor(actor)
                self.ren.ResetCamera()
                self.vtkWidget.GetRenderWindow().Render()

                # Add the cylinder details to the model list
                model_number = len(self.loaded_models) + 1
                self.loaded_models.append(actor)
                self.model_details_list.append({
                    "file_name": f"Cylinder {model_number}",
                    "num_points": cylinder.GetOutput().GetNumberOfPoints(),
                    "num_polys": cylinder.GetOutput().GetNumberOfPolys(),
                    "num_surfaces": cylinder.GetOutput().GetNumberOfCells()
                })
                self.add_model_details(model_number, f"Cylinder {model_number}", cylinder.GetOutput().GetNumberOfPoints(), cylinder.GetOutput().GetNumberOfPolys(), cylinder.GetOutput().GetNumberOfCells())

                # Close the dialog
                dialog.accept()

            # Connect the OK button to the create_cylinder function
            ok_button.clicked.connect(create_cylinder)

            # Connect the Cancel button to close the dialog
            cancel_button.clicked.connect(dialog.reject)

            # Show the dialog
            dialog.exec_()
            
        def change_background_color(self):
            # Open a color picker dialog
            color = QColorDialog.getColor()

            # Check if a valid color is selected
            if color.isValid():
                # Convert the QColor to RGB values
                r, g, b, _ = color.getRgbF()

                # Set the background color of the VTK renderer
                self.ren.SetBackground(r, g, b)
                self.vtkWidget.GetRenderWindow().Render()

        # Connect the background_action to the change_background_color function
        background_action.triggered.connect(lambda: change_background_color(self))
            
        # Connect the prism_action to the create_prism_dialog function
        prism_action.triggered.connect(lambda: create_prism_dialog(self))
        
        # Connect the cuboid_action to the create_cuboid_dialog function
        cuboid_action.triggered.connect(lambda: create_cuboid_dialog(self))
        
        # Connect the sphere_action to the create_sphere_dialog function
        sphere_action.triggered.connect(lambda: create_sphere_dialog(self))
        
        # Connect the cone_action to the create_cone_dialog function
        cone_action.triggered.connect(lambda: create_cone_dialog(self))
        
        # Connect the cylinder_action to the create_cylinder_dialog function
        cylinder_action.triggered.connect(lambda: create_cylinder_dialog(self))
        
        
    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;VTK Files (*.vtk)", options=options)
        if file_name:
            self.load_file(file_name)
            
    def load_file(self, file_name):
        # Determine the appropriate reader based on the file extension
        extension = os.path.splitext(file_name)[1].lower()

        if extension == ".vtk":
            reader = vtk.vtkPolyDataReader()
        elif extension == ".obj":
            reader = vtk.vtkOBJReader()
        elif extension == ".ply":
            reader = vtk.vtkPLYReader()
        elif extension == ".stl":
            reader = vtk.vtkSTLReader()
        else:
            QMessageBox.warning(self, "Error", f"Unsupported file format: {extension}")
            return

        reader.SetFileName(file_name)
        reader.Update()

        # Create a mapper and actor for the loaded model
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(green)
        
        # Position the actor to avoid stacking
        position_offset = len(self.loaded_models) * 0.5  # Adjust the offset as needed
        actor.SetPosition(position_offset, 0, 0)

        # Clear previous actors and add the new one
        #self.ren.RemoveAllViewProps()
        self.ren.AddActor(actor)
        self.ren.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
        
        # Extract model details
        poly_data = reader.GetOutput()
        num_points = poly_data.GetNumberOfPoints()
        num_polys = poly_data.GetNumberOfPolys()
        num_surfaces = poly_data.GetNumberOfCells()
        
         # Calculate model number before appending to the list
        model_number = len(self.loaded_models) + 1  # Model number based on the count of loaded models
        
        # Add model details to the QListWidget
        self.add_model_details(model_number, file_name, num_points, num_polys, num_surfaces)
        
        # Keep track of the loaded model
        self.loaded_models.append(actor)
        
        # Store model details
        self.model_details_list.append({
            "file_name": file_name,
            "num_points": num_points,
            "num_polys": num_polys,
            "num_surfaces": num_surfaces
            })
        
    def add_model_details(self, model_number, file_name, num_points, num_polys, num_surfaces):
        # Create a container widget
        container_widget = QWidget()
        layout = QHBoxLayout()
        
        # Create a label for the model details
        model_details = f"Model {model_number}: {os.path.basename(file_name)}\n"
        model_details += f"Points: {num_points}, Polygons: {num_polys}, Surfaces: {num_surfaces}"
        label = QLabel(model_details)
        
        # Create a button with an icon
        button_1 = QPushButton()
        icon_1 = QIcon(r"D:/UMS/SEM7/SDV/Assignment1/icon/888_edit.jpg")  # Replace with the path to your icon file
        button_1.setIcon(icon_1)
        button_1.clicked.connect(lambda: self.show_edit_panel(model_number))
        
        button_2 = QPushButton()
        icon_2 = QIcon(r"D:/UMS/SEM7/SDV/Assignment1/icon/pngtree-premium-simple-trash-icon-delete-png-image_12503501.png")  # Replace with the path to your icon file
        button_2.setIcon(icon_2)
        button_2.clicked.connect(lambda: self.delete_model(model_number))
        
        # Add the label and button to the layout
        layout.addWidget(label)
        layout.addWidget(button_1)
        layout.addWidget(button_2)
        
        # Set the layout for the container widget
        container_widget.setLayout(layout)
        
        # Add the container widget to the QListWidget
        item = QListWidgetItem()
        item.setSizeHint(container_widget.sizeHint())
        self.model_list_widget.addItem(item)
        self.model_list_widget.setItemWidget(item, container_widget)
                
    def delete_model(self, model_number):
        # Find the actor corresponding to the model number
        actor = self.loaded_models[model_number - 1]
    
        # Remove the actor from the renderer
        self.ren.RemoveActor(actor)
        self.vtkWidget.GetRenderWindow().Render()
    
        # Remove the actor from the loaded models list
        self.loaded_models.pop(model_number - 1)
    
        # Remove the corresponding item from the QListWidget
        self.model_list_widget.takeItem(model_number - 1)
    
        # Remove the model details from the list
        self.model_details_list.pop(model_number - 1)
    
        # Update the remaining model numbers in the QListWidget
        for i in range(self.model_list_widget.count()):
            item = self.model_list_widget.item(i)
            widget = self.model_list_widget.itemWidget(item)
            label = widget.findChild(QLabel)
            details = self.model_details_list[i]
            label.setText(f"Model {i + 1}: {os.path.basename(details['file_name'])}\n"
                          f"Points: {details['num_points']}, Polygons: {details['num_polys']}, Surfaces: {details['num_surfaces']}")
            
        # Check if the side frame should be hidden
        if hasattr(self, 'current_model_number') and self.current_model_number is not None:
            if self.current_model_number == model_number:
                self.bottom_layout_widget.hide()
                self.current_model_number = None
            elif self.current_model_number > model_number:
                self.current_model_number -= 1
                
    def add_3d_grid(self):
        # Create axes
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(1.5, 1.5, 1.5)
        axes.GetXAxisShaftProperty().SetColor(1, 0, 0)  # X axis in red
        axes.GetYAxisShaftProperty().SetColor(0, 1, 0)  # Y axis in green
        axes.GetZAxisShaftProperty().SetColor(0, 0, 1)  # Z axis in blue
        self.ren.AddActor(axes)
        
        # Create a grid
        grid = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        
        # Define grid size and spacing
        grid_size = 10
        spacing = 1.0
        
        # Create grid points and lines for the XY plane
        for i in range(-grid_size, grid_size + 1):
            points.InsertNextPoint(i * spacing, -grid_size * spacing, 0)
            points.InsertNextPoint(i * spacing, grid_size * spacing, 0)
            points.InsertNextPoint(-grid_size * spacing, i * spacing, 0)
            points.InsertNextPoint(grid_size * spacing, i * spacing, 0)
            
            lines.InsertNextCell(2)
            lines.InsertCellPoint(4 * (i + grid_size))
            lines.InsertCellPoint(4 * (i + grid_size) + 1)
            
            lines.InsertNextCell(2)
            lines.InsertCellPoint(4 * (i + grid_size) + 2)
            lines.InsertCellPoint(4 * (i + grid_size) + 3)
        
        grid.SetPoints(points)
        grid.SetLines(lines)
        
        # Create a mapper and actor for the grid
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(grid)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Light gray color
        
        # Add the grid to the renderer
        self.ren.AddActor(actor)
        
    def show_transformation_panel(self):
        # Check if the transformation panel is already created
        if not hasattr(self, 'transformation_panel_initialized') or not self.transformation_panel_initialized:
            # Create input fields for translation
            translate_label = QLabel("Translate (x, y, z):")
            translate_layout = QHBoxLayout()
            self.translate_x_input = QLineEdit()
            self.translate_y_input = QLineEdit()
            self.translate_z_input = QLineEdit()
            translate_layout.addWidget(self.translate_x_input)
            translate_layout.addWidget(self.translate_y_input)
            translate_layout.addWidget(self.translate_z_input)
            
            # Create input fields for rotation
            rotate_label = QLabel("Rotate (x, y, z):")
            rotate_layout = QHBoxLayout()
            self.rotate_x_input = QLineEdit()
            self.rotate_y_input = QLineEdit()
            self.rotate_z_input = QLineEdit()
            rotate_layout.addWidget(self.rotate_x_input)
            rotate_layout.addWidget(self.rotate_y_input)
            rotate_layout.addWidget(self.rotate_z_input)
            
            # Create input fields for scaling
            scale_label = QLabel("Scale (x, y, z):")
            scale_layout = QHBoxLayout()
            self.scale_x_input = QLineEdit()
            self.scale_y_input = QLineEdit()
            self.scale_z_input = QLineEdit()
            scale_layout.addWidget(self.scale_x_input)
            scale_layout.addWidget(self.scale_y_input)
            scale_layout.addWidget(self.scale_z_input)
            
            # Add input fields to the transformation layout
            self.transformation_layout.addWidget(translate_label)
            self.transformation_layout.addLayout(translate_layout)
            self.transformation_layout.addWidget(rotate_label)
            self.transformation_layout.addLayout(rotate_layout)
            self.transformation_layout.addWidget(scale_label)
            self.transformation_layout.addLayout(scale_layout)
            
            # Create Apply and Cancel buttons
            button_layout = QHBoxLayout()
            apply_button = QPushButton("Apply")
            cancel_button = QPushButton("Cancel")
            
            # Define the function to apply the transformation
            def apply_transformation():
                try:
                    # Check if any input field is empty
                    if not all([self.translate_x_input.text(), self.translate_y_input.text(), self.translate_z_input.text(),
                                self.rotate_x_input.text(), self.rotate_y_input.text(), self.rotate_z_input.text(),
                                self.scale_x_input.text(), self.scale_y_input.text(), self.scale_z_input.text()]):
                        raise ValueError("All fields must be filled with numeric values.")
                    
                    translate_values = [float(self.translate_x_input.text()), float(self.translate_y_input.text()), float(self.translate_z_input.text())]
                    rotate_values = [float(self.rotate_x_input.text()), float(self.rotate_y_input.text()), float(self.rotate_z_input.text())]
                    scale_values = [float(self.scale_x_input.text()), float(self.scale_y_input.text()), float(self.scale_z_input.text())]
                    
                    model_number = self.current_model_number
                    actor = self.loaded_models[model_number - 1]
                    
                    # Apply translation
                    actor.SetPosition(translate_values)
                    
                    # Apply rotation
                    actor.SetOrientation(rotate_values)
                    
                    # Apply scaling
                    actor.SetScale(scale_values)
                    
                    self.vtkWidget.GetRenderWindow().Render()
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", str(e))
            
            # Define the function to hide the transformation panel
            def hide_transformation_panel():
                self.transformation_panel_widget.hide()
            
            # Connect the Apply button to the apply_transformation function
            apply_button.clicked.connect(apply_transformation)
            
            # Connect the Cancel button to the hide_transformation_panel function
            cancel_button.clicked.connect(hide_transformation_panel)
            
            # Add the Apply and Cancel buttons to the button layout
            button_layout.addWidget(apply_button)
            button_layout.addWidget(cancel_button)
            
            # Add the button layout to the transformation layout
            self.transformation_layout.addLayout(button_layout)
            
            # Mark the transformation panel as initialized
            self.transformation_panel_initialized = True
        
        # Show the transformation panel
        self.transformation_panel_widget.show()
        
    def show_lighting_dialog(self):
        # Create a new dialog window
        dialog = QDialog(self)
        dialog.setWindowTitle("Lighting")
        dialog.setMinimumSize(300, 200)
        
        # Create a vertical layout for the dialog
        layout = QVBoxLayout(dialog)
        
        # Create input fields for lighting adjustments
        intensity_label = QLabel("Intensity:")
        intensity_input = QLineEdit()
        position_label = QLabel("Position (x, y, z):")
        position_layout = QHBoxLayout()
        position_x_input = QLineEdit()
        position_y_input = QLineEdit()
        position_z_input = QLineEdit()
        position_layout.addWidget(position_x_input)
        position_layout.addWidget(position_y_input)
        position_layout.addWidget(position_z_input)
        
        # Add input fields to the layout
        layout.addWidget(intensity_label)
        layout.addWidget(intensity_input)
        layout.addWidget(position_label)
        layout.addLayout(position_layout)
        
        # Create Apply and Cancel buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        cancel_button = QPushButton("Cancel")
        
        # Define the function to apply the lighting adjustments
        def apply_lighting():
            try:
                intensity = float(intensity_input.text())
                position_values = [float(position_x_input.text()), float(position_y_input.text()), float(position_z_input.text())]
                
                # Remove existing lights
                self.ren.RemoveAllLights()
                
                # Create a light source
                light = vtk.vtkLight()
                light.SetIntensity(intensity)
                light.SetPosition(position_values)
                
                # Add the light to the renderer
                self.ren.AddLight(light)
                
                self.vtkWidget.GetRenderWindow().Render()
                dialog.accept()
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", str(e))
        
        # Connect the Apply button to the apply_lighting function
        apply_button.clicked.connect(apply_lighting)
        
        # Connect the Cancel button to close the dialog
        cancel_button.clicked.connect(dialog.reject)
        
        # Add the Apply and Cancel buttons to the button layout
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        
        # Add the button layout to the main layout
        layout.addLayout(button_layout)
        
        # Show the dialog
        dialog.exec_()
        
    def show_texture_panel(self):
        # Initialize the texture layout if it doesn't exist
        if not hasattr(self, 'texture_layout'):
            self.texture_layout = QVBoxLayout()
        
        # Clear the existing layout
        for i in reversed(range(self.texture_layout.count())):
            widget = self.texture_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Create a button to load texture
        load_texture_button = QPushButton("Load Texture")
        
        # Define the function to load the texture
        def load_texture():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getOpenFileName(self, "Open Texture File", "", "Image Files (*.png *.jpg *.bmp);;All Files (*)", options=options)
            if file_name:
                self.texture_file_name = file_name
                texture_label.setText(f"Loaded Texture: {file_name}")
        
        # Connect the load texture button to the load_texture function
        load_texture_button.clicked.connect(load_texture)
        
        # Create a label to display the loaded texture file name
        texture_label = QLabel("No texture loaded")
        
        # Add the load texture button and label to the texture layout
        self.texture_layout.addWidget(load_texture_button)
        self.texture_layout.addWidget(texture_label)
        
        # Create Apply, Remove, and Cancel buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        remove_button = QPushButton("Remove")
        cancel_button = QPushButton("Cancel")
        
        # Define the function to apply the texture
        def apply_texture():
            if self.texture_file_name:
                model_number = self.current_model_number
                actor = self.loaded_models[model_number - 1]
                
                # Load the texture
                reader = vtk.vtkJPEGReader()
                reader.SetFileName(self.texture_file_name)
                reader.Update()
                
                # Create texture object
                texture = vtk.vtkTexture()
                texture.SetInputConnection(reader.GetOutputPort())
                
                # Generate texture coordinates for the model
                texture_mapper = vtk.vtkTextureMapToSphere()
                texture_mapper.SetInputConnection(actor.GetMapper().GetInputConnection(0, 0))
                texture_mapper.PreventSeamOn()
                
                # Create a new mapper and set the input data
                new_mapper = vtk.vtkPolyDataMapper()
                new_mapper.SetInputConnection(texture_mapper.GetOutputPort())
                
                # Apply the texture to the actor
                actor.SetMapper(new_mapper)
                actor.SetTexture(texture)
                
                self.vtkWidget.GetRenderWindow().Render()

        # Define the function to remove the texture
        def remove_texture():
            model_number = self.current_model_number
            actor = self.loaded_models[model_number - 1]
            
            # Get the current color of the actor
            current_color = actor.GetProperty().GetColor()
            
            # Remove the texture from the actor
            actor.SetTexture(None)
            
            # Restore the original color of the actor
            actor.GetProperty().SetColor(current_color)
            
            self.vtkWidget.GetRenderWindow().Render()
        
        # Define the function to hide the texture panel
        def hide_texture_panel():
            self.texture_panel_widget.hide()
        
        # Connect the Apply button to the apply_texture function
        apply_button.clicked.connect(lambda: apply_texture())
        
        # Connect the Remove button to the remove_texture function
        remove_button.clicked.connect(lambda: remove_texture())
        
        # Connect the Cancel button to the hide_texture_panel function
        cancel_button.clicked.connect(lambda: hide_texture_panel())
        
        # Add the Apply, Remove, and Cancel buttons to the button layout
        button_layout.addWidget(apply_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(cancel_button)
        
        # Add the button layout to the texture layout
        self.texture_layout.addLayout(button_layout)
        
        # Initialize and show the texture panel widget if it doesn't exist
        if not hasattr(self, 'texture_panel_widget'):
            self.texture_panel_widget = QWidget()
            self.texture_panel_widget.setLayout(self.texture_layout)
            self.side_layout.addWidget(self.texture_panel_widget)
        
        self.texture_panel_widget.show()
        
    def save_model(self):
        # Open a directory selection dialog
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if directory:
            for i, actor in enumerate(self.loaded_models):
                # Open a dialog to get the file name from the user
                file_name, ok = QInputDialog.getText(self, "Save Model", f"Enter name for model {i+1}:")
                
                if ok and file_name:
                    # Create a temporary renderer and render window to export the model
                    temp_ren = vtk.vtkRenderer()
                    temp_ren_win = vtk.vtkRenderWindow()
                    temp_ren_win.AddRenderer(temp_ren)
                    temp_iren = vtk.vtkRenderWindowInteractor()
                    temp_iren.SetRenderWindow(temp_ren_win)
                    
                    # Add the actor to the temporary renderer
                    temp_ren.AddActor(actor)
                    
                    # Set up the OBJ exporter
                    obj_exporter = vtk.vtkOBJExporter()
                    obj_exporter.SetFilePrefix(os.path.join(directory, file_name))
                    obj_exporter.SetInput(temp_ren_win)
                    obj_exporter.Write()
                    
                    # Clean up the temporary renderer and render window
                    temp_ren_win.Finalize()
                    temp_iren.TerminateApp()
                    del temp_iren, temp_ren_win, temp_ren
                    
            QMessageBox.information(self, "Save Model", "Models saved successfully!")
            
    def save_window(self):
        # Open a directory selection dialog
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if directory:
            # Open a dialog to get the file name from the user
            file_name, ok = QInputDialog.getText(self, "Save All Models", "Enter name for the combined model:")
            
            if ok and file_name:
                # Create a temporary renderer and render window to export the models
                temp_ren = vtk.vtkRenderer()
                temp_ren_win = vtk.vtkRenderWindow()
                temp_ren_win.AddRenderer(temp_ren)
                temp_iren = vtk.vtkRenderWindowInteractor()
                temp_iren.SetRenderWindow(temp_ren_win)
                
                # Add all actors to the temporary renderer
                for actor in self.loaded_models:
                    temp_ren.AddActor(actor)
                
                # Set up the OBJ exporter
                obj_exporter = vtk.vtkOBJExporter()
                obj_exporter.SetFilePrefix(os.path.join(directory, file_name))
                obj_exporter.SetInput(temp_ren_win)
                obj_exporter.Write()
                
                # Clean up the temporary renderer and render window
                temp_ren_win.Finalize()
                temp_iren.TerminateApp()
                del temp_iren, temp_ren_win, temp_ren
                
                QMessageBox.information(self, "Save All Models", "All models saved successfully!")
                
    def reset(self):
        for actor in self.loaded_models:
            actor.SetPosition(0, 0, 0)
            actor.SetOrientation(0, 0, 0)
            actor.SetScale(1, 1, 1)
            actor.GetProperty().SetColor(1, 1, 1)  # Reset color to white
            actor.SetTexture(None)  # Remove any textures
        self.vtkWidget.GetRenderWindow().Render()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())