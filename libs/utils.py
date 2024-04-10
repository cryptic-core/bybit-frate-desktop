from PyQt5.QtCore import Qt,QEvent,QObject

# class for api_secret lose focus
class FocusFilter(QObject):
  def __init__(self, widget,callback):
    super().__init__(widget)
    self.widget = widget
    self.callback = callback

  def eventFilter(self, obj, event):
    if obj == self.widget and event.type() == QEvent.FocusOut:
      # "Line Edit lost focus!"
      print("loseFocus")
      if(self.callback):
          self.callback()
      return True  
    else:
      return super().eventFilter(obj, event)
