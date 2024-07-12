from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QGraphicsView, QLineEdit,
                             QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem)
from PyQt6.QtGui import QPen, QColor, QPolygonF, QCursor, QKeySequence, QShortcut, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF, QSizeF, QLineF, pyqtSlot

import sys
import os

from ui_file.ui_gisWindow import Ui_GisWindow

class Figure:
    def __init__(self, color_pen, color_brush = (255, 255, 255, 0)):
        self.pen = QPen(QColor(*color_pen), 1)
        self.brush = QBrush(QColor(*color_brush), Qt.BrushStyle.SolidPattern)

class Point(Figure):
    def __init__(self, color):
        Figure.__init__(self, color)

class Line(Figure):
    def __init__(self, color):
        Figure.__init__(self, color)

class Polygon(Figure):
    def __init__(self, color_pen, color_brush):
        Figure.__init__(self, color_pen, color_brush)

class SelectedFigure(Figure):
    def __init__(self, color_pen, color_brush):
        Figure.__init__(self, color_pen, color_brush)

class MapGraphicsView(QGraphicsView):
    def __init__(self):
        super(MapGraphicsView, self).__init__()

        self.move_element = None
        self.list_delete_figure = []

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        factory = 1.25
        if event.angleDelta().y() > 0: 
            self.scale(factory, factory)
        else:
            self.scale(1 / factory, 1 / factory)

    def mouseMoveEvent(self, event):
        self.move_element = self.itemAt(event.pos())
        if self.move_element:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            super(MapGraphicsView, self).mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.move_element: 
            figure = self.itemAt(event.pos())
            selected_color = SelectedFigure((255, 168, 18), (255, 168, 18, 50))
            figure.setPen(selected_color.pen)

            if type(figure) == QGraphicsPolygonItem:
                figure.setBrush(selected_color.brush)

            if not figure in self.list_delete_figure:
                self.list_delete_figure.append(figure)
        else:
            super(MapGraphicsView, self).mousePressEvent(event)
    
    def clear_attributes(self):
        self.scene.clear()
        self.list_delete_figure.clear()

class GisWindow(QMainWindow, Ui_GisWindow):
    def __init__(self):
        super(GisWindow, self).__init__()
        self.setupUi(self)

        self.file_dialog = ""
        self.list_point = []
        self.list_line = []
        self.list_polygon = []
        self.list_save_figure = []

        self.MapGraphicsView = MapGraphicsView()
        self.verticalLayout.insertWidget(1, self.MapGraphicsView)

        self.PathLineEdit.setPlaceholderText(os.path.abspath("test_data.txt"))
        self.PathLineEdit.editingFinished.connect(self.input_path_to_file)
        self.PathPushButton.clicked.connect(self.call_file_dialog)

        save_shortcut = QShortcut (QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_coordinates_in_file)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_figure)

    def input_path_to_file(self):
        self.file_dialog = self.PathLineEdit.text()
        self.PathLineEdit.setText(self.file_dialog)
        self.fill_list_exception_handler()

    def call_file_dialog(self):
        self.file_dialog, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", "Текстовый файл (*.txt)")
        if self.file_dialog:
            self.PathLineEdit.setText(self.file_dialog)
            self.fill_list_exception_handler()

    def fill_list_exception_handler(self):
        try:
            self.clear_attributes()
            self.clear_space_lines()
            self.fill_message("Документ прочитан без ошибок.")
            self.fill_list_coordinates()

            if not self.list_point and not self.list_line and not self.list_polygon:
                self.fill_message("Ошибка.")

            self.painting_map()  
        except (FileNotFoundError):
            self.clear_attributes()
            self.fill_message("Ошибка.")
        
    def clear_attributes(self):
        self.list_point.clear()
        self.list_line.clear()
        self.list_polygon.clear()
        self.list_save_figure.clear()
        self.MapGraphicsView.clear_attributes()
    
    def clear_space_lines(self):
        with open(self.file_dialog) as f:
            lines = f.readlines()
            no_empty_lines = (line for line in lines if not line.isspace())
            with open(self.file_dialog, 'w') as n_f:
                n_f.writelines(no_empty_lines)

    def fill_list_coordinates(self):
        figure_file = open(self.file_dialog, "r", encoding="utf-8", errors='ignore')

        for line in figure_file.read().splitlines():
            if len(line.split(" ")) == 2:
                if self.file_exception_handler(line): self.list_point.append(self.file_exception_handler(line)[0])    

            elif len(line.split(" ")) == 4:
                point = self.file_exception_handler(line)
                if point: self.list_line.append(QLineF(point[0], point[1]))

            elif len(line.split(" ")) >= 6 and len(line.split(" ")) % 2 == 0:
                if self.file_exception_handler(line): self.list_polygon.append(QPolygonF(self.file_exception_handler(line)))

            else:
                self.fill_message("Документ прочитан не полностью.")

        figure_file.close()

    def get_coordinate_file(self, seq):
        point = []
        for i in range(0, len(seq), 2):
            point.append(QPointF(seq[i], seq[i+1]))
        return point
    
    def file_exception_handler(self, str_line):
        try:
            return self.get_coordinate_file(list(int(coord) for coord in str_line.split(" ")))
        except (ValueError):
            self.fill_message("Документ прочитан не полностью.")
    
    def fill_message(self, message):
        self.MessageLabel.setText(message)

    def painting_map(self):
        for point in self.list_point:
            rect = QRectF(point, QSizeF(1, 1))
            self.MapGraphicsView.scene.addEllipse(rect, Point((66, 133, 180)).pen)
        for line in self.list_line:
            self.MapGraphicsView.scene.addLine(line,  Line((170, 102, 81)).pen)
        for polygon in self.list_polygon:
            polygon_color = Polygon((85, 104, 50), (85, 104, 50, 50))
            self.MapGraphicsView.scene.addPolygon(polygon, polygon_color.pen, polygon_color.brush)

    def get_coordinate_scene(self):
        for figure in self.MapGraphicsView.scene.items():
            if type(figure) == QGraphicsEllipseItem:
                point = figure.rect().topLeft().toPoint()
                self.list_save_figure.append([str(point.x()), str(point.y())])

            elif type(figure) == QGraphicsLineItem:
                line = figure.line().toLine()
                list_point_line = [line.p1(), line.p2()]
                self.list_save_figure.append(self.collect_list_figure(list_point_line))

            elif type(figure) == QGraphicsPolygonItem:
                list_polygon_point = list(map(lambda point: point.toPoint(), figure.polygon()[:]))
                self.list_save_figure.append(self.collect_list_figure(list_polygon_point))

    def collect_list_figure(self, list_figure):
        list_result = []
        for i in list_figure:
            list_result.append(str(i.x()))
            list_result.append(str(i.y()))
        return list_result
    
    @pyqtSlot()
    def save_coordinates_in_file(self):
        file_dialog, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Текстовый файл (*.txt)")
        if file_dialog:
            self.get_coordinate_scene()

            save_file = open(file_dialog, "w", encoding="utf-8")
            list_str_coord = [" ".join(str_coord) for str_coord in self.list_save_figure]
            save_file.write("\n".join(list_str_coord))
            save_file.close()

            self.list_save_figure.clear()

    @pyqtSlot()
    def delete_figure(self):
        for figure in self.MapGraphicsView.list_delete_figure:
            self.MapGraphicsView.scene.removeItem(figure)
        self.MapGraphicsView.list_delete_figure.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GisWindow()
    window.show()
    app.exec()