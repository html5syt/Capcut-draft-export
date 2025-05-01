import flet as ft
import json
import time
import os
import sys
import zipfile


def export_draft(e: ft.ControlEvent):
    page = e.control.page
    if not page.session.contains_key("export_dict"):
        return
    export_dict = page.session.get("export_dict")
    if len(export_dict) == 0:
        return
    file_picker = ft.FilePicker(on_result=lambda e: export_zip(e))

    def export_zip(e):
        file_path = json.loads(e.data)["path"]
        if file_path is None or file_path == "null":
            return
        dialog = ft.AlertDialog(
            content=ft.Column(
                [
                    ft.Text("正在导出，请稍候..."),
                    ft.ProgressBar(value=0),
                ],
                expand=False,
                height=35,
            )
        )
        page.open(dialog)
        print(file_path)
        i = 0
        for draft_id, draft_info in export_dict.items():
            i += 1
            with zipfile.ZipFile(
                os.path.join(file_path, draft_info["draft_name"] + ".zip"),
                "w",
                zipfile.ZIP_LZMA,
            ) as zipf:
                folder_path = draft_info["draft_fold_path"]

                # Walk through the directory tree and add files to the zip
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        # Get the full path of the file
                        file_path = os.path.join(root, file)
                        # Calculate the relative path for the zip file structure
                        relative_path = os.path.relpath(file_path, folder_path)
                        relative_path = os.path.join(
                            os.path.basename(folder_path), relative_path
                        )
                        # Add the file to the zip with the relative path
                        zipf.write(file_path, relative_path)
            dialog.content.controls[1].value += i / len(export_dict)
        page.close(dialog)

    page.overlay.append(file_picker)
    page.update()
    file_picker.get_directory_path(dialog_title="选择导出到的文件夹")


# choose_export
def choose_export(e, self: ft.ListTile):
    print(e)
    print(self.summary)
    if e.data == "true":
        print("export")
        if not self.page.session.contains_key("export_dict"):
            self.page.session.set(
                "export_dict",
                {self.summary["draft_id"]: self.summary},
            )
        else:
            TEMP = self.page.session.get("export_dict")
            TEMP[self.summary["draft_id"]] = self.summary
            self.page.session.set(
                "export_dict",
                TEMP,
            )
    elif e.data == "false" and self.page.session.contains_key("export_dict"):
        print("not export")
        TEMP = self.page.session.get("export_dict")
        TEMP.pop(self.summary["draft_id"])
        self.page.session.set(
            "export_dict",
            TEMP,
        )
    if len(self.page.session.get("export_dict")) != 0:
        self.page.controls[0].title = ft.Text(
            "已选择" + str(len(self.page.session.get("export_dict"))) + "个草稿"
        )
        self.page.controls[0].leading = None
        self.page.floating_action_button.icon = ft.Icons.LOGOUT
        self.page.floating_action_button.tooltip = "导出草稿"
        self.page.floating_action_button.on_click = lambda e: export_draft(e)
    else:
        self.page.controls[0].title = ft.Text("剪映草稿管理工具")
        self.page.controls[0].leading = ft.Container(
            ft.Image(src="icon.png"), padding=10
        )
        self.page.floating_action_button.icon = ft.Icons.LOGIN
        self.page.floating_action_button.tooltip = "导入草稿"
        self.page.floating_action_button.on_click = lambda e: import_draft(e)
    self.page.update()
    print(len(self.page.session.get("export_dict")))
    print(self.page.session.get("export_dict"))
# import_draft
def import_draft(e: ft.ControlEvent):
    try:
        draft_root_path=e.control.page.controls[1].controls[0].content.summary["draft_root_path"]
    except:
        if sys.platform == "win32":
            path = os.path.expandvars(
                r"%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft\root_meta_info.json"
            )
        elif sys.platform == "darwin":
            path = os.path.expanduser(
                r"~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/root_meta_info.json"
            )
        with open(
            path,
            "r",
        ) as f:
            draft_root_path=json.load(f)["root_path"]

    page = e.control.page
    file_picker2 = ft.FilePicker(on_result=lambda e: import_zip(e))

    def import_zip(e):
        files = json.loads(e.data)["files"]
        if files is None or len(files) == 0:
            return
        dialog = ft.AlertDialog(
            content=ft.Column(
                [
                    ft.Text("正在导入，请稍候..."),
                    ft.ProgressBar(value=0),
                ],
                expand=False,
                height=35,
            )
        )
        page.open(dialog)
        print(files)
        i = 0
        for file in files:
            i += 1
            with zipfile.ZipFile(
                file["path"],
                "r",
            ) as zipf:
                # print(zipf.namelist())
                zipf.extractall(draft_root_path)
            dialog.content.controls[1].value += i / len(files)
        page.close(dialog)

    page.overlay.append(file_picker2)
    page.update()
    file_picker2.pick_files(dialog_title="选择导入的文件",allowed_extensions=["zip"],allow_multiple=True)

class ExportItem(ft.ListTile):
    def __init__(
        self,
        summary: dict,
    ):
        self.summary = summary
        super().__init__(
            leading=ft.Checkbox(on_change=lambda e: choose_export(e, self)),
            title=ft.Text(summary["draft_name"]),
            subtitle=ft.Text(
                "创建于："
                + time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(summary["tm_draft_create"] // (10**6)),  # 取前10位
                )
                + "\n最近修改于："
                + time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(summary["tm_draft_modified"] // (10**6)),  # 取前10位
                )
            ),
            expand=False,
            expand_loose=False,
        )


def read_root_meta_info(mainview: ft.GridView, not_first_read=False):
    mainview.controls.clear()
    if sys.platform == "win32":
        path = os.path.expandvars(
            r"%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft\root_meta_info.json"
        )
    elif sys.platform == "darwin":
        path = os.path.expanduser(
            r"~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/root_meta_info.json"
        )
    with open(
        path,
        "r",
    ) as f:
        for draft in json.load(f)["all_draft_store"] * 20:
            mainview.controls.append(
                ft.Container(
                    ExportItem(
                        summary=draft,
                    ),
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                )
            )
    mainview.update()


def main(page: ft.Page):
    page.title = "剪映草稿管理工具"
    # page.window.maximized = True
    page.adaptive = True

    # appbar
    appbar = ft.AppBar(
        title=ft.Text("剪映草稿管理工具"),
        leading=ft.Container(ft.Image(src="icon.png"), padding=10),
        bgcolor=ft.Colors.BLUE,
        actions=[
            # ft.IconButton(ft.Icons.LOGOUT),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="帮助"),
                    ft.PopupMenuItem(),  # divider
                    ft.PopupMenuItem(text="关于"),
                ],
                tooltip="菜单",
            ),
        ],
    )
    page.add(appbar)

    # import_btn
    action_btn = ft.FloatingActionButton(
        icon=ft.Icons.LOGIN, on_click=lambda e: import_draft(e), tooltip="导入草稿"
    )

    page.floating_action_button = action_btn

    # listview
    mainview = ft.GridView(controls=[], runs_count=6, expand=True)

    page.add(mainview)

    # first_read
    read_root_meta_info(mainview)

    page.update()


ft.app(main)
