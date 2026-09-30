import flet as ft
from flet import *  # noqa: F401,F403
import asyncio
from random import choice

from custom_checkbox import CustomCheckBox


def main(page: Page):
    BG = "#FFDEF1"
    FWG = "#97b4ff"
    FG = "#97b4ff"
    PINK = "#FFDEF1"

    page.window.width=420
    page.window.height=870
    circle = Stack(
        controls=[
            Container(width=100, height=100, border_radius=50, bgcolor="white12"),
            Container(
                gradient=SweepGradient(
                    center=Alignment.CENTER,
                    start_angle=0.0,
                    end_angle=3,
                    stops=[0.5, 0.5],
                    colors=["#00000000", PINK],
                ),
                width=100,
                height=100,
                border_radius=50,
                content=Row(
                    alignment="center",
                    controls=[
                        Container(
                            padding=Padding.all(5),
                            bgcolor=BG,
                            width=90,
                            height=90,
                            border_radius=50,
                            content=Container(
                                bgcolor=FG,
                                height=80,
                                width=80,
                                border_radius=40,
                                content=CircleAvatar(
                                    opacity=0.8,
                                    foreground_image_src="images/ghand.jpg",
                                ),
                            ),
                        )
                    ],
                ),
            ),
        ]
    )

    def shrink(e):
        page_2.controls[0].width = 120
        page_2.controls[0].scale = Scale(
            0.8, alignment=Alignment.CENTER_RIGHT
        )
        page_2.controls[0].border_radius = BorderRadius.only(
            top_left=35, top_right=0, bottom_left=35, bottom_right=0
        )
        page_2.update()

    def restore(e):
        page_2.controls[0].width = 400
        page_2.controls[0].border_radius = 35
        page_2.controls[0].scale = Scale(1, alignment=Alignment.CENTER_RIGHT)
        page_2.update()

    tasks_to_create = ['dars']
    async def print_input(e):
        input = user_task_input.value
        if not input:
            if len(create_task_view.controls) == 6:
                create_task_view.controls.append(Text(value="Please enter a task name", color='red', weight='bold'))
                page.update()
                await asyncio.sleep(5)
                create_task_view.controls.pop()
                page.update()
            else:
                pass
        else:
            tasks_to_create.append(input)
            print(tasks_to_create)
            page.update()

    user_task_input = TextField(
                            label=Text(value="Task name",color='BLACK'),
                            label_style=TextStyle(color="BLACK"),
                            border_color="transparent",
                            )

    close_btn = Button(content="Close",
                            icon=Icons.EXIT_TO_APP_OUTLINED,
                            color="white",
                            icon_color="white",
                            height=40,width=90,
                            on_click=lambda _: asyncio.create_task(page.push_route("/")))
    back_btn = Button(content="",
        icon=Icons.ARROW_BACK_IOS_ROUNDED,
        color="white",
        icon_color="white",
        height=60,width=60,
    )
    close_container = Container(padding=Padding.only(left=10),
            on_click=lambda _: asyncio.create_task(page.push_route("/")), height=40, width=40, content=Text("X")
        )
    create_task_view = Column(
        controls=[close_btn
            ,
            Container(padding=10,content=(user_task_input),bgcolor="#FF7ED4",height=70,width=400,border_radius=15),
            Container(height=5),
            ExpansionTile(
            title=Text("Category"),
            bgcolor=BG,
            subtitle=Text("Choose the category below"),
            affinity=TileAffinity.PLATFORM,
            maintain_state=True,
            collapsed_text_color=Colors.WHITE,
            text_color=Colors.BLACK,
            controls=[Divider(color='BLACK',height=1,opacity=0.5),
                      ListTile(title=Container(
                    content=Text(value="University", color="BLACK"),
                    margin=10,
                    padding=10,
                    alignment=Alignment.CENTER,
                    width=300,
                    height=50,
                    border_radius=10,
                    ink=True,
                    on_click=lambda _: print("Clickable transparent with Ink clicked!"),
                    )
                ),Divider(color='BLACK',height=1,opacity=0.5),
                      ListTile(title=Container(
                    content=Text(value="Finnish", color="BLACK"),
                    margin=10,
                    padding=10,
                    alignment=Alignment.CENTER,
                    width=300,
                    height=50,
                    border_radius=10,
                    ink=True,
                    on_click=lambda _: print("Clickable transparent with Ink clicked!"),
                    )),Divider(color='BLACK',height=1,opacity=0.5),
                      ListTile(title=Container(
                    content=Text(value="Painting", color="BLACK"),
                    margin=10,
                    padding=10,
                    alignment=Alignment.CENTER,
                    width=300,
                    height=50,
                    border_radius=10,
                    ink=True,
                    on_click=lambda _: print("Clickable transparent with Ink clicked!"),
                    )),],
            ),
            Container(height=5),
            FloatingActionButton(
                                 foreground_color="white",
                                 content="Submit",
                                 bgcolor=BG,height=50,
                                 width=155,
                                 on_click=print_input),
        ],alignment='center'
    ,horizontal_alignment=CrossAxisAlignment.CENTER)
    color_group=["#F26B0F","#FCC737","#E73879","#7E1891"]

    tasks = Column(
        height=400,
        scroll="auto",
    )
    # for i,item in enumerate(tasks_to_create):
    for i,item in enumerate(tasks_to_create):
        tasks.controls.append(
            Container(
                height=70,
                width=400,
                bgcolor=BG,
                border_radius=25,
                padding=Padding.only(
                    left=20,
                ),
                content=CustomCheckBox(color=choice(color_group), label=item),
            ),
        )
    categories_card = Row(scroll="auto")
    categories = ["University", "Finnish", "Painting"]
    for i, category in enumerate(categories):
        categories_card.controls.append(
            Container(
                border_radius=20,
                bgcolor=BG,
                width=170,
                height=110,
                padding=15,
                content=Column(
                    controls=[
                        Text("40 Tasks"),
                        Text(category),
                        Container(
                            width=160,
                            height=5,
                            bgcolor="black12",
                            border_radius=20,
                            padding=Padding.only(right=i * 30),
                            content=Container(
                                bgcolor=PINK,
                            ),
                        ),
                    ]
                ),
            )
        )

    first_page_contents = Container(
        content=Column(
            controls=[
                Row(
                    alignment="spaceBetween",
                    controls=[
                        Container(
                            on_click=lambda e: shrink(e), content=Icon(Icons.MENU)
                        ),
                        Row(
                            controls=[
                                Icon(Icons.SEARCH),
                                Icon(Icons.NOTIFICATIONS_OUTLINED),
                            ],
                        ),
                    ],
                ),
                Container(height=20),
                Text(value="What's up, Ghand!\U0001F36D",size=30,weight=FontWeight.W_700),
                Text(value="CATEGORIES"),
                Container(
                    padding=Padding.only(
                        top=10,
                        bottom=20,
                    ),
                    content=categories_card,
                ),
                Container(height=20),
                Text("TODAY'S TASKS"),
                Stack(
                    controls=[
                        tasks,
                        FloatingActionButton(
                            bottom=2,
                            right=20,
                            icon=Icons.ADD,
                            on_click=lambda _: asyncio.create_task(page.push_route("/create_task")),
                        ),
                    ]
                ),
            ],
        ),
    )

    page_1 = Container(
        width=400,
        height=850,
        bgcolor=BG,
        border_radius=35,
        padding=Padding.only(left=50, top=60, right=200),
        content=Column(
            controls=[
                Row(
                    alignment="end",
                    controls=[
                        Container(
                            border_radius=25,
                            padding=Padding.only(
                                top=13,
                                left=13,
                            ),
                            height=50,
                            width=40,
                            border=Border.all(color="white", width=2),
                            on_click=lambda e: restore(e),
                            content=Text("<"),
                        )
                    ],
                ),
                Container(height=20),  # height=20
                circle,
                Text("Mahshid Mokhtari", size=27, weight="bold"),
                Container(height=25),
                Row(
                    controls=[
                        Icon(Icons.FAVORITE_BORDER_SHARP, color="white60"),
                        Text(
                            "Templates",
                            size=15,
                            weight=FontWeight.W_300,
                            color="black",
                            font_family="poppins",
                        ),
                    ]
                ),
                Container(height=5),
                Row(
                    controls=[
                        Icon(Icons.CARD_TRAVEL, color="white60"),
                        Text(
                            "Templates",
                            size=15,
                            weight=FontWeight.W_300,
                            color="black",
                            font_family="poppins",
                        ),
                    ]
                ),
                Container(height=5),
                Row(
                    controls=[
                        Icon(Icons.CALCULATE_OUTLINED, color="white60"),
                        Text(
                            "Templates",
                            size=15,
                            weight=FontWeight.W_300,
                            color="black",
                            font_family="poppins",
                        ),
                    ]
                ),
                Image(
                    src="images/ghand.jpg",
                    width=300,
                    height=200,
                ),
                Text(
                    "Good",
                    color=FG,
                    font_family="poppins",
                ),
                Text(
                    "Consistency",
                    size=22,
                ),
            ]
        ),
    )

    page_2 = Row(
        alignment="end",
        controls=[
            Container(
                width=400,
                height=850,
                bgcolor=FG,
                border_radius=35,
                animate=Animation(600, AnimationCurve.DECELERATE),
                animate_scale=Animation(400, curve="decelerate"),
                padding=Padding.only(top=50, left=20, right=20, bottom=5),
                content=Column(controls=[first_page_contents]),
            )
        ],
    )

    container = Container(
        width=400,
        height=850,
        bgcolor=BG,
        border_radius=35,
        content=Stack(
            controls=[
                page_1,
                page_2,
            ]
        ),
    )

    pages = {
        "/": View(
            route="/",
            controls=[
                container,
            ],
        ),
        "/create_task": View(
            route="/create_task",
            controls=[create_task_view],
        ),
    }

    def route_change(e=None):
        page.views.clear()
        page.views.append(pages.get(page.route, pages["/"]))
        page.update()

    page.on_route_change = route_change
    route_change()


ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)