from flet import *
class CustomCheckBox(Container):
    def __init__(self, color, label='', selection_fill='#183588', size=25, stroke_width=2,
                 animation=None, checked=False, font_size=17, pressed=None):
        super().__init__()

        self.selection_fill = selection_fill
        self.color = color
        self.label = label
        self.size = size
        self.stroke_width = stroke_width
        self.animation = animation
        self.checked = checked
        self.font_size = font_size
        self.pressed = pressed

        self.BG = '#041955'
        self.FG = '#3450a1'
        self.PINK = '#eb06ff'
        self.CHECKED = '#183588'

        self._build_content()

    def _build_checked(self):
        return Container(
            animate=self.animation,
            width=self.size,
            height=self.size,
            border_radius=(self.size / 2) + 5,
            bgcolor=self.CHECKED,
            content=Icon(Icons.CHECK_ROUNDED, size=15)
        )

    def _build_unchecked(self):
        return Container(
            animate=self.animation,
            width=self.size,
            height=self.size,
            border_radius=(self.size / 2) + 5,
            bgcolor=None,
            border=Border.all(color=self.color, width=self.stroke_width),
            content=Container()
        )

    def _build_content(self):
        if self.checked:
            checkbox_widget = self._build_checked()
        else:
            checkbox_widget = self._build_unchecked()

        self.check_box = checkbox_widget

        self.content = Container(
            on_click=self.checked_check,  
            content=Row(
                controls=[
                    checkbox_widget,
                    Text(
                        self.label,
                        font_family='poppins',
                        size=self.font_size,
                        weight=FontWeight.W_300
                    )
                ]
            )
        )

    def checked_check(self, e):
        if not self.checked:
            self.checked = True
        else:
            self.checked = False

        if self.pressed:
            self.run()

        self._build_content()
        self.update()

    def is_checked(self):
        return self.checked

    def run(self, *args):
        self.pressed(args)